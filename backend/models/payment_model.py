from sqlalchemy import CheckConstraint, Column, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import relationship

from backend.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    payment_number = Column(String(30), nullable=False, unique=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="cascade"), nullable=False, index=True)
    payment_date = Column(DateTime, nullable=False, server_default=func.now())
    amount = Column(Numeric(10, 2), nullable=False)
    method = Column(
        Enum("cash", "card", "bank_transfer", name="payment_method"),
        nullable=False,
        default="bank_transfer",
    )
    status = Column(
        Enum("unpaid", "partial", "paid", "refunded", name="payment_status"),
        nullable=False,
        default="unpaid",
        index=True,
    )
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    order = relationship("Order", back_populates="payments")

    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_payments_amount_positive"),
    )

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, number='{self.payment_number}', status='{self.status}')>"
