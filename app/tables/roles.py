from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey
from app.src.database import Base
import uuid

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    role: Mapped[str | None]
