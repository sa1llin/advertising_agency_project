from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


BillboardSize = Literal["3x6", "3x12", "4x8"]

RentalLocation = Literal[
    "center",
    "main_street",
    "residential_area",
]


class BillboardCalculatorRequest(BaseModel):
    billboard_size: BillboardSize = Field(
        description="Размер билборда"
    )

    rental_days: int = Field(
        gt=0,
        le=365,
        description="Срок аренды в днях"
    )

    need_printing: bool = Field(
        default=False,
        description="Нужна ли печать плаката"
    )

    printing_cost: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        description="Стоимость печати плаката"
    )

    rental_location: RentalLocation = Field(
        description="Место аренды, от которого зависит базовая цена за день"
    )

    @model_validator(mode="after")
    def validate_printing_cost(self):
        if self.need_printing and self.printing_cost <= 0:
            raise ValueError("Если печать нужна, укажите стоимость печати больше 0")

        if not self.need_printing:
            self.printing_cost = Decimal("0.00")

        return self


class BillboardCalculatorResponse(BaseModel):
    total_amount: Decimal
    currency: str = "UAH"
    message: str


LedScreenAddress = Literal[
    "soborna_street",
    "central_square",
    "shopping_mall",
]

LedScreenSize = Literal[
    "small",
    "medium",
    "large",
]


class LedCalculatorRequest(BaseModel):
    led_screen_address: LedScreenAddress = Field(
        description="Адрес LED-экрана"
    )

    led_screen_size: LedScreenSize = Field(
        description="Размер LED-экрана"
    )

    video_seconds: int = Field(
        gt=0,
        le=60,
        description="Количество секунд ролика"
    )

    impressions_per_day: int = Field(
        gt=0,
        le=1000,
        description="Количество показов в день"
    )

    placement_start_date: date = Field(
        description="Дата начала размещения"
    )

    placement_end_date: date = Field(
        description="Дата завершения размещения"
    )

    @model_validator(mode="after")
    def validate_placement_period(self):
        if self.placement_end_date < self.placement_start_date:
            raise ValueError("Дата завершения не может быть раньше даты начала")

        return self


class LedCalculatorResponse(BaseModel):
    total_amount: Decimal
    currency: str = "UAH"
    message: str
    
PrintedProductType = Literal[
    "business_card",
    "flyer",
    "poster",
    "calendar",
    "mug",
]

PrintedMaterial = Literal[
    "glossy_paper",
    "matte_paper",
    "cardboard",
    "vinyl",
    "ceramic",
]

PrintedSize = Literal[
    "small",
    "medium",
    "large",
]

PrintedColorMode = Literal[
    "black_white",
    "one_side_color",
    "full_color",
]


class PrintCalculatorRequest(BaseModel):
    product_type: PrintedProductType = Field(
        description="Тип печатной продукции"
    )

    quantity: int = Field(
        gt=0,
        le=100000,
        description="Количество единиц продукции"
    )

    material: PrintedMaterial = Field(
        description="Материал"
    )

    size: PrintedSize = Field(
        description="Размер продукции"
    )

    color_mode: PrintedColorMode = Field(
        description="Цветность"
    )


class PrintCalculatorResponse(BaseModel):
    total_amount: Decimal
    currency: str = "UAH"
    message: str