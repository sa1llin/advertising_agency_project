from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from backend.database import Base


class OrderSegment(Base):
    __tablename__ = "order_segments"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="cascade"),
        nullable=False,
        index=True,
    )
    sequence = Column(Integer, nullable=False, default=1)
    segment_kind = Column(
        Enum("initial", "extension", name="order_segment_kind"),
        nullable=False,
        default="initial",
        index=True,
    )
    advertising_space_id = Column(
        Integer,
        ForeignKey("advertising_spaces.id", ondelete="restrict"),
        nullable=True,
        index=True,
    )

    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    need_printing = Column(Boolean, nullable=False, default=False)

    video_seconds = Column(Integer, nullable=True)
    impressions_per_day = Column(Integer, nullable=True)

    product_type = Column(String(60), nullable=True)
    product_name = Column(String(120), nullable=True)
    material_code = Column(String(60), nullable=True)
    size_code = Column(String(60), nullable=True)
    color_mode = Column(String(60), nullable=True)
    quantity = Column(Integer, nullable=True)

    rental_cost = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    placement_cost = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    printing_cost = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    materials_cost = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    subtotal = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    pricing_snapshot = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    order = relationship("Order", back_populates="segments")
    advertising_space = relationship(
        "AdvertisingSpace",
        back_populates="order_segments",
    )
