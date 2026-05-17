from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)

    order_number: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        unique=True,
        index=True,
    )

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="restrict"),
        nullable=False,
        index=True,
    )

    manager_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="set null"),
        nullable=True,
        index=True,
    )

    service_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("services.id", ondelete="set null"),
        nullable=True,
        index=True,
    )

    order_type: Mapped[str] = mapped_column(
        Enum("billboard", "led", "printing", name="order_type"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        Enum("new", "in_progress", "paused", "completed", "cancelled", name="order_status"),
        nullable=False,
        default="new",
        index=True,
    )

    order_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    rental_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    rental_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    product_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    product_size: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    material_type: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    quantity: Mapped[Optional[int]] = mapped_column(nullable=True)

    led_seconds: Mapped[Optional[int]] = mapped_column(nullable=True)
    led_block_seconds: Mapped[Optional[int]] = mapped_column(nullable=True, default=600)

    vat_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("20.00"),
    )

    discount_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    amount_without_vat: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    vat_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    client = relationship("Client", back_populates="orders")
    manager = relationship("User", back_populates="orders")
    service = relationship("Service", back_populates="orders")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "rental_start is null or rental_end is null or rental_end >= rental_start",
            name="ck_orders_rental_period",
        ),
        CheckConstraint(
            "quantity is null or quantity > 0",
            name="ck_orders_quantity_positive",
        ),
        CheckConstraint(
            "led_seconds is null or led_seconds between 1 and 600",
            name="ck_orders_led_seconds",
        ),
        CheckConstraint(
            "led_block_seconds is null or led_block_seconds between 1 and 600",
            name="ck_orders_led_block_seconds",
        ),
        CheckConstraint(
            "vat_rate >= 0 and vat_rate <= 100",
            name="ck_orders_vat_rate",
        ),
        CheckConstraint(
            "discount_rate >= 0 and discount_rate <= 100",
            name="ck_orders_discount_rate",
        ),
        CheckConstraint(
            "amount_without_vat >= 0",
            name="ck_orders_amount_without_vat_positive",
        ),
        CheckConstraint(
            "vat_amount >= 0",
            name="ck_orders_vat_amount_positive",
        ),
        CheckConstraint(
            "discount_amount >= 0",
            name="ck_orders_discount_amount_positive",
        ),
        CheckConstraint(
            "total_amount >= 0",
            name="ck_orders_total_amount_positive",
        ),
    )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, order_number='{self.order_number}')>"