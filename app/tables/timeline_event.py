from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy import DateTime, func
from datetime import datetime

import uuid

from app.core import Base

class TimelineEvent(Base):
    __tablename__ = "timeline_event"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    # connected project
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False) 

    title:Mapped[str] = mapped_column(String(100))
    description:Mapped[str] = mapped_column(String(256))

    # note: this is supposed to support both single-date events and events with start/end date
    # so end_date is nullable
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True
    )
