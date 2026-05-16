from sqlalchemy import CheckConstraint, Column, Date, DateTime, Enum, Integer, Numeric, String, Text, func

from backend.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String(150), nullable=False, index=True)
    category = Column(
        Enum("materials", "rent", "salary", "utilities", "maintenance", "other", name="expense_category"),
        nullable=False,
        default="other",
        index=True,
    )
    expense_date = Column(Date, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_expenses_amount_positive"),
    )

    def __repr__(self) -> str:
        return f"<Expense(id={self.id}, title='{self.title}', amount='{self.amount}')>"
