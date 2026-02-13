from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, String, Text
from app.src.database import Base
import uuid

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str | None]
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)