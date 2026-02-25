from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.src.database import Base


class PersonReport(Base):
    __tablename__ = "person_reports"

    person_id: Mapped[str] = mapped_column(
        ForeignKey("people.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    reports_to_id: Mapped[str] = mapped_column(
        ForeignKey("people.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
