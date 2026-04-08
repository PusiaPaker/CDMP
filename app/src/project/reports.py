from io import BytesIO
import datetime
from pathlib import Path

from sqlalchemy import select
from dateutil.relativedelta import relativedelta

from app.core import db
from app.tables import TimelineEvent, Expense, ProjectPerson
from app.src.project.visualizations import build_event_distribution, build_role_distribution
from app.src.project.finance import *

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.textlabels import Label
from reportlab.graphics.shapes import Drawing, String
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

PANDATA_LOGO_PATH = Path(__file__).resolve().parents[2] / "static" / "assets" / "logo" / "pandata-logo.png"
PANDATA_BG = colors.HexColor("#f8f9fb")
PANDATA_SURFACE = colors.HexColor("#ffffff")
PANDATA_BORDER = colors.HexColor("#e5e7eb")
PANDATA_TEXT_PRIMARY = colors.HexColor("#111827")
PANDATA_TEXT_SECONDARY = colors.HexColor("#6b7280")
PANDATA_ACCENT = colors.HexColor("#1f2933")
REPORT_BAR_COLORS = [
    colors.HexColor("#6366f1"),
    colors.HexColor("#3b82f6"),
    colors.HexColor("#10b981"),
    colors.HexColor("#f59e0b"),
    colors.HexColor("#ec4899"),
    colors.HexColor("#8b5cf6"),
    colors.HexColor("#0ea5e9"),
    colors.HexColor("#22c55e"),
    colors.HexColor("#f97316"),
    colors.HexColor("#a855f7"),
]

##############################
# Database utility functions #
#############################
def _get_next_events(project_id):
    '''
    gets up to 5 events that happen after curent date
    '''
    today = datetime.date.today()
    events = db.session.scalars(
        select(TimelineEvent)
        .where(TimelineEvent.project_id == project_id)
        .order_by(TimelineEvent.start_date.asc())
    ).all()
    return [event for event in events if event.start_date.date() >= today][:5]


def _get_timeline_bounds(project_id):
    events = db.session.scalars(
        select(TimelineEvent)
        .where(TimelineEvent.project_id == project_id)
        .order_by(TimelineEvent.start_date.asc())
    ).all()

    if not events:
        return None, None

    earliest_start = min(event.start_date for event in events)
    latest_timeline_date = max(
        event.end_date or event.start_date
        for event in events
    )
    return earliest_start, latest_timeline_date


def _get_active_project_phase(project_id):
    today = datetime.date.today()
    events = db.session.scalars(
        select(TimelineEvent)
        .where(TimelineEvent.project_id == project_id)
        .order_by(TimelineEvent.start_date.asc(), TimelineEvent.end_date.asc())
    ).all()

    for event in events:
        event_end_date = (event.end_date or event.start_date).date()
        if event.start_date.date() <= today <= event_end_date:
            return {
                "name": event.title,
                "description": event.description,
            }

    return None

#####################################
# Reportlab/papyrus style utilities #
#####################################
# These are a mess, the reportlab library uses inches as units and weird placements
# techniques to be able to center/position things. 

def _get_report_styles():
    base_styles = getSampleStyleSheet()

    return {
        #
        # General Styles
        # 
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base_styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=25,
            leading=30,
            textColor=PANDATA_TEXT_PRIMARY,
            spaceAfter=0,
        ),
        "meta": ParagraphStyle(
            "ReportMeta",
            parent=base_styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=PANDATA_TEXT_SECONDARY,
            spaceAfter=0,
        ),
        "body": ParagraphStyle(
            "ReportBody",
            parent=base_styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            textColor=PANDATA_TEXT_PRIMARY,
            spaceAfter=0,
        ),
        "heading": ParagraphStyle(
            "ReportHeading",
            parent=base_styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13.5,
            leading=18,
            textColor=PANDATA_ACCENT,
            spaceAfter=0,
        ),
        #
        # Progress and Milestones
        #
        "TEST": ParagraphStyle(
            "ReportHeading",
            parent=base_styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13.5,
            leading=18,
            textColor=PANDATA_ACCENT,
            spaceAfter=0,
        ),
    }


