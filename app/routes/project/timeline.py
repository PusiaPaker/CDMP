from __future__ import annotations

from calendar import Calendar, month_name
from collections import defaultdict
from datetime import date, datetime, timedelta

from flask import render_template, abort, request, jsonify, flash, redirect, url_for, session
from sqlalchemy import select, func

from app.core import db
from app.tables import Project, TimelineEvent, UnlistedTimelineEvent
from app.src.calendar_assignment import get_assignment_project_options
from app.src.project.queries import user_has_project_access

from .project import ProjectBP

MONTH_CALENDAR = Calendar(firstweekday=6)


def _get_project_or_404(project_id: str) -> Project:
    project = db.session.get(Project, project_id)
    if not project or not user_has_project_access(session["user_id"], project_id):
        abort(404)
    return project


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


def _parse_ics_datetime(value: str) -> tuple[datetime | None, bool]:
    cleaned = value.strip()

    for fmt, is_date_only in (
        ("%Y%m%dT%H%M%S%z", False),
        ("%Y%m%dT%H%M%SZ", False),
        ("%Y%m%dT%H%M%S", False),
        ("%Y%m%d", True),
    ):
        try:
            parsed = datetime.strptime(cleaned, fmt)
            if parsed.tzinfo is not None:
                parsed = parsed.astimezone().replace(tzinfo=None)
            return parsed, is_date_only
        except ValueError:
            continue

    return None, False


def _decode_ics_text(value: str | None) -> str | None:
    if value is None:
        return None

    decoded = (
        value.replace("\\n", "\n")
        .replace("\\N", "\n")
        .replace("\\,", ",")
        .replace("\\;", ";")
        .replace("\\\\", "\\")
        .strip()
    )
    return decoded or None


def _unfold_ics_lines(raw_text: str) -> list[str]:
    unfolded_lines: list[str] = []
    for line in raw_text.splitlines():
        if line.startswith((" ", "\t")) and unfolded_lines:
            unfolded_lines[-1] += line[1:]
        else:
            unfolded_lines.append(line.strip())
    return unfolded_lines


def _parse_ics_events(raw_text: str) -> tuple[list[dict], int]:
    pending_event: dict[str, str] | None = None
    raw_events: list[dict[str, str]] = []

    for line in _unfold_ics_lines(raw_text):
        if line == "BEGIN:VEVENT":
            pending_event = {}
            continue

        if line == "END:VEVENT":
            if pending_event is not None:
                raw_events.append(pending_event)
            pending_event = None
            continue

        if pending_event is None or ":" not in line:
            continue

        name, value = line.split(":", 1)
        property_name = name.split(";", 1)[0].upper()

        if property_name in {"SUMMARY", "DESCRIPTION", "DTSTART", "DTEND"} and property_name not in pending_event:
            pending_event[property_name] = value
            pending_event[f"{property_name}_META"] = name.upper()

    parsed_events: list[dict] = []
    skipped = 0

    for raw_event in raw_events:
        title = (_decode_ics_text(raw_event.get("SUMMARY")) or "").strip()
        description = _decode_ics_text(raw_event.get("DESCRIPTION"))
        start_value = raw_event.get("DTSTART")

        if not title or not start_value:
            skipped += 1
            continue

        start_date, start_is_date_only = _parse_ics_datetime(start_value)
        if start_date is None:
            skipped += 1
            continue

        end_date = None
        end_value = raw_event.get("DTEND")
        if end_value:
            parsed_end_date, end_is_date_only = _parse_ics_datetime(end_value)
            if parsed_end_date is not None:
                if start_is_date_only and end_is_date_only and parsed_end_date.date() > start_date.date():
                    parsed_end_date = parsed_end_date - timedelta(days=1)

                if parsed_end_date < start_date:
                    parsed_end_date = start_date

                if parsed_end_date != start_date:
                    end_date = parsed_end_date

        parsed_events.append(
            {
                "title": title[:100],
                "description": description[:256] if description else None,
                "start_date": start_date,
                "end_date": end_date,
            }
        )

    return parsed_events, skipped


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


