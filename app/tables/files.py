from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, String, Text
from app.src.database import Base
import uuid
from sqlalchemy import DateTime, func
from datetime import datetime

class File(Base):
    __tablename__ = "files"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    # connected project
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False) 
    file_name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    upload_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )