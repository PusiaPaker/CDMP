from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

import uuid

from app.core import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(unique=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True)
