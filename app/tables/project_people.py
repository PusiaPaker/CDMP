from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, UniqueConstraint, String
from app.src.database import Base


class ProjectPerson(Base):
    __tablename__ = "project_people"

    id: Mapped[int] = mapped_column(primary_key=True)

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    person_id: Mapped[str] = mapped_column(ForeignKey("people.id"), nullable=False)

    role_level: Mapped[str | None] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        UniqueConstraint("project_id", "person_id", name="uq_project_person"),
    )
