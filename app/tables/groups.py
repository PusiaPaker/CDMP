from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey
from app.src.database import Base
import uuid

class Group(Base):
    __tablename__ = "groups"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid()))
    project_id: Mapped[str | None]
    #project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id", onupdate="CASCADE", ondelete="SET NULL", nullable=True)
