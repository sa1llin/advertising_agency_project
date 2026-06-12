import json
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.models.advertising_space_model import AdvertisingSpace, PricingItem
from backend.models.order_model import Order
from backend.models.order_segment_model import OrderSegment
from backend.schemas.order_schema import OrderSegmentInput
from backend.services.order_service import calculate_order_amounts


MONEY = Decimal("0.01")


def build_segment(
    db: Session,
    order_type: str,
    data: OrderSegmentInput,
    *,
    sequence: int,
    force_kind: str | None = None,
) -> OrderSegment:
    values = data.model_dump()
    values["sequence"] = sequence
    if force_kind is not None:
        values["segment_kind"] = force_kind

    if order_type == "billboard":
        costs, snapshot = _calculate_billboard(db, data)
    elif order_type == "led":
        costs, snapshot = _calculate_led(db, data)
    elif order_type == "printing":
        costs, snapshot = _calculate_printing(db, data)
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Непідтримуваний тип замовлення.",
        )

    values.update(costs)
    values["pricing_snapshot"] = json.dumps(
        snapshot,
        ensure_ascii=False,
        default=str,
    )
    return OrderSegment(**values)


def recalculate_order(order: Order) -> None:
    subtotal = sum(
        (Decimal(segment.subtotal or 0) for segment in order.segments),
        Decimal("0.00"),
    ).quantize(MONEY, rounding=ROUND_HALF_UP)
    amounts = calculate_order_amounts(
        amount_without_vat=subtotal,
        vat_rate=Decimal(order.vat_rate),
        discount_rate=Decimal(order.discount_rate),
    )
    order.amount_without_vat = subtotal
    order.discount_amount = amounts["discount_amount"]
    order.vat_amount = amounts["vat_amount"]
    order.total_amount = amounts["total_amount"]
    _sync_legacy_fields(order)


def _calculate_billboard(
    db: Session,
    data: OrderSegmentInput,
) -> tuple[dict[str, Decimal], dict[str, object]]:
    space = _space(db, data.advertising_space_id, "billboard")
    days = _days(data)
    rental = _money(Decimal(space.base_price) * days)
    printing = Decimal("0.00")
    print_price = None
    if data.need_printing:
        print_price = _price(db, "billboard_print", str(space.size))
        printing = _money(print_price.amount)

    subtotal = _money(rental + printing)
    return (
        {
            "rental_cost": rental,
            "placement_cost": Decimal("0.00"),
            "printing_cost": printing,
            "materials_cost": Decimal("0.00"),
            "subtotal": subtotal,
        },
        {
            "space_id": space.id,
            "space_location": space.location,
            "space_size": space.size,
            "daily_price": space.base_price,
            "days": days,
            "poster_print_price": print_price.amount if print_price else 0,
        },
    )


def _calculate_led(
    db: Session,
    data: OrderSegmentInput,
) -> tuple[dict[str, Decimal], dict[str, object]]:
    space = _space(db, data.advertising_space_id, "led")
    days = _days(data)
    seconds = int(data.video_seconds or 0)
    impressions = int(data.impressions_per_day or 0)
    placement = _money(
        Decimal(space.base_price) * seconds * impressions * days
    )
    return (
        {
            "rental_cost": Decimal("0.00"),
            "placement_cost": placement,
            "printing_cost": Decimal("0.00"),
            "materials_cost": Decimal("0.00"),
            "subtotal": placement,
        },
        {
            "space_id": space.id,
            "space_location": space.location,
            "space_size": space.size,
            "price_per_second_impression": space.base_price,
            "video_seconds": seconds,
            "impressions_per_day": impressions,
            "days": days,
        },
    )


def _calculate_printing(
    db: Session,
    data: OrderSegmentInput,
) -> tuple[dict[str, Decimal], dict[str, object]]:
    product = _price(db, "print_product", data.product_type)
    material = _price(db, "print_material", data.material_code)
    size_item = _price(db, "print_size", data.size_code)
    color = _price(db, "print_color", data.color_mode)
    quantity = int(data.quantity or 0)

    printing_unit = Decimal(product.amount) + Decimal(color.amount)
    materials_unit = Decimal(material.amount) + Decimal(size_item.amount)
    printing = _money(printing_unit * quantity)
    materials = _money(materials_unit * quantity)
    subtotal = _money(printing + materials)
    return (
        {
            "rental_cost": Decimal("0.00"),
            "placement_cost": Decimal("0.00"),
            "printing_cost": printing,
            "materials_cost": materials,
            "subtotal": subtotal,
        },
        {
            "product": {
                "code": product.code,
                "label": product.label,
                "unit_price": product.amount,
            },
            "material": {
                "code": material.code,
                "label": material.label,
                "unit_price": material.amount,
            },
            "size": {
                "code": size_item.code,
                "label": size_item.label,
                "unit_price": size_item.amount,
            },
            "color": {
                "code": color.code,
                "label": color.label,
                "unit_price": color.amount,
            },
            "quantity": quantity,
        },
    )


def _space(
    db: Session,
    space_id: int | None,
    expected_type: str,
) -> AdvertisingSpace:
    space = (
        db.query(AdvertisingSpace)
        .filter(
            AdvertisingSpace.id == space_id,
            AdvertisingSpace.space_type == expected_type,
            AdvertisingSpace.is_active.is_(True),
        )
        .first()
    )
    if space is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Обрану рекламну площину не знайдено або вона неактивна.",
        )
    return space


def _price(
    db: Session,
    category: str,
    code: str | None,
) -> PricingItem:
    item = (
        db.query(PricingItem)
        .filter(
            PricingItem.category == category,
            PricingItem.code == code,
            PricingItem.is_active.is_(True),
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"У прайс-листі немає активної ціни {category}/{code}.",
        )
    return item


def _days(data: OrderSegmentInput) -> int:
    if data.period_start is None or data.period_end is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Для сегмента потрібно вказати період.",
        )
    return (data.period_end - data.period_start).days + 1


def _money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)


def _sync_legacy_fields(order: Order) -> None:
    dated_segments = [
        segment
        for segment in order.segments
        if segment.period_start is not None and segment.period_end is not None
    ]
    order.rental_start = (
        min(segment.period_start for segment in dated_segments)
        if dated_segments
        else None
    )
    order.rental_end = (
        max(segment.period_end for segment in dated_segments)
        if dated_segments
        else None
    )

    first = order.segments[0] if order.segments else None
    if order.order_type == "printing" and first is not None:
        order.product_name = first.product_name or first.product_type
        order.product_size = first.size_code
        order.material_type = first.material_code
        order.quantity = first.quantity
    else:
        order.product_name = None
        order.product_size = None
        order.material_type = None
        order.quantity = None

    if order.order_type == "led" and first is not None:
        order.led_seconds = first.video_seconds
    else:
        order.led_seconds = None
