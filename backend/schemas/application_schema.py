from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


ApplicationServiceType = Literal["billboard", "led", "printing", "other"]
ApplicationStatus = Literal["new", "processed", "rejected"]
ApplicationSource = Literal["contact", "calculator"]


class CalculationRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1, max_length=200)
    amount: Decimal = Field(ge=0)


class BillboardCalculation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_type: Literal["billboard"]
    advertising_space_id: int = Field(gt=0)
    location: str = Field(min_length=1, max_length=255)
    size: str | None = Field(default=None, max_length=60)
    period_start: date
    period_end: date
    days: int = Field(gt=0)
    need_printing: bool = False
    estimated_total: Decimal = Field(ge=0)
    price_rows: list[CalculationRow] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_period(self):
        if self.period_end < self.period_start:
            raise ValueError("Дата завершення не може бути раніше дати початку")
        expected_days = (self.period_end - self.period_start).days + 1
        if self.days != expected_days:
            raise ValueError("Кількість днів не відповідає обраному періоду")
        return self


class LedCalculation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_type: Literal["led"]
    advertising_space_id: int = Field(gt=0)
    location: str = Field(min_length=1, max_length=255)
    size: str | None = Field(default=None, max_length=60)
    period_start: date
    period_end: date
    days: int = Field(gt=0)
    video_seconds: int = Field(ge=1, le=600)
    impressions_per_day: int = Field(gt=0, le=100_000)
    estimated_total: Decimal = Field(ge=0)
    price_rows: list[CalculationRow] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_period(self):
        if self.period_end < self.period_start:
            raise ValueError("Дата завершення не може бути раніше дати початку")
        expected_days = (self.period_end - self.period_start).days + 1
        if self.days != expected_days:
            raise ValueError("Кількість днів не відповідає обраному періоду")
        return self


class PrintingCalculation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_type: Literal["printing"]
    product_type: str = Field(min_length=1, max_length=60)
    product_name: str = Field(min_length=1, max_length=120)
    material_code: str = Field(min_length=1, max_length=60)
    material_name: str = Field(min_length=1, max_length=120)
    size_code: str = Field(min_length=1, max_length=60)
    size_name: str = Field(min_length=1, max_length=120)
    color_mode: str = Field(min_length=1, max_length=60)
    color_name: str = Field(min_length=1, max_length=120)
    quantity: int = Field(gt=0, le=1_000_000)
    estimated_total: Decimal = Field(ge=0)
    price_rows: list[CalculationRow] = Field(default_factory=list)


CalculationData = BillboardCalculation | LedCalculation | PrintingCalculation


class ApplicationCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    phone: str = Field(min_length=5, max_length=30)
    email: str = Field(min_length=5, max_length=120)
    service_type: ApplicationServiceType = "other"
    comment: str | None = Field(default=None, max_length=5000)
    source: ApplicationSource = "contact"
    calculation_data: CalculationData | None = Field(
        default=None,
        discriminator="service_type",
    )
    estimated_total: Decimal | None = Field(default=None, ge=0)

    @field_validator("full_name", "phone", "email", "comment", mode="before")
    @classmethod
    def strip_text(cls, value):
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        return normalized or None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("Вкажіть коректну email-адресу")
        return value.casefold()

    @model_validator(mode="after")
    def validate_source_and_calculation(self):
        if self.source == "contact":
            self.calculation_data = None
            self.estimated_total = None
            return self

        if self.calculation_data is None:
            raise ValueError("Для заявки з калькулятора потрібні дані розрахунку")
        if self.service_type != self.calculation_data.service_type:
            raise ValueError("Тип послуги не відповідає вибраному калькулятору")
        self.estimated_total = self.calculation_data.estimated_total
        return self


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


class ApplicationVisibilityUpdate(BaseModel):
    is_hidden: bool = True


class ApplicationOrderLink(BaseModel):
    order_id: int = Field(gt=0)


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    phone: str
    email: str
    service_type: str
    comment: str | None
    source: str
    calculation_data: dict[str, object] | None
    estimated_total: Decimal | None
    status: str
    client_id: int | None
    order_id: int | None
    processed_by: int | None
    is_hidden: bool
    submitted_at: datetime
    processed_at: datetime | None
