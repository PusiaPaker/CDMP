import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.src.database import Base


class Person(Base):
    __tablename__ = "people"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    linkedin_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
