from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal

from app.core import db
from app.routes.project.timeline import _parse_ics_events
from app.src.project.mapper import expenses_mapping_handler, events_mapping_handler, people_mapping_handler
from app.tables import Expense, Person, ProjectPerson, TimelineEvent


def _mapped_indexes(mapping):
    return defaultdict(lambda: None, mapping)


def test_people_import_counts_existing_person_assigned_to_project_as_created(app_ctx, make_user, make_project):
    owner = make_user(username="owner")
    project = make_project(owner_id=owner.id, title="Import Project")

    existing_person = Person(
        name="Jordan Lee",
        email="jordan@example.com",
        phone="555-111-2222",
        title="Director",
    )
    db.session.add(existing_person)
    db.session.commit()

    rows = [["Jordan Lee", "jordan@example.com", "555-111-2222", "Director", "Executive Sponsor"]]
    mapped_to_index = _mapped_indexes({
        "Name": 0,
        "Email": 1,
        "Phone": 2,
        "Job Title": 3,
        "Role": 4,
    })

    commit_status = people_mapping_handler(project.id, rows, mapped_to_index)

    assert commit_status["created"] == 1
    assert commit_status["created_people"] == 0
    assert commit_status["skipped"] == 0
    assert db.session.query(ProjectPerson).filter_by(project_id=project.id, person_id=existing_person.id).count() == 1


def test_expenses_import_accepts_flexible_dates_amount_formats_and_aliases(app_ctx, make_user, make_project):
    owner = make_user(username="owner")
    project = make_project(owner_id=owner.id, title="Expense Import Project")

    rows = [
        ["ERP Implementation", None, "$40,000.50", "2/1/2025", "One time", None],
        ["Annual Support", "Covers vendor support", "12000", "April 6, 2026", "annually", "license fees"],
        ["Ops Platform", "", "1,250", date(2026, 7, 1), "month", ""],
    ]
    mapped_to_index = _mapped_indexes({
        "Expense Name": 0,
        "Expense Purpose": 1,
        "Amount": 2,
        "Date": 3,
        "Frequency": 4,
        "Category": 5,
    })

    commit_status = expenses_mapping_handler(project.id, rows, mapped_to_index)

    assert commit_status == {"created": 3, "skipped": 0}

    imported_expenses = (
        db.session.query(Expense)
        .filter(Expense.project_id == project.id)
        .order_by(Expense.expense_name.asc())
        .all()
    )

    assert len(imported_expenses) == 3

    annual_support = imported_expenses[0]
    erp_implementation = imported_expenses[1]
    ops_platform = imported_expenses[2]

    assert annual_support.amount == Decimal("12000.00")
    assert annual_support.expense_date == date(2026, 4, 6)
    assert annual_support.recurrence_type == "annual"
    assert annual_support.category == "license fees"

    assert erp_implementation.amount == Decimal("40000.50")
    assert erp_implementation.expense_date == date(2025, 2, 1)
    assert erp_implementation.recurrence_type == "one_time"
    assert erp_implementation.category == "unspecified"
    assert erp_implementation.expense_purpose == ""

    assert ops_platform.amount == Decimal("1250.00")
    assert ops_platform.expense_date == date(2026, 7, 1)
    assert ops_platform.recurrence_type == "monthly"
    assert ops_platform.category == "unspecified"


def test_expenses_import_skips_missing_required_fields_and_invalid_values(app_ctx, make_user, make_project):
    owner = make_user(username="owner")
    project = make_project(owner_id=owner.id, title="Expense Skip Project")

    rows = [
        ["", "Missing name", "100", "2025-01-01", "monthly", "ops"],
        ["Bad Amount", "", "twelve dollars", "2025-01-01", "monthly", "ops"],
        ["Bad Frequency", "", "100", "2025-01-01", "weekly", "ops"],
        ["No Date", "", "100", "", "monthly", "ops"],
        ["Valid Cost", "Accepted row", "$1,250.25", "April 7 2026", "yearly", "misc"],
    ]
    mapped_to_index = _mapped_indexes({
        "Expense Name": 0,
        "Expense Purpose": 1,
        "Amount": 2,
        "Date": 3,
        "Frequency": 4,
        "Category": 5,
    })

    commit_status = expenses_mapping_handler(project.id, rows, mapped_to_index)

    assert commit_status == {"created": 1, "skipped": 4}

    imported_expenses = db.session.query(Expense).filter(Expense.project_id == project.id).all()

    assert len(imported_expenses) == 1
    assert imported_expenses[0].expense_name == "Valid Cost"
    assert imported_expenses[0].amount == Decimal("1250.25")
    assert imported_expenses[0].expense_date == date(2026, 4, 7)
    assert imported_expenses[0].recurrence_type == "annual"


