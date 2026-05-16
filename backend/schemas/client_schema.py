from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ClientType = Literal["individual", "fop", "company"]


class ClientBase(BaseModel):
    client_type: ClientType = "individual"
    full_name: str = Field(..., min_length=2, max_length=150)
    company_name: str | None = Field(default=None, max_length=150)
    phone: str = Field(..., min_length=5, max_length=30)
    email: str | None = Field(default=None, max_length=120)
    legal_address: str | None = Field(default=None, max_length=255)
    tax_number: str | None = Field(default=None, max_length=50)
    comment: str | None = None
    is_active: bool = True


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    client_type: ClientType | None = None
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    company_name: str | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, min_length=5, max_length=30)
    email: str | None = Field(default=None, max_length=120)
    legal_address: str | None = Field(default=None, max_length=255)
    tax_number: str | None = Field(default=None, max_length=50)
    comment: str | None = None
    is_active: bool | None = None


class ClientResponse(ClientBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)