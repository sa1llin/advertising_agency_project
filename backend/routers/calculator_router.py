from fastapi import APIRouter, status

from backend.schemas.calculator_schema import (
    BillboardCalculatorRequest,
    BillboardCalculatorResponse,
    LedCalculatorRequest,
    LedCalculatorResponse,
    PrintCalculatorRequest,
    PrintCalculatorResponse,
)
from backend.services.calculator_service import (
    calculate_billboard_price,
    calculate_led_price,
    calculate_print_price,
)


router = APIRouter(
    prefix="/calculator",
    tags=["Calculator"],
)


@router.post(
    "/billboard",
    response_model=BillboardCalculatorResponse,
    status_code=status.HTTP_200_OK,
)
def calculate_billboard(data: BillboardCalculatorRequest):
    total_amount = calculate_billboard_price(data)

    return BillboardCalculatorResponse(
        total_amount=total_amount,
        message="Это ориентировочная стоимость. Точную цену менеджер уточнит при личном звонке или встрече.",
    )


@router.post(
    "/led",
    response_model=LedCalculatorResponse,
    status_code=status.HTTP_200_OK,
)
def calculate_led(data: LedCalculatorRequest):
    total_amount = calculate_led_price(data)

    return LedCalculatorResponse(
        total_amount=total_amount,
        message="Это ориентировочная стоимость размещения на LED-экране. Точную цену менеджер уточнит при личном звонке или встрече.",
    )


@router.post(
    "/print",
    response_model=PrintCalculatorResponse,
    status_code=status.HTTP_200_OK,
)
def calculate_print(data: PrintCalculatorRequest):
    total_amount = calculate_print_price(data)

    return PrintCalculatorResponse(
        total_amount=total_amount,
        message="Это ориентировочная стоимость печатной продукции. Точную цену менеджер уточнит при личном звонке или встрече.",
    )