def _build_next_events_table(project, styles):
    rows = [["Event Title", "Type", "Date"]]

    for event in _get_next_events(project.id):
        rows.append([
            Paragraph(event.title or "", styles["body"]),
            "Phase start" if event.end_date else "Event",
            event.start_date.strftime("%Y-%m-%d"),
        ])

    if len(rows) == 1:
        rows.append([Paragraph("No upcoming events", styles["body"]), "", ""])

    table = Table(rows, colWidths=[3.95 * inch, 1.25 * inch, 1.5 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PANDATA_ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), PANDATA_SURFACE),
        ("TEXTCOLOR", (0, 1), (-1, -1), PANDATA_TEXT_PRIMARY),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PANDATA_SURFACE, PANDATA_BG]),
        ("BOX", (0, 0), (-1, -1), 1, PANDATA_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.75, PANDATA_BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def _build_event_distribution_chart(project, styles):
    chart_data = build_event_distribution(project.id)
    if not chart_data["data"]:
        return Paragraph("No timeline activity yet.", styles["body"])

    drawing = Drawing(460, 260)
    drawing.hAlign = "CENTER"

    past_data = chart_data.get("past_data", chart_data["data"])
    future_data = chart_data.get("future_data", [0] * len(chart_data["data"]))
    max_value = max(past_data + future_data)
    chart = VerticalBarChart()
    chart.x = 78
    chart.y = 56
    chart.width = 304
    chart.height = 150
    chart.data = [past_data, future_data]
    chart.categoryAxis.categoryNames = chart_data["labels"]
    chart.categoryAxis.labels.angle = 25
    chart.categoryAxis.labels.boxAnchor = "ne"
    chart.categoryAxis.labels.fontName = "Helvetica"
    chart.categoryAxis.labels.fontSize = 8
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = max_value + 2
    chart.valueAxis.forceZero = 1
    chart.bars[0].fillColor = colors.HexColor("#16a34a")
    chart.bars[0].strokeColor = colors.HexColor("#16a34a")
    chart.bars[1].fillColor = colors.HexColor("#dc2626")
    chart.bars[1].strokeColor = colors.HexColor("#dc2626")
    drawing.add(chart)

    drawing.add(String(
        drawing.width / 2,
        drawing.height - 16,
        "Event Distribution",
        textAnchor="middle",
        fontName="Helvetica-Bold",
        fontSize=12,
        fillColor=PANDATA_TEXT_PRIMARY,
    ))

    drawing.add(String(
        drawing.width / 2,
        18,
        "time",
        textAnchor="middle",
        fontName="Helvetica-Bold",
        fontSize=10,
        fillColor=PANDATA_TEXT_SECONDARY,
    ))

    y_axis_label = Label()
    y_axis_label.setOrigin(20, chart.y + (chart.height / 2))
    y_axis_label.angle = 90
    y_axis_label.boxAnchor = "c"
    y_axis_label.setText("# of events")
    y_axis_label.fontName = "Helvetica-Bold"
    y_axis_label.fontSize = 10
    y_axis_label.fillColor = PANDATA_TEXT_SECONDARY
    drawing.add(y_axis_label)

    return drawing


def _build_role_distribution_chart(project_id, styles):
    chart_data = build_role_distribution(project_id)
    if not chart_data["data"]:
        return Paragraph("No stakeholder role distribution data is available yet.", styles["body"])

    drawing = Drawing(460, 250)
    drawing.hAlign = "CENTER"

    max_value = max(chart_data["data"])
    chart = VerticalBarChart()
    chart.x = 78
    chart.y = 56
    chart.width = 304
    chart.height = 142
    chart.data = [chart_data["data"]]
    chart.categoryAxis.categoryNames = chart_data["labels"]
    chart.categoryAxis.labels.angle = 25
    chart.categoryAxis.labels.boxAnchor = "ne"
    chart.categoryAxis.labels.fontName = "Helvetica"
    chart.categoryAxis.labels.fontSize = 8
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = max_value + 2
    chart.valueAxis.forceZero = 1
    for index, _ in enumerate(chart_data["data"]):
        bar_color = REPORT_BAR_COLORS[index % len(REPORT_BAR_COLORS)]
        chart.bars[(0, index)].fillColor = bar_color
        chart.bars[(0, index)].strokeColor = bar_color
    drawing.add(chart)

    drawing.add(String(
        drawing.width / 2,
        drawing.height - 16,
        "Role Distribution",
        textAnchor="middle",
        fontName="Helvetica-Bold",
        fontSize=12,
        fillColor=PANDATA_TEXT_PRIMARY,
    ))

    y_axis_label = Label()
    y_axis_label.setOrigin(20, chart.y + (chart.height / 2))
    y_axis_label.angle = 90
    y_axis_label.boxAnchor = "c"
    y_axis_label.setText("# of people")
    y_axis_label.fontName = "Helvetica-Bold"
    y_axis_label.fontSize = 10
    y_axis_label.fillColor = PANDATA_TEXT_SECONDARY
    drawing.add(y_axis_label)

    return drawing


def _build_financial_category_chart(category_split, styles):
    if not category_split["data"]:
        return Paragraph("No financial category data is available yet.", styles["body"])

    drawing = Drawing(460, 250)
    drawing.hAlign = "CENTER"

    max_value = max(category_split["data"])
    chart = VerticalBarChart()
    chart.x = 78
    chart.y = 56
    chart.width = 304
    chart.height = 142
    chart.data = [category_split["data"]]
    chart.categoryAxis.categoryNames = category_split["labels"]
    chart.categoryAxis.labels.angle = 25
    chart.categoryAxis.labels.boxAnchor = "ne"
    chart.categoryAxis.labels.fontName = "Helvetica"
    chart.categoryAxis.labels.fontSize = 8
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = max_value + (max_value * 0.15 if max_value else 2)
    chart.valueAxis.forceZero = 1
    for index, _ in enumerate(category_split["data"]):
        bar_color = REPORT_BAR_COLORS[index % len(REPORT_BAR_COLORS)]
        chart.bars[(0, index)].fillColor = bar_color
        chart.bars[(0, index)].strokeColor = bar_color
    drawing.add(chart)

    drawing.add(String(
        drawing.width / 2,
        drawing.height - 16,
        "Spend by Category",
        textAnchor="middle",
        fontName="Helvetica-Bold",
        fontSize=12,
        fillColor=PANDATA_TEXT_PRIMARY,
    ))

    y_axis_label = Label()
    y_axis_label.setOrigin(20, chart.y + (chart.height / 2))
    y_axis_label.angle = 90
    y_axis_label.boxAnchor = "c"
    y_axis_label.setText("spend ($)")
    y_axis_label.fontName = "Helvetica-Bold"
    y_axis_label.fontSize = 10
    y_axis_label.fillColor = PANDATA_TEXT_SECONDARY
    drawing.add(y_axis_label)

    return drawing


def _draw_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(PANDATA_TEXT_SECONDARY)
    text = "Generated by Pandata"
    logo_size = 0.18 * inch
    gap = 0.06 * inch
    text_width = canvas.stringWidth(text, "Helvetica", 9)
    has_logo = PANDATA_LOGO_PATH.exists()
    total_width = text_width + (gap + logo_size if has_logo else 0)
    start_x = (doc.pagesize[0] - total_width) / 2
    footer_y = 0.5 * inch

    if has_logo:
        canvas.drawImage(
            str(PANDATA_LOGO_PATH),
            start_x,
            footer_y - (logo_size / 2),
            width=logo_size,
            height=logo_size,
            preserveAspectRatio=True,
            mask="auto",
        )

    canvas.drawString(start_x + (logo_size + gap if has_logo else 0), footer_y - 3, text)
    canvas.restoreState()


def _decorate_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(PANDATA_BG)
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], stroke=0, fill=1)

    card_x = doc.leftMargin - (0.18 * inch)
    card_y = doc.bottomMargin - (0.1 * inch)
    card_width = doc.width + (0.36 * inch)
    card_height = doc.height + (0.2 * inch)

    canvas.setFillColor(PANDATA_SURFACE)
    canvas.setStrokeColor(PANDATA_BORDER)
    canvas.roundRect(card_x, card_y, card_width, card_height, 14, stroke=1, fill=1)

    canvas.setFillColor(PANDATA_ACCENT)
    canvas.rect(card_x, card_y + card_height - (0.08 * inch), card_width, 0.08 * inch, stroke=0, fill=1)
    canvas.restoreState()

    _draw_footer(canvas, doc)

