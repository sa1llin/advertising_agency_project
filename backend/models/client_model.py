from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import relationship

from backend.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    client_type = Column(
        Enum("individual", "fop", "company", name="client_type"),
        nullable=False,
        default="individual",
    )
    full_name = Column(String(150), nullable=False, index=True)
    company_name = Column(String(150), nullable=True, index=True)
    phone = Column(String(30), nullable=False, index=True)
    email = Column(String(120), nullable=True, index=True)
    legal_address = Column(String(255), nullable=True)
    tax_number = Column(String(50), nullable=True)
    comment = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    orders = relationship("Order", back_populates="client", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Client(id={self.id}, full_name='{self.full_name}')>"
