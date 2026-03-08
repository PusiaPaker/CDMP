from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy import DateTime, func
from datetime import datetime

import uuid

from app.core import Base

class File(Base):
    __tablename__ = "files"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    # connected project
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False) 

    # original name of uploaded file
    file_name_original: Mapped[str] = mapped_column(String(150))

    # name of file on the disk
    # will be "id.extension"
    file_name_disk: Mapped[str] = mapped_column(String(150))

    # this one is just one of: {unspecified, image, spreadsheet, text}
    # we might need it later on
    file_category:Mapped[str] = mapped_column(String(20))

    description: Mapped[str] = mapped_column(Text)
    upload_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
