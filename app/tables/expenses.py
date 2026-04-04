from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Date, ForeignKey, Numeric, String, Text

import uuid
from datetime import date
from decimal import Decimal

from app.core import Base


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)

    expense_name: Mapped[str] = mapped_column(String(150), nullable=False)
    expense_purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)

    # one of: one_time, monthly, annual
    recurrence_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # e.g licensing fee, consulting, misc
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="unspecified")
