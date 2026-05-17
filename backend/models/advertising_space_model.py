# from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Enum, Integer, Numeric, String, Text, func
# from sqlalchemy.orm import relationship

# from backend.database import Base


# class AdvertisingSpace(Base):
#     __tablename__ = "advertising_spaces"

#     id = Column(Integer, primary_key=True, autoincrement=True, index=True)
#     inventory_code = Column(String(50), nullable=False, unique=True, index=True)
#     space_type = Column(
#         Enum("billboard", "led", name="advertising_space_type"),
#         nullable=False,
#         index=True,
#     )
#     city = Column(String(100), nullable=False, default="Харків")
#     address = Column(String(255), nullable=False, index=True)
#     location_description = Column(Text, nullable=True)
#     size = Column(String(50), nullable=False)
#     daily_price = Column(Numeric(10, 2), nullable=False, default=0)
#     monthly_price = Column(Numeric(10, 2), nullable=True)
#     max_led_seconds = Column(Integer, nullable=True)
#     is_active = Column(Boolean, nullable=False, default=True)
#     created_at = Column(DateTime, nullable=False, server_default=func.now())
#     updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

#     #orders = relationship("Order", back_populates="advertising_space")

#     __table_args__ = (
#         CheckConstraint("daily_price >= 0", name="ck_advertising_spaces_daily_price_positive"),
#         CheckConstraint("monthly_price is null or monthly_price >= 0", name="ck_advertising_spaces_monthly_price_positive"),
#         CheckConstraint("max_led_seconds is null or max_led_seconds between 1 and 600", name="ck_advertising_spaces_led_seconds"),
#     )

#     def __repr__(self) -> str:
#         return f"<AdvertisingSpace(id={self.id}, code='{self.inventory_code}', type='{self.space_type}')>"


from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, Numeric, String, Text, func

from backend.database import Base


class AdvertisingSpace(Base):
    __tablename__ = "advertising_spaces"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)

    title = Column(String(120), nullable=False, index=True)
    space_type = Column(
        Enum("billboard", "led", name="advertising_space_type"),
        nullable=False,
        index=True,
    )

    location = Column(String(255), nullable=False)
    size = Column(String(60), nullable=True)

    base_price = Column(Numeric(10, 2), nullable=False, default=0)
    description = Column(Text, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())