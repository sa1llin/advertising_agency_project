from sqlalchemy import CheckConstraint, Column, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import relationship

from backend.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    order_number = Column(String(30), nullable=False, unique=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="restrict"), nullable=False, index=True)
    manager_id = Column(Integer, ForeignKey("users.id", ondelete="restrict"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="restrict"), nullable=False, index=True)
    advertising_space_id = Column(Integer, ForeignKey("advertising_spaces.id", ondelete="set null"), nullable=True, index=True)

    order_type = Column(
        Enum("billboard", "led", "printing", name="order_type"),
        nullable=False,
        index=True,
    )
    status = Column(
        Enum("new", "in_progress", "paused", "completed", "cancelled", name="order_status"),
        nullable=False,
        default="new",
        index=True,
    )

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    rental_start = Column(Date, nullable=True)
    rental_end = Column(Date, nullable=True)

    product_name = Column(String(120), nullable=True)
    product_size = Column(String(60), nullable=True)
    material_type = Column(String(120), nullable=True)
    quantity = Column(Integer, nullable=True)

    led_seconds = Column(Integer, nullable=True)
    led_block_seconds = Column(Integer, nullable=True, default=600)

    vat_rate = Column(Numeric(5, 2), nullable=False, default=20)
    discount_rate = Column(Numeric(5, 2), nullable=False, default=0)
    amount_without_vat = Column(Numeric(10, 2), nullable=False, default=0)
    vat_amount = Column(Numeric(10, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)

    comment = Column(Text, nullable=True)

    client = relationship("Client", back_populates="orders")
    manager = relationship("User", back_populates="orders")
    service = relationship("Service", back_populates="orders")
    advertising_space = relationship("AdvertisingSpace", back_populates="orders")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("rental_start is null or rental_end is null or rental_end >= rental_start", name="ck_orders_rental_period"),
        CheckConstraint("quantity is null or quantity > 0", name="ck_orders_quantity_positive"),
        CheckConstraint("led_seconds is null or led_seconds between 1 and 600", name="ck_orders_led_seconds"),
        CheckConstraint("led_block_seconds is null or led_block_seconds between 1 and 600", name="ck_orders_led_block_seconds"),
        CheckConstraint("vat_rate >= 0 and vat_rate <= 100", name="ck_orders_vat_rate"),
        CheckConstraint("discount_rate >= 0 and discount_rate <= 100", name="ck_orders_discount_rate"),
        CheckConstraint("amount_without_vat >= 0", name="ck_orders_amount_without_vat_positive"),
        CheckConstraint("vat_amount >= 0", name="ck_orders_vat_amount_positive"),
        CheckConstraint("discount_amount >= 0", name="ck_orders_discount_amount_positive"),
        CheckConstraint("total_amount >= 0", name="ck_orders_total_amount_positive"),
    )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, number='{self.order_number}', status='{self.status}')>"
