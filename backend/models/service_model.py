from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, Numeric, String, Text, func
from sqlalchemy.orm import relationship

from backend.database import Base


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(120), nullable=False, unique=True, index=True)
    service_type = Column(
        Enum("billboard", "led", "printing", name="service_type"),
        nullable=False,
        index=True,
    )
    unit_name = Column(String(50), nullable=False, default="unit")
    base_price = Column(Numeric(10, 2), nullable=False, default=0)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    orders = relationship("Order", back_populates="service")

    def __repr__(self) -> str:
        return f"<Service(id={self.id}, name='{self.name}', type='{self.service_type}')>"
