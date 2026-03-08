from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, String

import uuid

from app.core import Base

class Person(Base):
    __tablename__ = "people"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))

    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    title: Mapped[str | None] = mapped_column(String(120), nullable=True)
