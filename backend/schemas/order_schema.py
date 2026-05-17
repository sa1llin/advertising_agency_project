from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


OrderType = Literal["billboard", "led", "printing"]
OrderStatus = Literal["new", "in_progress", "paused", "completed", "cancelled"]


class OrderBase(BaseModel):
    client_id: int = Field(gt=0)
    manager_id: int | None = Field(default=None, gt=0)
    service_id: int | None = Field(default=None, gt=0)

    order_type: OrderType
    status: OrderStatus = "new"

    rental_start: date | None = None
    rental_end: date | None = None

    product_name: str | None = Field(default=None, max_length=120)
    product_size: str | None = Field(default=None, max_length=60)
    material_type: str | None = Field(default=None, max_length=120)

    quantity: int | None = Field(default=None, gt=0)

    led_seconds: int | None = Field(default=None, ge=1, le=600)
    led_block_seconds: int | None = Field(default=600, ge=1, le=600)

    vat_rate: Decimal = Field(default=Decimal("20.00"), ge=0, le=100)
    discount_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    amount_without_vat: Decimal = Field(default=Decimal("0.00"), ge=0)

    comment: str | None = None

    @model_validator(mode="after")
    def validate_order_details(self):
        if self.order_type in ("billboard", "led"):
            if self.rental_start is None or self.rental_end is None:
                raise ValueError("Для billboard и led нужно указать rental_start и rental_end")

            if self.rental_end < self.rental_start:
                raise ValueError("Дата окончания аренды не может быть раньше даты начала")

        if self.order_type == "led" and self.led_seconds is None:
            raise ValueError("Для led-заказа нужно указать led_seconds")

        if self.order_type == "printing":
            if not self.product_name:
                raise ValueError("Для printing-заказа нужно указать product_name")

            if self.quantity is None:
                raise ValueError("Для printing-заказа нужно указать quantity")

        return self


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    client_id: int | None = Field(default=None, gt=0)
    manager_id: int | None = Field(default=None, gt=0)
    service_id: int | None = Field(default=None, gt=0)

    status: OrderStatus | None = None

    rental_start: date | None = None
    rental_end: date | None = None

    product_name: str | None = Field(default=None, max_length=120)
    product_size: str | None = Field(default=None, max_length=60)
    material_type: str | None = Field(default=None, max_length=120)

    quantity: int | None = Field(default=None, gt=0)

    led_seconds: int | None = Field(default=None, ge=1, le=600)
    led_block_seconds: int | None = Field(default=None, ge=1, le=600)

    vat_rate: Decimal | None = Field(default=None, ge=0, le=100)
    discount_rate: Decimal | None = Field(default=None, ge=0, le=100)
    amount_without_vat: Decimal | None = Field(default=None, ge=0)

    comment: str | None = None


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str

    client_id: int
    manager_id: int | None
    service_id: int | None

    order_type: str
    status: str

    order_date: datetime

    rental_start: date | None
    rental_end: date | None

    product_name: str | None
    product_size: str | None
    material_type: str | None

    quantity: int | None

    led_seconds: int | None
    led_block_seconds: int | None

    vat_rate: Decimal
    discount_rate: Decimal

    amount_without_vat: Decimal
    vat_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal

    comment: str | None

    created_at: datetime
    updated_at: datetime