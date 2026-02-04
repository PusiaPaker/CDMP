from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey
from app.src.database import Base
import uuid

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid()))
    owner_id: Mapped[str | None]
 
