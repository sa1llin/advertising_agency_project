from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class AdvertisingSpaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    space_type: str
    location: str
    size: str | None
    base_price: Decimal
    description: str | None
    is_active: bool


class PricingItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    code: str
    label: str
    amount: Decimal
    unit_name: str
    description: str | None
    is_active: bool


class OrderCatalogResponse(BaseModel):
    advertising_spaces: list[AdvertisingSpaceResponse]
    pricing_items: list[PricingItemResponse]
    loaded_at: datetime
