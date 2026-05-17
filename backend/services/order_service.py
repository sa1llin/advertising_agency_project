from decimal import Decimal, ROUND_HALF_UP


def calculate_order_amounts(
    amount_without_vat: Decimal,
    vat_rate: Decimal,
    discount_rate: Decimal,
) -> dict[str, Decimal]:
    amount_without_vat = Decimal(amount_without_vat)
    vat_rate = Decimal(vat_rate)
    discount_rate = Decimal(discount_rate)

    discount_amount = amount_without_vat * discount_rate / Decimal("100")
    amount_after_discount = amount_without_vat - discount_amount
    vat_amount = amount_after_discount * vat_rate / Decimal("100")
    total_amount = amount_after_discount + vat_amount

    return {
        "discount_amount": discount_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "vat_amount": vat_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "total_amount": total_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
    }


def generate_order_number(order_id: int) -> str:
    return f"ORD-{order_id:05d}"