def _build_calendar_weeks(year: int, month: int, events: list[TimelineEvent]) -> list[list[dict]]:
    events_by_day: dict[date, list[TimelineEvent]] = defaultdict(list)

    for event in events:
        current_day = event.start_date.date()
        last_day = (event.end_date or event.start_date).date()

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
                        key=lambda item: (item.start_date, item.title.lower()),
                    ),
                }
                for day in week
            ]
        )

    return calendar_weeks


def _build_month_link(project_id: str, year: int, month: int, selected_date: date) -> str:
    return url_for(
        "project.timeline",
        project_id=project_id,
        year=year,
        month=month,
        selected_date=selected_date.isoformat(),
    )


@ProjectBP.route("/<project_id>/timeline/", methods=["GET"])
def timeline(project_id):
    project = _get_project_or_404(project_id)
    user_id = session["user_id"]
    year, month = _resolve_month_request()
    selected_date = _resolve_selected_date(year, month)

    month_start = datetime(year, month, 1)
    next_year, next_month = _shift_month(year, month, 1)
    next_month_start = datetime(next_year, next_month, 1)

    month_events = (
        db.session.execute(
            select(TimelineEvent)
            .where(TimelineEvent.project_id == project_id)
            .where(TimelineEvent.start_date < next_month_start)
            .where(func.coalesce(TimelineEvent.end_date, TimelineEvent.start_date) >= month_start)
            .order_by(TimelineEvent.start_date.asc(), TimelineEvent.title.asc())
        )
        .scalars()
        .all()
    )

    all_events = (
        db.session.execute(
            select(TimelineEvent)
            .where(TimelineEvent.project_id == project_id)
            .order_by(TimelineEvent.start_date.asc(), TimelineEvent.title.asc())
        )
        .scalars()
        .all()
    )

    unlisted_events = (
        db.session.execute(
            select(UnlistedTimelineEvent)
            .where(UnlistedTimelineEvent.owner_user_id == user_id)
            .order_by(UnlistedTimelineEvent.start_date.asc(), UnlistedTimelineEvent.title.asc())
        )
        .scalars()
        .all()
    )

    previous_year, previous_month = _shift_month(year, month, -1)
    following_year, following_month = _shift_month(year, month, 1)

    event_years = {year, date.today().year}
    for event in all_events:
        event_years.add(event.start_date.year)
        if event.end_date:
            event_years.add(event.end_date.year)

    min_year = min(event_years) - 1
    max_year = max(event_years) + 1
    year_options = list(range(min_year, max_year + 1))
    month_options = [{"value": idx, "label": month_name[idx]} for idx in range(1, 13)]

    return render_template(
        "project/timeline.html.j2",
        project=project,
        active_project_id=project.id,
        calendar_weeks=_build_calendar_weeks(year, month, month_events),
        all_events=all_events,
        unlisted_events=unlisted_events,
        assignment_project_options=get_assignment_project_options(user_id),
        calendar_year=year,
        calendar_month=month,
        month_label=f"{month_name[month]} {year}",
        selected_date=selected_date,
        month_options=month_options,
        year_options=year_options,
        previous_month_link=_build_month_link(project.id, previous_year, previous_month, selected_date),
        next_month_link=_build_month_link(project.id, following_year, following_month, selected_date),
    ), 200


