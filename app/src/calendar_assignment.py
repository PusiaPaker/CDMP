from __future__ import annotations

from flask import abort
from sqlalchemy import select

from app.core import db
from app.tables import GoogleCalendarSyncLink, Project, TimelineEvent, UnlistedTimelineEvent
from app.src.project.queries import get_projects_for_user, user_has_project_access


def get_assignment_project_options(user_id: str) -> list[dict[str, str | None]]:
    projects = get_projects_for_user(user_id)
    return [
        {"id": None, "label": "Unlisted"},
        *[
            {"id": project_id, "label": data["title"]}
            for project_id, data in sorted(projects.items(), key=lambda item: item[1]["title"].lower())
        ],
    ]


def _find_sync_link(local_kind: str, local_id: str) -> GoogleCalendarSyncLink | None:
    return (
        db.session.execute(
            select(GoogleCalendarSyncLink)
            .where(GoogleCalendarSyncLink.local_event_kind == local_kind)
            .where(GoogleCalendarSyncLink.local_event_id == local_id)
        )
        .scalars()
        .first()
    )


def reassign_calendar_event(
    user_id: str,
    event_kind: str,
    event_id: str,
    target_project_id: str | None,
) -> str:
    normalized_target = (target_project_id or "").strip() or None

    if normalized_target is not None and not user_has_project_access(user_id, normalized_target):
        abort(404)

    if event_kind == "unlisted":
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
            abort(404)

        if normalized_target is None:
            return "Event is already unlisted."

        project = db.session.get(Project, normalized_target)
        if project is None:
            abort(404)

        moved_event = TimelineEvent(
            project_id=project.id,
            title=event.title,
            description=event.description,
            start_date=event.start_date,
            end_date=event.end_date,
        )
        db.session.add(moved_event)
        db.session.flush()

        sync_link = _find_sync_link("unlisted", event.id)
        if sync_link:
            sync_link.local_event_kind = "project"
            sync_link.local_event_id = moved_event.id

        db.session.delete(event)
        db.session.commit()
        return f'Event moved to "{project.title}".'

    if event_kind == "project":
        event = db.session.get(TimelineEvent, event_id)
        if event is None or not user_has_project_access(user_id, event.project_id):
            abort(404)

        current_project = db.session.get(Project, event.project_id)

        if normalized_target == event.project_id:
            return f'Event is already in "{current_project.title if current_project else "this project"}".'

        if normalized_target is None:
            moved_event = UnlistedTimelineEvent(
                owner_user_id=user_id,
                title=event.title,
                description=event.description,
                start_date=event.start_date,
                end_date=event.end_date,
            )
            db.session.add(moved_event)
            db.session.flush()

            sync_link = _find_sync_link("project", event.id)
            if sync_link:
                sync_link.local_event_kind = "unlisted"
                sync_link.local_event_id = moved_event.id

            db.session.delete(event)
            db.session.commit()
            return "Event moved to Unlisted."

        project = db.session.get(Project, normalized_target)
        if project is None:
            abort(404)

        event.project_id = project.id
        db.session.commit()
        return f'Event moved to "{project.title}".'

    abort(404)


def update_calendar_event(
    user_id: str,
    event_kind: str,
    event_id: str,
    *,
    target_project_id: str | None,
    title: str,
    description: str | None,
    start_date,
    end_date,
) -> str:
    normalized_target = (target_project_id or "").strip() or None

    if normalized_target is not None and not user_has_project_access(user_id, normalized_target):
        abort(404)

    cleaned_description = (description or "").strip() or None

    if event_kind == "unlisted":
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
            abort(404)

        if normalized_target is None:
            event.title = title
            event.description = cleaned_description
            event.start_date = start_date
            event.end_date = end_date
            db.session.commit()
            return "Event updated."

        project = db.session.get(Project, normalized_target)
        if project is None:
            abort(404)

        moved_event = TimelineEvent(
            project_id=project.id,
            title=title,
            description=cleaned_description,
            start_date=start_date,
            end_date=end_date,
        )
        db.session.add(moved_event)
        db.session.flush()

        sync_link = _find_sync_link("unlisted", event.id)
        if sync_link:
            sync_link.local_event_kind = "project"
            sync_link.local_event_id = moved_event.id

        db.session.delete(event)
        db.session.commit()
        return f'Event updated and moved to "{project.title}".'

    if event_kind == "project":
        event = db.session.get(TimelineEvent, event_id)
        if event is None or not user_has_project_access(user_id, event.project_id):
            abort(404)

        if normalized_target is None:
            moved_event = UnlistedTimelineEvent(
                owner_user_id=user_id,
                title=title,
                description=cleaned_description,
                start_date=start_date,
                end_date=end_date,
            )
            db.session.add(moved_event)
            db.session.flush()

            sync_link = _find_sync_link("project", event.id)
            if sync_link:
                sync_link.local_event_kind = "unlisted"
                sync_link.local_event_id = moved_event.id

            db.session.delete(event)
            db.session.commit()
            return "Event updated and moved to Unlisted."

        project = db.session.get(Project, normalized_target)
        if project is None:
            abort(404)

        event.project_id = project.id
        event.title = title
        event.description = cleaned_description
        event.start_date = start_date
        event.end_date = end_date
        db.session.commit()
        return f'Event updated in "{project.title}".'

    abort(404)


def delete_calendar_event(user_id: str, event_kind: str, event_id: str) -> str:
    if event_kind == "unlisted":
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
            abort(404)

        sync_link = _find_sync_link("unlisted", event.id)
        if sync_link:
            db.session.delete(sync_link)
        db.session.delete(event)
        db.session.commit()
        return "Unlisted event removed from the calendar."

    if event_kind == "project":
        event = db.session.get(TimelineEvent, event_id)
        if event is None or not user_has_project_access(user_id, event.project_id):
            abort(404)

        sync_link = _find_sync_link("project", event.id)
        if sync_link:
            db.session.delete(sync_link)
        db.session.delete(event)
        db.session.commit()
        return "Project event removed from the calendar."

    abort(404)
