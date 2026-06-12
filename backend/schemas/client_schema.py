from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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

    @field_validator(
        "full_name",
        "company_name",
        "phone",
        "email",
        "legal_address",
        "tax_number",
        "comment",
        mode="before",
    )
    @classmethod
    def strip_text_fields(cls, value):
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        return normalized or None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        return value.lower() if value else value


class ClientCreate(ClientBase):
    @model_validator(mode="after")
    def validate_organization_fields(self):
        if self.client_type in ("fop", "company"):
            if not self.company_name:
                raise ValueError("Для ФОП або юридичної особи потрібно вказати назву")
            if not self.legal_address:
                raise ValueError(
                    "Для ФОП або юридичної особи потрібно вказати юридичну адресу"
                )
        return self


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
