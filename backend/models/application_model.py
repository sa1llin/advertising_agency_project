from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class WebsiteApplication(Base):
    __tablename__ = "website_applications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    service_type: Mapped[str] = mapped_column(
        Enum("billboard", "led", "printing", "other", name="application_service_type"),
        nullable=False,
        default="other",
        index=True,
    )
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="contact",
        index=True,
    )
    calculation_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    estimated_total: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        Enum("new", "processed", "rejected", name="application_status"),
        nullable=False,
        default="new",
        index=True,
    )
    client_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("clients.id", ondelete="set null"),
        nullable=True,
        index=True,
    )
    order_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("orders.id", ondelete="set null"),
        nullable=True,
        unique=True,
        index=True,
    )
    processed_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="set null"),
        nullable=True,
        index=True,
    )
    is_hidden: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
