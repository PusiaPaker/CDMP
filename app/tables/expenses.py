from sqlalchemy.orm import Mapped, mapped_column, validates
from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String, Text

import uuid
from datetime import date
from decimal import Decimal

from app.core import Base
from app.src.utilities import normalize_expense_frequency


class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint(
            "recurrence_type IN ('one_time', 'monthly', 'annual')",
            name="ck_expenses_recurrence_type",
        ),
    )

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)

    expense_name: Mapped[str] = mapped_column(String(150), nullable=False)
    expense_purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)

    # one of: one_time, monthly, annual
    recurrence_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # e.g licensing, consulting, misc
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="unspecified")

    # make sure that they are one of ou expected values
    @validates("recurrence_type")
    def validate_recurrence_type(self, key, value):
        return normalize_expense_frequency(value)
