from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import quote

import requests
from cryptography.fernet import Fernet
from flask import current_app
from sqlalchemy import select

from app.core import db
from app.tables import (
    GoogleCalendarSyncLink,
    GoogleCalendarToken,
    TimelineEvent,
    UnlistedTimelineEvent,
)


GOOGLE_CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"
PRIMARY_CALENDAR_ID = "primary"


class GoogleCalendarSyncError(Exception):
    pass


@dataclass
class GoogleCalendarSyncResult:
    created: int = 0
    updated: int = 0
    removed: int = 0
    total_seen: int = 0


def _fernet() -> Fernet:
    secret_key = current_app.config.get("SECRET_KEY", "")
    digest = hashlib.sha256(secret_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_google_refresh_token(refresh_token: str) -> str:
    return _fernet().encrypt(refresh_token.encode("utf-8")).decode("utf-8")


def decrypt_google_refresh_token(refresh_token_encrypted: str) -> str:
    return _fernet().decrypt(refresh_token_encrypted.encode("utf-8")).decode("utf-8")


def _get_google_metadata() -> dict:
    response = requests.get(current_app.config["GOOGLE_DISCOVERY_URL"], timeout=15)
    response.raise_for_status()
    return response.json()


def _refresh_access_token(refresh_token: str) -> str:
    metadata = _get_google_metadata()
    response = requests.post(
        metadata["token_endpoint"],
        data={
            "client_id": current_app.config["GOOGLE_CLIENT_ID"],
            "client_secret": current_app.config["GOOGLE_CLIENT_SECRET"],
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout=15,
    )

    if response.status_code >= 400:
        raise GoogleCalendarSyncError("Google token refresh failed. Please sign in with Google again.")

    payload = response.json()
    access_token = payload.get("access_token")
    if not access_token:
        raise GoogleCalendarSyncError("Google did not return an access token for calendar sync.")

    return access_token


def _parse_google_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def _parse_google_event_dates(event: dict) -> tuple[datetime | None, datetime | None]:
    start = event.get("start") or {}
    end = event.get("end") or {}

    if start.get("date"):
        start_date = datetime.strptime(start["date"], "%Y-%m-%d")
        end_date = None
        if end.get("date"):
            parsed_end = datetime.strptime(end["date"], "%Y-%m-%d")
            if parsed_end.date() > start_date.date():
                parsed_end -= timedelta(days=1)
            if parsed_end.date() > start_date.date():
                end_date = parsed_end
        return start_date, end_date

    start_value = start.get("dateTime")
    if not start_value:
        return None, None

    start_date = _parse_google_datetime(start_value)
    end_value = end.get("dateTime")
    end_date = _parse_google_datetime(end_value) if end_value else None

    if end_date is not None and end_date <= start_date:
        end_date = None

    return start_date, end_date


def _fetch_primary_calendar_events(access_token: str) -> list[dict]:
    page_token = None
    events: list[dict] = []
    calendar_id = quote(PRIMARY_CALENDAR_ID, safe="")

    while True:
        response = requests.get(
            f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "singleEvents": "true",
                "showDeleted": "false",
                "orderBy": "startTime",
                "maxResults": 2500,
                "pageToken": page_token,
            },
            timeout=20,
        )

        if response.status_code >= 400:
            raise GoogleCalendarSyncError("Google Calendar refresh failed. Confirm Calendar API access is enabled.")

        payload = response.json()
        events.extend(payload.get("items", []))
        page_token = payload.get("nextPageToken")
        if not page_token:
            break

    return events


def has_google_calendar_connection(user_id: str) -> bool:
    return (
        db.session.execute(
            select(GoogleCalendarToken).where(GoogleCalendarToken.user_id == user_id)
        )
        .scalars()
        .first()
        is not None
    )


def _get_local_event_from_link(user_id: str, link: GoogleCalendarSyncLink):
    if link.local_event_kind == "unlisted":
        return (
            db.session.execute(
                select(UnlistedTimelineEvent)
                .where(UnlistedTimelineEvent.id == link.local_event_id)
                .where(UnlistedTimelineEvent.owner_user_id == user_id)
            )
            .scalars()
            .first()
        )

    if link.local_event_kind == "project":
        return db.session.get(TimelineEvent, link.local_event_id)

    return None


def _update_link_to_new_local_event(link: GoogleCalendarSyncLink, local_kind: str, local_id: str) -> None:
    link.local_event_kind = local_kind
    link.local_event_id = local_id


def sync_primary_google_calendar(user_id: str) -> GoogleCalendarSyncResult:
    token_row = (
        db.session.execute(
            select(GoogleCalendarToken).where(GoogleCalendarToken.user_id == user_id)
        )
        .scalars()
        .first()
    )
    if token_row is None:
        raise GoogleCalendarSyncError("Google Calendar is not connected for this account.")

    refresh_token = decrypt_google_refresh_token(token_row.refresh_token_encrypted)
    access_token = _refresh_access_token(refresh_token)
    google_events = _fetch_primary_calendar_events(access_token)

    result = GoogleCalendarSyncResult(total_seen=len(google_events))
    seen_event_ids: set[str] = set()

    for google_event in google_events:
        google_event_id = (google_event.get("id") or "").strip()
        if not google_event_id:
            continue

        seen_event_ids.add(google_event_id)
        start_date, end_date = _parse_google_event_dates(google_event)
        if start_date is None:
            continue

        title = (google_event.get("summary") or "").strip() or "Untitled Google event"
        description = (google_event.get("description") or "").strip() or None
        google_updated = google_event.get("updated")

        link = (
            db.session.execute(
                select(GoogleCalendarSyncLink)
                .where(GoogleCalendarSyncLink.user_id == user_id)
                .where(GoogleCalendarSyncLink.google_calendar_id == PRIMARY_CALENDAR_ID)
                .where(GoogleCalendarSyncLink.google_event_id == google_event_id)
            )
            .scalars()
            .first()
        )

        if link is None:
            local_event = UnlistedTimelineEvent(
                owner_user_id=user_id,
                title=title[:100],
                description=description[:256] if description else None,
                start_date=start_date,
                end_date=end_date,
            )
            db.session.add(local_event)
            db.session.flush()

            db.session.add(
                GoogleCalendarSyncLink(
                    user_id=user_id,
                    google_calendar_id=PRIMARY_CALENDAR_ID,
                    google_event_id=google_event_id,
                    local_event_kind="unlisted",
                    local_event_id=local_event.id,
                    last_google_updated=google_updated,
                )
            )
            result.created += 1
            continue

        local_event = _get_local_event_from_link(user_id, link)
        if local_event is None:
            local_event = UnlistedTimelineEvent(
                owner_user_id=user_id,
                title=title[:100],
                description=description[:256] if description else None,
                start_date=start_date,
                end_date=end_date,
            )
            db.session.add(local_event)
            db.session.flush()
            _update_link_to_new_local_event(link, "unlisted", local_event.id)
            link.last_google_updated = google_updated
            result.created += 1
            continue

        local_event.title = title[:100]
        local_event.description = description[:256] if description else None
        local_event.start_date = start_date
        local_event.end_date = end_date
        link.last_google_updated = google_updated
        result.updated += 1

    stale_links = (
        db.session.execute(
            select(GoogleCalendarSyncLink)
            .where(GoogleCalendarSyncLink.user_id == user_id)
            .where(GoogleCalendarSyncLink.google_calendar_id == PRIMARY_CALENDAR_ID)
        )
        .scalars()
        .all()
    )

    for link in stale_links:
        if link.google_event_id in seen_event_ids:
            continue

        local_event = _get_local_event_from_link(user_id, link)
        if local_event is not None:
            db.session.delete(local_event)
        db.session.delete(link)
        result.removed += 1

    db.session.commit()
    return result
