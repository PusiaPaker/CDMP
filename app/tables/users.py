from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey
from app.src.database import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    group_id: Mapped[str | None]
    #group_id: Mapped[str | None] = mapped_column(ForeignKey("groups.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