def test_timeline_import_accepts_mixed_date_formats_ranges_and_single_dates(app_ctx, make_user, make_project):
    owner = make_user(username="owner")
    project = make_project(owner_id=owner.id, title="Timeline Import Project")

    rows = [
        ["Kickoff", "2025-01-15", "", "Project starts"],
        ["Planning Phase", "2/1/2025", "4/15/2025", "Plan the work"],
        ["Go Live", "", "April 6, 2026", "Release day"],
        ["Training", datetime(2026, 5, 1, 14, 30), "", "Live session"],
    ]
    mapped_to_index = _mapped_indexes({
        "Title": 0,
        "Start Date": 1,
        "End Date": 2,
        "Description": 3,
    })

    commit_status = events_mapping_handler(project.id, rows, mapped_to_index)

    assert commit_status == {"created": 4, "skipped": 0}

    imported_events = (
        db.session.query(TimelineEvent)
        .filter(TimelineEvent.project_id == project.id)
        .order_by(TimelineEvent.title.asc())
        .all()
    )

    assert len(imported_events) == 4

    go_live = next(event for event in imported_events if event.title == "Go Live")
    kickoff = next(event for event in imported_events if event.title == "Kickoff")
    planning_phase = next(event for event in imported_events if event.title == "Planning Phase")
    training = next(event for event in imported_events if event.title == "Training")

    assert kickoff.start_date == datetime(2025, 1, 15)
    assert kickoff.end_date is None

    assert planning_phase.start_date == datetime(2025, 2, 1)
    assert planning_phase.end_date == datetime(2025, 4, 15)
    assert planning_phase.description == "Plan the work"

    assert go_live.start_date == datetime(2026, 4, 6)
    assert go_live.end_date is None

    assert training.start_date == datetime(2026, 5, 1, 14, 30)
    assert training.end_date is None


def test_timeline_import_skips_missing_titles_dates_and_invalid_date_values(app_ctx, make_user, make_project):
    owner = make_user(username="owner")
    project = make_project(owner_id=owner.id, title="Timeline Skip Project")

    rows = [
        ["", "2025-01-01", "", "Missing title"],
        ["No Dates", "", "", "Missing both dates"],
        ["Bad Start", "not-a-date", "", "Invalid start date"],
        ["Bad Range", "2025-01-01", "definitely-not-a-date", "Invalid end date"],
        ["Valid Milestone", "", "7/4/2026", "Holiday checkpoint"],
    ]
    mapped_to_index = _mapped_indexes({
        "Title": 0,
        "Start Date": 1,
        "End Date": 2,
        "Description": 3,
    })

    commit_status = events_mapping_handler(project.id, rows, mapped_to_index)

    assert commit_status == {"created": 1, "skipped": 4}

    imported_events = db.session.query(TimelineEvent).filter(TimelineEvent.project_id == project.id).all()

    assert len(imported_events) == 1
    assert imported_events[0].title == "Valid Milestone"
    assert imported_events[0].start_date == datetime(2026, 7, 4)
    assert imported_events[0].end_date is None


def test_ics_import_treats_same_day_events_as_deadlines():
    raw_text = """BEGIN:VCALENDAR
BEGIN:VEVENT
SUMMARY:Design Review
DTSTART:20260415T090000
DTEND:20260415T103000
DESCRIPTION:Review final mockups
END:VEVENT
BEGIN:VEVENT
SUMMARY:Launch Window
DTSTART:20260420T090000
DTEND:20260422T170000
END:VEVENT
END:VCALENDAR"""

    parsed_events, skipped = _parse_ics_events(raw_text)

    assert skipped == 0
    assert len(parsed_events) == 2
    assert parsed_events[0]["title"] == "Design Review"
    assert parsed_events[0]["start_date"] == datetime(2026, 4, 15, 9, 0)
    assert parsed_events[0]["end_date"] is None
    assert parsed_events[1]["title"] == "Launch Window"
    assert parsed_events[1]["end_date"] == datetime(2026, 4, 22, 17, 0)