@ProjectBP.route("/<project_id>/timeline/events", methods=["POST"])
def create_timeline_event(project_id):
    project = _get_project_or_404(project_id)

    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip() or None
    start_date = _parse_date_field(request.form.get("start_date"))
    end_date = _parse_date_field(request.form.get("end_date"))

    if not title:
        flash("Event title is required.")
        return redirect(
            url_for(
                "project.timeline",
                project_id=project.id,
                year=request.form.get("return_year", type=int),
                month=request.form.get("return_month", type=int),
                selected_date=request.form.get("selected_date") or "",
            )
        )

    if start_date is None:
        flash("Please provide a valid start date.")
        return redirect(
            url_for(
                "project.timeline",
                project_id=project.id,
                year=request.form.get("return_year", type=int),
                month=request.form.get("return_month", type=int),
                selected_date=request.form.get("selected_date") or "",
            )
        )

    if end_date is not None and end_date < start_date:
        flash("End date cannot be earlier than start date.")
        return redirect(
            url_for(
                "project.timeline",
                project_id=project.id,
                year=request.form.get("return_year", type=int),
                month=request.form.get("return_month", type=int),
                selected_date=request.form.get("selected_date") or start_date.date().isoformat(),
            )
        )

    event = TimelineEvent(
        project_id=project.id,
        title=title[:100],
        description=description[:256] if description else None,
        start_date=start_date,
        end_date=end_date,
    )
    db.session.add(event)
    db.session.commit()

    flash("Event added to the project calendar.")
    return redirect(
        url_for(
            "project.timeline",
            project_id=project.id,
            year=start_date.year,
            month=start_date.month,
            selected_date=start_date.date().isoformat(),
        )
    )


@ProjectBP.route("/<project_id>/timeline/events/<event_id>/delete", methods=["POST"])
def delete_timeline_event(project_id, event_id):
    project = _get_project_or_404(project_id)
    event = db.session.get(TimelineEvent, event_id)

    if not event or event.project_id != project.id:
        return abort(404)

    db.session.delete(event)
    db.session.commit()

    flash("Event removed from the project calendar.")
    return redirect(
        url_for(
            "project.timeline",
            project_id=project.id,
            year=request.form.get("return_year", type=int),
            month=request.form.get("return_month", type=int),
            selected_date=request.form.get("selected_date") or "",
        )
    )


@ProjectBP.route("/<project_id>/timeline/import", methods=["POST"])
def import_timeline_events(project_id):
    project = _get_project_or_404(project_id)
    calendar_file = request.files.get("calendar_file")

    if not calendar_file or not calendar_file.filename:
        flash("Choose an .ics calendar file to import.")
        return redirect(
            url_for(
                "project.timeline",
                project_id=project.id,
                year=request.form.get("return_year", type=int),
                month=request.form.get("return_month", type=int),
                selected_date=request.form.get("selected_date") or "",
            )
        )

    if not calendar_file.filename.lower().endswith(".ics"):
        flash("Only .ics calendar exports are supported here.")
        return redirect(
            url_for(
                "project.timeline",
                project_id=project.id,
                year=request.form.get("return_year", type=int),
                month=request.form.get("return_month", type=int),
                selected_date=request.form.get("selected_date") or "",
            )
        )

    raw_bytes = calendar_file.read()
    try:
        raw_text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        raw_text = raw_bytes.decode("latin-1")

    parsed_events, skipped = _parse_ics_events(raw_text)
    if not parsed_events:
        flash("No importable events were found in that calendar file.")
        return redirect(
            url_for(
                "project.timeline",
                project_id=project.id,
                year=request.form.get("return_year", type=int),
                month=request.form.get("return_month", type=int),
                selected_date=request.form.get("selected_date") or "",
            )
        )

    for parsed_event in parsed_events:
        db.session.add(
            TimelineEvent(
                project_id=project.id,
                title=parsed_event["title"],
                description=parsed_event["description"],
                start_date=parsed_event["start_date"],
                end_date=parsed_event["end_date"],
            )
        )

    db.session.commit()

    imported = len(parsed_events)
    if skipped:
        flash(f"Imported {imported} events. Skipped {skipped} items that were incomplete or invalid.")
    else:
        flash(f"Imported {imported} events into the project calendar.")

    first_event = parsed_events[0]["start_date"]
    return redirect(
        url_for(
            "project.timeline",
            project_id=project.id,
            year=first_event.year,
            month=first_event.month,
            selected_date=first_event.date().isoformat(),
        )
    )

@ProjectBP.route("/<project_id>/timeline/debug", methods=["GET"])
def timeline_debug(project_id):
    project = _get_project_or_404(project_id)
    
    events = (
        db.session.execute(
            select(TimelineEvent)
            .where(TimelineEvent.project_id == project_id)
        )
        .scalars().all()
    )

    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'start_date': event.start_date,
            'end_date': event.end_date
        })

    return jsonify(events_data)
