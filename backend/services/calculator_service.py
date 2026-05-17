from decimal import Decimal, ROUND_HALF_UP

from backend.schemas.calculator_schema import (
    BillboardCalculatorRequest,
    LedCalculatorRequest,
    PrintCalculatorRequest,
)

BASE_DAILY_PRICE_BY_LOCATION = {
    "center": Decimal("850.00"),
    "main_street": Decimal("650.00"),
    "residential_area": Decimal("450.00"),
}


SIZE_COEFFICIENTS = {
    "3x6": Decimal("1.00"),
    "3x12": Decimal("1.60"),
    "4x8": Decimal("1.35"),
}


def calculate_billboard_price(data: BillboardCalculatorRequest) -> Decimal:
    base_daily_price = BASE_DAILY_PRICE_BY_LOCATION[data.rental_location]
    size_coefficient = SIZE_COEFFICIENTS[data.billboard_size]

    rental_price = base_daily_price * size_coefficient * data.rental_days
    printing_price = data.printing_cost if data.need_printing else Decimal("0.00")

    total_amount = rental_price + printing_price

    return total_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


LED_BASE_PRICE_PER_SECOND = {
    "soborna_street": Decimal("0.80"),
    "central_square": Decimal("1.20"),
    "shopping_mall": Decimal("1.00"),
}


LED_SIZE_COEFFICIENTS = {
    "small": Decimal("1.00"),
    "medium": Decimal("1.35"),
    "large": Decimal("1.70"),
}


def calculate_led_price(data: LedCalculatorRequest) -> Decimal:
    base_price_per_second = LED_BASE_PRICE_PER_SECOND[data.led_screen_address]
    size_coefficient = LED_SIZE_COEFFICIENTS[data.led_screen_size]

    placement_days = (
        data.placement_end_date - data.placement_start_date
    ).days + 1

    total_amount = (
        base_price_per_second
        * data.video_seconds
        * data.impressions_per_day
        * placement_days
        * size_coefficient
    )

    return total_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


PRINT_BASE_PRICE_BY_PRODUCT = {
    "business_card": Decimal("2.50"),
    "flyer": Decimal("6.00"),
    "poster": Decimal("45.00"),
    "calendar": Decimal("80.00"),
    "mug": Decimal("120.00"),
}


PRINT_MATERIAL_COEFFICIENTS = {
    "glossy_paper": Decimal("1.10"),
    "matte_paper": Decimal("1.00"),
    "cardboard": Decimal("1.25"),
    "vinyl": Decimal("1.50"),
    "ceramic": Decimal("1.70"),
}


PRINT_SIZE_COEFFICIENTS = {
    "small": Decimal("1.00"),
    "medium": Decimal("1.35"),
    "large": Decimal("1.70"),
}


PRINT_COLOR_COEFFICIENTS = {
    "black_white": Decimal("1.00"),
    "one_side_color": Decimal("1.25"),
    "full_color": Decimal("1.60"),
}


def calculate_print_price(data: PrintCalculatorRequest) -> Decimal:
    base_price = PRINT_BASE_PRICE_BY_PRODUCT[data.product_type]
    material_coefficient = PRINT_MATERIAL_COEFFICIENTS[data.material]
    size_coefficient = PRINT_SIZE_COEFFICIENTS[data.size]
    color_coefficient = PRINT_COLOR_COEFFICIENTS[data.color_mode]

    total_amount = (
        base_price
        * data.quantity
        * material_coefficient
        * size_coefficient
        * color_coefficient
    )

    return total_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
