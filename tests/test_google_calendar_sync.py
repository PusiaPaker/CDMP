from datetime import datetime

from app.core import db
from app.src.google_calendar import (
    PRIMARY_CALENDAR_ID,
    _should_skip_google_event,
    encrypt_google_refresh_token,
    sync_primary_google_calendar,
)
from app.tables import GoogleCalendarSyncLink, GoogleCalendarToken, UnlistedTimelineEvent


def test_should_skip_google_birthday_events():
    assert _should_skip_google_event({"eventType": "birthday", "summary": "Team lunch"}) is True
    assert _should_skip_google_event({"birthdayProperties": {"type": "birthday"}, "summary": "Alex"}) is True
    assert _should_skip_google_event({"summary": "Happy Birthday"}) is True
    assert _should_skip_google_event({"summary": "Quarterly Planning"}) is False


def test_sync_primary_google_calendar_filters_birthday_events_and_removes_existing_birthdays(
    app_ctx, make_user, monkeypatch
):
    user = make_user(username="calendar-owner")

    token = GoogleCalendarToken(
        user_id=user.id,
        refresh_token_encrypted=encrypt_google_refresh_token("refresh-token"),
        scopes="openid email profile https://www.googleapis.com/auth/calendar.readonly",
    )
    db.session.add(token)

    stale_birthday_event = UnlistedTimelineEvent(
        owner_user_id=user.id,
        title="Happy Birthday",
        description=None,
        start_date=datetime(2026, 4, 13),
        end_date=None,
    )
    db.session.add(stale_birthday_event)
    db.session.flush()

    db.session.add(
        GoogleCalendarSyncLink(
            user_id=user.id,
            google_calendar_id=PRIMARY_CALENDAR_ID,
            google_event_id="birthday-1",
            local_event_kind="unlisted",
            local_event_id=stale_birthday_event.id,
            last_google_updated="2026-04-13T00:00:00Z",
        )
    )
    db.session.commit()

    monkeypatch.setattr("app.src.google_calendar._refresh_access_token", lambda refresh_token: "access-token")
    monkeypatch.setattr(
        "app.src.google_calendar._fetch_primary_calendar_events",
        lambda access_token: [
            {
                "id": "birthday-1",
                "summary": "Happy Birthday",
                "eventType": "birthday",
                "start": {"date": "2026-04-13"},
                "end": {"date": "2026-04-14"},
                "updated": "2026-04-13T00:00:00Z",
            },
            {
                "id": "meeting-1",
                "summary": "Weekly Sync",
                "description": "Project status review",
                "start": {"dateTime": "2026-04-14T15:00:00Z"},
                "end": {"dateTime": "2026-04-14T15:30:00Z"},
                "updated": "2026-04-14T12:00:00Z",
            },
        ],
    )

    result = sync_primary_google_calendar(user.id)

    remaining_events = (
        db.session.query(UnlistedTimelineEvent)
        .filter(UnlistedTimelineEvent.owner_user_id == user.id)
        .order_by(UnlistedTimelineEvent.title.asc())
        .all()
    )
    remaining_links = (
        db.session.query(GoogleCalendarSyncLink)
        .filter(GoogleCalendarSyncLink.user_id == user.id)
        .order_by(GoogleCalendarSyncLink.google_event_id.asc())
        .all()
    )

    assert result.created == 1
    assert result.updated == 0
    assert result.removed == 1
    assert [event.title for event in remaining_events] == ["Weekly Sync"]
    assert remaining_events[0].description == "Project status review"
    assert remaining_events[0].start_date == datetime(2026, 4, 14, 11, 0)
    assert remaining_events[0].end_date == datetime(2026, 4, 14, 11, 30)
    assert [link.google_event_id for link in remaining_links] == ["meeting-1"]