####################################
# Report generaton logic functions #
####################################
def generate_report_pdf(project, generated_by):
    '''
    project: Project row from db
    generated_by: username (or eventually name) of person who
        generated the report on pandata
    '''
    #
    # Prepare text fields and other data for being inserted into the reportlab PDF
    #
    
    generated_at = datetime.datetime.now().astimezone()
    timeline_start, timeline_end = _get_timeline_bounds(project.id)
    active_project_phase = _get_active_project_phase(project.id)

    if timeline_start:
        active_delta = relativedelta(generated_at.date(), timeline_start.date())
        active_months = (active_delta.years * 12) + active_delta.months
        active_months_text = f"{active_months} month" if active_months == 1 else f"{active_months} months"
        timeline_end_text = timeline_end.strftime("%A, %B %d, %Y")
    else:
        active_months_text = "0 months"
        timeline_end_text = "an unknown date"

    active_project_phase_name = active_project_phase["name"] if active_project_phase else "None"
    active_project_phase_description = (
        active_project_phase["description"]
        if active_project_phase and active_project_phase.get("description")
        else "No active project phase description is available."
    )

    # need this for the financial data page functions
    expenses = (
        db.session.query(Expense)
        .filter(Expense.project_id == project.id)
        .order_by(Expense.expense_date.desc())
        .all()
    )

    total_expenses = compute_total_expenses(expenses)
    recurring_cost_count = number_of_recurring_costs(expenses)
    next_year_cost = next_year_spending(expenses)
    category_split = category_cost_split_data(expenses)
    top_category = category_split["labels"][0] if category_split["labels"] else "unspecified"
    stakeholder_count = (
        db.session.query(ProjectPerson)
        .filter(ProjectPerson.project_id == project.id)
        .count()
    )
    role_distribution = build_role_distribution(project.id)

    if project.budget_amount is None:
        within_budget_text = "without an allocated budget set yet"
        within_budget_color = "#6b7280"
        budget_summary_text = "No project budget has been set for this workspace yet."
    else:
        budget_remaining = project.budget_amount - total_expenses

        if total_expenses <= project.budget_amount:
            within_budget_text = "within the allocated budget"
            within_budget_color = "#16a34a"
            budget_summary_text = f"${budget_remaining} remains in the current project budget."
        else:
            within_budget_text = "outside of the allocated budget"
            within_budget_color = "#dc2626"
            budget_summary_text = f"The project is currently ${abs(budget_remaining)} over budget."

    #
    # Element sequence for the reportlab library stuff
    # 
    # The pages are defined by these PageBreak() elements in the elements list
    #
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.95 * inch,
        bottomMargin=1.0 * inch,
    )
    styles = _get_report_styles()

    elements = [
        #
        # INTRO PAGE
        #
        Paragraph(project.title or '', styles["title"]),
        Spacer(1, 0.22 * inch),
        Paragraph(
            f'Generated {generated_at.strftime("%Y-%m-%d %I:%M %p %Z")} by {generated_by}.',
            styles["meta"],
        ),
        Paragraph(
            f'This report was automatically generated by Pandata based on the data that is available for Projet '
            f'"{project.title or ""}". Fresh reports can be generated at https://pandata.work',
            styles["meta"],
        ),
        Spacer(1, 0.32 * inch),
        Paragraph("Description", styles["heading"]),
        Spacer(1, 0.08 * inch),
        Paragraph(project.description or 'No description provided.', styles["body"]),
        Spacer(1, 0.32 * inch),
        Paragraph("Upcoming Events", styles["heading"]),
        Spacer(1, 0.12 * inch),
        _build_next_events_table(project, styles),
        PageBreak(),
        #
        # PROGRESS AND MILESTONES PAGE
        #
        Paragraph("Progress and Milestones", styles["title"]),
        Spacer(1, 0.28 * inch),
        Paragraph(
            (
                f"As of {generated_at.strftime('%A, %B %d, %Y')}, the project has been active for "
                f"{active_months_text}. Current timeline data expects all tasks will be completed on "
                f"{timeline_end_text}. Below is a distribution of events across the entire project's timespan."
            ),
            styles["body"],
        ),
        Spacer(1, 0.18 * inch),
        _build_event_distribution_chart(project, styles),
        Spacer(1, 0.22 * inch),
        Paragraph(f"<b>Active Project Phase</b>: {active_project_phase_name}", styles["body"]),
        Spacer(1, 0.06 * inch),
        Paragraph(active_project_phase_description, styles["meta"]),
        PageBreak(),
        #
        # PERFORMANCE AND FINANCIALS PAGE
        #
        Paragraph("Performance and Financials", styles["title"]),
        Spacer(1, 0.24 * inch),
        Paragraph(
                f"""
                This project is currently <font color="{within_budget_color}">{within_budget_text}</font>.
                Pandata is currently tracking {len(expenses)} individual expenses (consisting of annual, monthly and one time
                costs).
                """, 
                styles["body"]),
        Spacer(1, 0.24 * inch),
        Paragraph(f"<b>Allocated Project Budget</b>: $ {project.budget_amount if project.budget_amount is not None else 'Not set'}", styles["body"]),
        Paragraph(f"<b>Accumulated Expenses</b>: $ {total_expenses}", styles["body"]),
        Paragraph(f"<b>Recurring Cost Count</b>: {recurring_cost_count}", styles["body"]),
        Paragraph(f"<b>Projected Next-Year Recurring Spend</b>: $ {next_year_cost}", styles["body"]),
        Paragraph(f"<b>Largest Cost Category</b>: {top_category}", styles["body"]),
        Spacer(1, 0.08 * inch),
        Paragraph(budget_summary_text, styles["meta"]),
        Spacer(1, 0.18 * inch),
        _build_financial_category_chart(category_split, styles),
        PageBreak(),
        #
        # STAKEHOLDERS PAGE
        #
        Paragraph("Stakeholders", styles["title"]),
        Spacer(1, 0.22 * inch),
        Paragraph(
            (
                f"Pandata is currently tracking {stakeholder_count} assigned stakeholders for this project. "
                f"Current role mapping spans {role_distribution['total_roles']} distinct role categories."
            ),
            styles["body"],
        ),
        Spacer(1, 0.16 * inch),
        _build_role_distribution_chart(project.id, styles),
    ]

    doc.build(elements, onFirstPage=_decorate_page, onLaterPages=_decorate_page)
    buffer.seek(0)
    return buffer

def get_report_file_name(project_title):
    '''
    Builds filename for a report
    '''
    current = datetime.datetime.now()
    return f'report-{project_title}-{current.date()}.pdf'
