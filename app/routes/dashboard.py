from calendar import Calendar, month_name
from collections import defaultdict
from datetime import date, datetime, timedelta

from flask import Blueprint, redirect, render_template, request, session, url_for, flash
from sqlalchemy import select

from app.src.calendar_assignment import (
    delete_calendar_event,
    get_assignment_project_options,
    reassign_calendar_event,
    update_calendar_event,
)
from app.src.google_calendar import GoogleCalendarSyncError, has_google_calendar_connection, sync_primary_google_calendar
from app.src.project.queries import get_projects_for_user, user_has_project_access

from app.core import db
from app.tables import User, TimelineEvent, Project, Role, UnlistedTimelineEvent


DashBP = Blueprint("dashboard", __name__)
MONTH_CALENDAR = Calendar(firstweekday=6)


def _resolve_month_request() -> tuple[int, int]:
    today = date.today()
    year = request.args.get("year", type=int) or today.year
    month = request.args.get("month", type=int) or today.month

    if month < 1 or month > 12:
        month = today.month

    return year, month


def _shift_month(year: int, month: int, offset: int) -> tuple[int, int]:
    shifted = month - 1 + offset
    shifted_year = year + (shifted // 12)
    shifted_month = (shifted % 12) + 1
    return shifted_year, shifted_month


def _resolve_selected_date(year: int, month: int) -> date:
    selected_date = request.args.get("selected_date", "").strip()
    if selected_date:
        try:
            parsed = datetime.strptime(selected_date, "%Y-%m-%d").date()
            if parsed.year == year and parsed.month == month:
                return parsed
        except ValueError:
            pass

    today = date.today()
    if today.year == year and today.month == month:
        return today

    return date(year, month, 1)


def _build_month_link(year: int, month: int, selected_date: date) -> str:
    return url_for(
        "dashboard.timeline",
        year=year,
        month=month,
        selected_date=selected_date.isoformat(),
    )


def _event_overlaps_month(event: dict, month_start: datetime, next_month_start: datetime) -> bool:
    event_end = event["end"] or event["start"]
    return event["start"] < next_month_start and event_end >= month_start


def _build_calendar_weeks(year: int, month: int, events: list[dict]) -> list[list[dict]]:
    events_by_day: dict[date, list[dict]] = defaultdict(list)

    for event in events:
        current_day = event["start"].date()
        last_day = (event["end"] or event["start"]).date()

        while current_day <= last_day:
            events_by_day[current_day].append(event)
            current_day += timedelta(days=1)

    today = date.today()
    calendar_weeks: list[list[dict]] = []

    for week in MONTH_CALENDAR.monthdatescalendar(year, month):
        calendar_weeks.append(
            [
                {
                    "date": day,
                    "is_current_month": day.month == month,
                    "is_today": day == today,
                    "events": sorted(
                        events_by_day.get(day, []),
                        key=lambda item: (item["start"], item["content"].lower()),
                    ),
                }
                for day in week
            ]
        )

    return calendar_weeks

@DashBP.before_request
def require_login():
    if "user_id" not in session:
        return redirect(url_for("authentication.login", next=request.path))

@DashBP.route("/")
def main():
    user_id = session["user_id"]

    user = db.session.get(User, user_id)
    username = user.username if user else "User"

    projects = get_projects_for_user(user_id)

    return render_template(
        "dashboard/home.html.j2",
        projects=projects,
    ), 200

@DashBP.route("/timeline")
def timeline():
    user_id = session["user_id"]
    year, month = _resolve_month_request()
    selected_date = _resolve_selected_date(year, month)

    projects = get_projects_for_user(user_id)

    events = (
        db.session.execute(
            select(TimelineEvent, Project.title)
            .join(Project, TimelineEvent.project_id == Project.id)
            .join(Role, Role.project_id == Project.id)
            .where(Role.user_id == user_id)
            .distinct()
            .order_by(Project.title, TimelineEvent.start_date, TimelineEvent.end_date)
        )
        .all()
    )

    timeline_events = []
    for event, project_title in events:
        timeline_events.append({
            'id': event.id,
            'kind': 'project',
            'project_id': event.project_id,
            'project_title': project_title,
            'content': event.title,
            'description': event.description,
            'start': event.start_date,
            'end': event.end_date,
            'missing_start': False,
        })

    unlisted_events = (
        db.session.execute(
            select(UnlistedTimelineEvent)
            .where(UnlistedTimelineEvent.owner_user_id == user_id)
            .order_by(UnlistedTimelineEvent.start_date, UnlistedTimelineEvent.end_date, UnlistedTimelineEvent.title)
        )
        .scalars()
        .all()
    )

    for event in unlisted_events:
        timeline_events.append({
            'id': event.id,
            'kind': 'unlisted',
            'project_id': None,
            'project_title': 'Unlisted',
            'content': event.title,
            'description': event.description,
            'start': event.start_date,
            'end': event.end_date,
            'missing_start': False,
        })

    timeline_events.sort(
        key=lambda event: (
            event["start"] or datetime.max,
            event["end"] or datetime.max,
            event["content"].lower(),
        )
    )

    month_start = datetime(year, month, 1)
    next_year, next_month = _shift_month(year, month, 1)
    next_month_start = datetime(next_year, next_month, 1)
    month_events = [
        event for event in timeline_events
        if _event_overlaps_month(event, month_start, next_month_start)
    ]

    previous_year, previous_month = _shift_month(year, month, -1)
    following_year, following_month = _shift_month(year, month, 1)

    event_years = {year, date.today().year}
    for event in timeline_events:
        event_years.add(event["start"].year)
        if event["end"]:
            event_years.add(event["end"].year)

    min_year = min(event_years) - 1
    max_year = max(event_years) + 1
    year_options = list(range(min_year, max_year + 1))
    month_options = [{"value": idx, "label": month_name[idx]} for idx in range(1, 13)]

    return render_template(
        "dashboard/timeline.html",
        dashboard_title=f"Global Calendar ",
        description="Track global and project-specific events in calendar view.",
        projects=projects,
        assignment_project_options=get_assignment_project_options(user_id),
        google_calendar_connected=has_google_calendar_connection(user_id),
        timeline_events=timeline_events,
        calendar_weeks=_build_calendar_weeks(year, month, month_events),
        calendar_year=year,
        calendar_month=month,
        selected_date=selected_date,
        month_options=month_options,
        year_options=year_options,
        previous_month_link=_build_month_link(previous_year, previous_month, selected_date),
        next_month_link=_build_month_link(following_year, following_month, selected_date),
    ), 200


def _parse_date_field(value: str | None) -> datetime | None:
    if not value:
        return None

    cleaned = value.strip()
    if not cleaned:
        return None

    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue

    return None


@DashBP.route("/timeline/unlisted", methods=["POST"])
def create_unlisted_timeline_event():
    user_id = session["user_id"]

    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip() or None
    start_date = _parse_date_field(request.form.get("start_date"))
    end_date = _parse_date_field(request.form.get("end_date"))
    target_project_id = (request.form.get("target_project_id") or "").strip() or None

    if not title:
        flash("Event title is required.")
        return redirect(
            url_for(
                "dashboard.timeline",
                year=request.form.get("return_year", type=int),
                month=request.form.get("return_month", type=int),
                selected_date=request.form.get("selected_date") or "",
            )
        )

    if start_date is None:
        flash("Please provide a valid start date for the unlisted event.")
        return redirect(
            url_for(
                "dashboard.timeline",
                year=request.form.get("return_year", type=int),
                month=request.form.get("return_month", type=int),
                selected_date=request.form.get("selected_date") or "",
            )
        )

    if end_date is not None and end_date < start_date:
        flash("End date cannot be earlier than start date.")
        return redirect(
            url_for(
                "dashboard.timeline",
                year=request.form.get("return_year", type=int),
                month=request.form.get("return_month", type=int),
                selected_date=request.form.get("selected_date") or start_date.date().isoformat(),
            )
        )

    if target_project_id and not user_has_project_access(user_id, target_project_id):
        flash("That project could not be found.")
        return redirect(
            url_for(
                "dashboard.timeline",
                year=request.form.get("return_year", type=int),
                month=request.form.get("return_month", type=int),
                selected_date=request.form.get("selected_date") or start_date.date().isoformat(),
            )
        )

    if target_project_id:
        event = TimelineEvent(
            project_id=target_project_id,
            title=title[:100],
            description=description[:256] if description else None,
            start_date=start_date,
            end_date=end_date,
        )
        success_message = "Event added to the selected project."
    else:
        event = UnlistedTimelineEvent(
            owner_user_id=user_id,
            title=title[:100],
            description=description[:256] if description else None,
            start_date=start_date,
            end_date=end_date,
        )
        success_message = "Event added to the universal calendar."

    db.session.add(event)
    db.session.commit()

    flash(success_message)
    return redirect(
        url_for(
            "dashboard.timeline",
            year=start_date.year,
            month=start_date.month,
            selected_date=start_date.date().isoformat(),
        )
    )


@DashBP.route("/timeline/unlisted/<event_id>/delete", methods=["POST"])
def delete_unlisted_timeline_event(event_id):
    user_id = session["user_id"]

    event = (
        db.session.execute(
            select(UnlistedTimelineEvent)
            .where(UnlistedTimelineEvent.id == event_id)
            .where(UnlistedTimelineEvent.owner_user_id == user_id)
        )
        .scalars()
        .first()
    )

    if event is None:
        flash("That unlisted event could not be found.")
        return redirect(
            url_for(
                "dashboard.timeline",
                year=request.form.get("return_year", type=int),
                month=request.form.get("return_month", type=int),
                selected_date=request.form.get("selected_date") or "",
            )
        )

    db.session.delete(event)
    db.session.commit()

    flash("Unlisted event removed from the universal calendar.")
    return redirect(
        url_for(
            "dashboard.timeline",
            year=request.form.get("return_year", type=int),
            month=request.form.get("return_month", type=int),
            selected_date=request.form.get("selected_date") or "",
        )
    )


@DashBP.route("/timeline/events/<event_kind>/<event_id>/project", methods=["POST"])
def update_event_project(event_kind, event_id):
    user_id = session["user_id"]
    target_project_id = request.form.get("target_project_id")

    flash(reassign_calendar_event(user_id, event_kind, event_id, target_project_id))

    return_target = (request.form.get("return_to") or "").strip()
    if return_target.startswith("/"):
        return redirect(return_target)

    return redirect(url_for("dashboard.timeline"))


@DashBP.route("/timeline/google/refresh", methods=["POST"])
def refresh_google_calendar():
    user_id = session["user_id"]

    try:
        result = sync_primary_google_calendar(user_id)
        flash(
            f"Google Calendar refreshed. Added {result.created}, updated {result.updated}, removed {result.removed}."
        )
    except GoogleCalendarSyncError as exc:
        flash(str(exc))

    return redirect(
        url_for(
            "dashboard.timeline",
            year=request.form.get("return_year", type=int),
            month=request.form.get("return_month", type=int),
            selected_date=request.form.get("selected_date") or "",
        )
    )


@DashBP.route("/timeline/events/<event_kind>/<event_id>/update", methods=["POST"])
def update_event_details(event_kind, event_id):
    user_id = session["user_id"]

    title = (request.form.get("title") or "").strip()
    description = request.form.get("description")
    start_date = _parse_date_field(request.form.get("start_date"))
    end_date = _parse_date_field(request.form.get("end_date"))
    target_project_id = request.form.get("target_project_id")

    if not title:
        flash("Event title is required.")
    elif start_date is None:
        flash("Please provide a valid start date.")
    elif end_date is not None and end_date < start_date:
        flash("End date cannot be earlier than start date.")
    else:
        flash(
            update_calendar_event(
                user_id,
                event_kind,
                event_id,
                target_project_id=target_project_id,
                title=title[:100],
                description=(description or "")[:256] if description else None,
                start_date=start_date,
                end_date=end_date,
            )
        )

    return_target = (request.form.get("return_to") or "").strip()
    if return_target.startswith("/"):
        return redirect(return_target)

    return redirect(url_for("dashboard.timeline"))


@DashBP.route("/timeline/events/<event_kind>/<event_id>/delete", methods=["POST"])
def delete_any_event(event_kind, event_id):
    user_id = session["user_id"]
    flash(delete_calendar_event(user_id, event_kind, event_id))

    return_target = (request.form.get("return_to") or "").strip()
    if return_target.startswith("/"):
        return redirect(return_target)

    return redirect(url_for("dashboard.timeline"))
