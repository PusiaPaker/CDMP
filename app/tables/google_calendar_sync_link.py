from datetime import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core import Base


class GoogleCalendarSyncLink(Base):
    __tablename__ = "google_calendar_sync_link"
    __table_args__ = (
        UniqueConstraint("user_id", "google_calendar_id", "google_event_id", name="uq_google_calendar_sync_link"),
    )

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    google_calendar_id: Mapped[str] = mapped_column(String(255), nullable=False)
    google_event_id: Mapped[str] = mapped_column(String(512), nullable=False)
    local_event_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    local_event_id: Mapped[str] = mapped_column(String(64), nullable=False)
    last_google_updated: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
