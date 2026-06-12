from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from PySide6.QtCore import QMarginsF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QImage,
    QPageLayout,
    QPageSize,
    QPainter,
    QPdfWriter,
    QPen,
)

from utils.display import format_date, order_type_label

MONEY = Decimal("0.01")
TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "assets" / "invoices"
TEMPLATE_NAMES = {
    "billboard": "invoice_billboard.png",
    "led": "invoice_led.png",
    "printing": "invoice_printing.png",
}

SUPPLIER_LINES = [
    "ТОВ «Creative Spark Agency»",
    "ЄДРПОУ: 41234567",
    "ІПН: 412345626543",
    "61002, м. Харків, вул. Сумська, 45",
    "Тел.: +38 (099) 999-11-22",
    "Email: info@creativespark.ua",
    "Р/р UA123456789012345678901234567 в АТ «Ощадбанк»",
    "МФО 300465",
]

PRODUCT_LABELS = {
    "business_card": "Візитки",
    "calendar": "Календарі",
    "flyer": "Флаєри",
    "wristband": "Браслети",
    "mug": "Чашки",
    "other": "Інша продукція",
}
FONT_FILES = [
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("C:/Windows/Fonts/arialbd.ttf"),
]
_FONT_FAMILY: str | None = None


class InvoiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class InvoiceLine:
    description: str
    unit: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal


def invoice_file_name(
    order: dict[str, object], invoice_date: date | None = None
) -> str:
    return f"{invoice_number(order, invoice_date)}.pdf"


def invoice_number(
    order: dict[str, object],
    invoice_date: date | None = None,
) -> str:
    issued_on = invoice_date or date.today()
    raw_number = str(order.get("order_number") or "")
    digits = "".join(character for character in raw_number if character.isdigit())
    if digits:
        suffix = digits[-5:].zfill(5)
    else:
        suffix = str(order.get("id") or 0).zfill(5)
    return f"RF-{issued_on.year}-{suffix}"


def generate_invoice(
    path: str | Path,
    order: dict[str, object],
    client: dict[str, object],
    manager_name: str,
    catalog: dict[str, object],
    *,
    invoice_date: date | None = None,
) -> Path:
    destination = Path(path)
    order_type = str(order.get("order_type") or "")
    template_name = TEMPLATE_NAMES.get(order_type)
    if template_name is None:
        raise InvoiceError("Для цього типу замовлення немає шаблону рахунку.")

    template_path = TEMPLATE_DIR / template_name
    if not template_path.exists():
        raise InvoiceError(f"Не знайдено шаблон рахунку: {template_path}")

    issued_on = invoice_date or date.today()
    image = _render_invoice(
        template_path,
        order,
        client,
        manager_name,
        catalog,
        issued_on,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    suffix = destination.suffix.lower()
    if suffix == ".png":
        if not image.save(str(destination), "PNG"):
            raise InvoiceError("Не вдалося зберегти рахунок у форматі PNG.")
    elif suffix == ".pdf":
        _save_pdf(destination, image, invoice_number(order, issued_on))
    else:
        raise InvoiceError("Рахунок можна зберегти лише у форматі PDF або PNG.")
    return destination


def build_invoice_lines(
    order: dict[str, object],
    catalog: dict[str, object],
) -> list[InvoiceLine]:
    order_type = str(order.get("order_type") or "")
    spaces = {
        item.get("id"): item
        for item in catalog.get("advertising_spaces", [])
        if isinstance(item, dict)
    }
    price_labels = {
        (str(item.get("category") or ""), str(item.get("code") or "")): str(
            item.get("label") or item.get("code") or ""
        )
        for item in catalog.get("pricing_items", [])
        if isinstance(item, dict)
    }
    segments = order.get("segments")
    segment_rows = (
        [segment for segment in segments if isinstance(segment, dict)]
        if isinstance(segments, list)
        else []
    )

    lines: list[InvoiceLine] = []
    for segment in segment_rows:
        amount = _decimal(segment.get("subtotal"))
        if order_type == "printing":
            quantity = _decimal(segment.get("quantity"), Decimal("1"))
            if quantity <= 0:
                quantity = Decimal("1")
            product_code = str(segment.get("product_type") or "")
            product_name = str(
                segment.get("product_name")
                or PRODUCT_LABELS.get(product_code)
                or product_code
                or order.get("product_name")
                or "Друкована продукція"
            )
            details = [
                _catalog_label(
                    price_labels, "print_material", segment.get("material_code")
                ),
                _catalog_label(price_labels, "print_size", segment.get("size_code")),
                _catalog_label(price_labels, "print_color", segment.get("color_mode")),
            ]
            description = product_name
            if any(details):
                description += ": " + ", ".join(item for item in details if item)
            lines.append(
                InvoiceLine(
                    description=description,
                    unit="шт.",
                    quantity=quantity,
                    unit_price=_money(amount / quantity),
                    amount=_money(amount),
                )
            )
            continue

        space = spaces.get(segment.get("advertising_space_id"), {})
        location = str(space.get("location") or "рекламна площина")
        size = str(space.get("size") or "").strip()
        period = _period_text(
            segment.get("period_start"),
            segment.get("period_end"),
        )
        if order_type == "led":
            description = f"Розміщення реклами на LED-екрані"
            if size:
                description += f" {size}"
            description += f", {location}, період {period}"
            if segment.get("video_seconds"):
                description += f", ролик {segment.get('video_seconds')} с"
            if segment.get("impressions_per_day"):
                description += f", {segment.get('impressions_per_day')} показів/день"
        else:
            description = "Розміщення реклами на білборді"
            if size:
                description += f" {size}"
            description += f", {location}, період {period}"
            if segment.get("need_printing"):
                description += ", включно з друком плаката"
        lines.append(
            InvoiceLine(
                description=description,
                unit="послуга",
                quantity=Decimal("1"),
                unit_price=_money(amount),
                amount=_money(amount),
            )
        )

    if lines:
        return lines

    amount = _decimal(order.get("amount_without_vat"))
    quantity = (
        _decimal(order.get("quantity"), Decimal("1"))
        if order_type == "printing"
        else Decimal("1")
    )
    if quantity <= 0:
        quantity = Decimal("1")
    description = str(
        order.get("product_name") or order_type_label(order_type) or "Послуга"
    )
    period = _period_text(order.get("rental_start"), order.get("rental_end"))
    if period != "—":
        description += f", період {period}"
    return [
        InvoiceLine(
            description=description,
            unit="шт." if order_type == "printing" else "послуга",
            quantity=quantity,
            unit_price=_money(amount / quantity),
            amount=_money(amount),
        )
    ]


def amount_in_words(value: object) -> str:
    amount = _decimal(value)
    hryvnias = int(amount)
    kopecks = int((amount - Decimal(hryvnias)) * 100)
    words = _integer_to_words(hryvnias)
    currency = _plural(hryvnias, "гривня", "гривні", "гривень")
    kopeck_word = _plural(kopecks, "копійка", "копійки", "копійок")
    result = f"{words} {currency} {kopecks:02d} {kopeck_word}"
    return result[:1].upper() + result[1:]


def _render_invoice(
    template_path: Path,
    order: dict[str, object],
    client: dict[str, object],
    manager_name: str,
    catalog: dict[str, object],
    issued_on: date,
) -> QImage:
    image = QImage(str(template_path))
    if image.isNull():
        raise InvoiceError(f"Не вдалося відкрити шаблон: {template_path}")
    image = image.convertToFormat(QImage.Format.Format_ARGB32)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    dark = QColor("#0B1D3A")
    orange = QColor("#FF5A00")
    width_scale = image.width() / 1055
    height_scale = image.height() / 1491

    def rect(x: float, y: float, width: float, height: float) -> QRectF:
        return QRectF(
            x * width_scale,
            y * height_scale,
            width * width_scale,
            height * height_scale,
        )

    def draw(
        area: QRectF,
        text: object,
        size: int,
        *,
        bold: bool = False,
        color: QColor = dark,
        alignment: Qt.AlignmentFlag = (
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        ),
        wrap: bool = True,
    ) -> None:
        font = QFont(_font_family())
        font.setPixelSize(max(8, round(size * min(width_scale, height_scale))))
        font.setBold(bold)
        painter.setFont(font)
        painter.setPen(color)
        flags = alignment
        if wrap:
            flags |= Qt.TextFlag.TextWordWrap
        painter.drawText(area, flags, str(text or "—"))

    number = invoice_number(order, issued_on)
    draw(
        rect(625, 112, 360, 34),
        f"№ {number}",
        22,
        bold=True,
        alignment=Qt.AlignmentFlag.AlignRight,
    )
    draw(
        rect(625, 151, 360, 32),
        f"від {issued_on.strftime('%d.%m.%Y')}",
        19,
        bold=True,
        alignment=Qt.AlignmentFlag.AlignRight,
    )

    draw(rect(52, 234, 445, 35), "Постачальник", 20, bold=True)
    draw(rect(566, 234, 430, 35), "Покупець", 20, bold=True)
    draw(rect(52, 292, 447, 285), "\n".join(SUPPLIER_LINES), 15)
    draw(rect(566, 292, 430, 285), "\n".join(_buyer_lines(client)), 15)

    period = _period_text(order.get("rental_start"), order.get("rental_end"))
    meta = [
        ("Номер замовлення:", order.get("order_number") or "—"),
        ("Тип продукції:", order_type_label(order.get("order_type"))),
        ("Період розміщення:", period),
        ("Менеджер:", manager_name),
        ("Статус:", "До оплати"),
    ]
    meta_rects = [
        rect(91, 644, 141, 82),
        rect(313, 644, 105, 82),
        rect(503, 644, 150, 82),
        rect(731, 644, 114, 82),
        rect(922, 644, 76, 82),
    ]
    for area, (label, value) in zip(meta_rects, meta):
        draw(
            QRectF(area.x(), area.y(), area.width(), 25 * height_scale),
            label,
            13,
            bold=True,
        )
        draw(
            QRectF(
                area.x(),
                area.y() + 31 * height_scale,
                area.width(),
                area.height() - 31 * height_scale,
            ),
            value,
            13,
        )

    lines = build_invoice_lines(order, catalog)
    _draw_line_items(painter, image, lines, rect, dark)

    sale_amount = _decimal(order.get("amount_without_vat"))
    vat_amount = _decimal(order.get("vat_amount"))
    discount_amount = _decimal(order.get("discount_amount"))
    total_amount = _decimal(order.get("total_amount"))
    vat_rate = _decimal(order.get("vat_rate"), Decimal("20"))
    discount_rate = _decimal(order.get("discount_rate"))
    totals = [
        ("Сума без ПДВ:", _money_text(sale_amount)),
        (f"ПДВ {_percent_text(vat_rate)}%:", _money_text(vat_amount)),
        (
            f"Знижка {_percent_text(discount_rate)}%:",
            _money_text(discount_amount),
        ),
        ("Усього до сплати:", _money_text(total_amount)),
    ]
    y_positions = [1008, 1032, 1085, 1139]
    for index, ((label, value), y) in enumerate(zip(totals, y_positions)):
        is_total = index == len(totals) - 1
        draw(rect(603, y, 210, 34), label, 17, bold=is_total)
        draw(
            rect(812, y, 185, 34),
            value,
            22 if is_total else 17,
            bold=is_total,
            color=orange if is_total else dark,
            alignment=Qt.AlignmentFlag.AlignRight,
        )

    valid_until = issued_on + timedelta(days=7)
    draw(
        rect(52, 1221, 945, 34),
        f"Сума до сплати: {amount_in_words(total_amount)}.",
        16,
    )
    draw(
        rect(52, 1264, 945, 32),
        f"Рахунок дійсний до: {valid_until.strftime('%d.%m.%Y')}",
        16,
    )
    draw(
        rect(52, 1307, 945, 48),
        (
            "Призначення платежу: Оплата згідно рахунку-фактури "
            f"№ {number} за замовленням {order.get('order_number') or '—'}."
        ),
        15,
    )
    draw(rect(52, 1377, 270, 30), "Виписав:", 16)
    draw(rect(398, 1377, 300, 30), "Керівник:", 16)
    draw(rect(830, 1377, 100, 30), "М.П.", 16)

    painter.end()
    return image


def _draw_line_items(
    painter: QPainter,
    image: QImage,
    lines: list[InvoiceLine],
    rect,
    color: QColor,
) -> None:
    headers = [
        "№",
        "Найменування товару / послуги",
        "Од.",
        "Кількість",
        "Ціна без ПДВ, грн",
        "Сума без ПДВ, грн",
    ]
    columns = [(52, 47), (99, 345), (444, 96), (540, 116), (656, 173), (829, 169)]

    def font(size: int, bold: bool = False) -> QFont:
        result = QFont(_font_family())
        result.setPixelSize(
            max(8, round(size * min(image.width() / 1055, image.height() / 1491)))
        )
        result.setBold(bold)
        return result

    painter.setPen(color)
    painter.setFont(font(13, True))
    for (x, width), header in zip(columns, headers):
        painter.drawText(
            rect(x + 4, 802, width - 8, 44),
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            header,
        )

    visible_lines = lines[:4]
    row_height = 116 / max(1, len(visible_lines))
    body_font_size = 14 if len(visible_lines) == 1 else 11
    for index, line in enumerate(visible_lines):
        top = 849 + index * row_height
        if index:
            painter.setPen(QPen(QColor("#98A5B8"), 1))
            painter.drawLine(
                rect(52, top, 946, 1).topLeft(),
                rect(52, top, 946, 1).topRight(),
            )
        painter.setPen(color)
        painter.setFont(font(body_font_size))
        values = [
            str(index + 1),
            line.description,
            line.unit,
            _quantity_text(line.quantity),
            _money_number(line.unit_price),
            _money_number(line.amount),
        ]
        for column_index, ((x, width), value) in enumerate(zip(columns, values)):
            alignment = Qt.AlignmentFlag.AlignCenter
            if column_index == 1:
                alignment = (
                    Qt.AlignmentFlag.AlignLeft
                    | Qt.AlignmentFlag.AlignVCenter
                    | Qt.TextFlag.TextWordWrap
                )
            painter.drawText(
                rect(x + 7, top + 2, width - 14, row_height - 4),
                alignment,
                value,
            )


def _buyer_lines(client: dict[str, object]) -> list[str]:
    company = str(client.get("company_name") or client.get("full_name") or "Клієнт")
    contact = str(client.get("full_name") or "").strip()
    lines = [company]
    tax_number = str(client.get("tax_number") or "").strip()
    if tax_number:
        lines.append(f"ЄДРПОУ / ІПН: {tax_number}")
    address = str(client.get("legal_address") or "").strip()
    if address:
        lines.append(address)
    if contact and contact.casefold() != company.casefold():
        lines.append(f"Контактна особа: {contact}")
    phone = str(client.get("phone") or "").strip()
    if phone:
        lines.append(f"Тел.: {phone}")
    email = str(client.get("email") or "").strip()
    if email:
        lines.append(f"Email: {email}")
    return lines


def _catalog_label(
    labels: dict[tuple[str, str], str],
    category: str,
    value: object,
) -> str:
    code = str(value or "")
    return labels.get((category, code), code)


def _font_family() -> str:
    global _FONT_FAMILY
    if _FONT_FAMILY is not None:
        return _FONT_FAMILY
    for font_path in FONT_FILES:
        if not font_path.exists():
            continue
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        if font_id < 0:
            continue
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            _FONT_FAMILY = families[0]
            return _FONT_FAMILY
    _FONT_FAMILY = "Segoe UI"
    return _FONT_FAMILY


def _period_text(start: object, end: object) -> str:
    if not start and not end:
        return "—"
    return f"{format_date(start)} – {format_date(end)}"


def _save_pdf(path: Path, image: QImage, title: str) -> None:
    writer = QPdfWriter(str(path))
    writer.setTitle(title)
    writer.setResolution(150)
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    writer.setPageMargins(
        QMarginsF(0, 0, 0, 0),
        QPageLayout.Unit.Millimeter,
    )
    painter = QPainter(writer)
    if not painter.isActive():
        raise InvoiceError("Не вдалося створити PDF рахунку.")
    page_rect = writer.pageLayout().paintRectPixels(writer.resolution())
    painter.drawImage(QRectF(page_rect), image)
    painter.end()
    if not path.exists() or path.stat().st_size == 0:
        raise InvoiceError("PDF рахунку не було створено.")


def _decimal(value: object, fallback: Decimal = Decimal("0")) -> Decimal:
    if value is None:
        return fallback
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return fallback


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def _money_number(value: Decimal) -> str:
    return f"{_money(value):,.2f}".replace(",", " ").replace(".", ",")


def _money_text(value: Decimal) -> str:
    return f"{_money_number(value)} грн"


def _quantity_text(value: Decimal) -> str:
    return str(int(value)) if value == value.to_integral() else str(value.normalize())


def _percent_text(value: Decimal) -> str:
    normalized = _money(value)
    return f"{normalized:.2f}".rstrip("0").rstrip(".")


def _integer_to_words(number: int) -> str:
    if number == 0:
        return "нуль"
    scales = [
        (1_000_000_000, "мільярд", "мільярди", "мільярдів", False),
        (1_000_000, "мільйон", "мільйони", "мільйонів", False),
        (1_000, "тисяча", "тисячі", "тисяч", True),
    ]
    parts: list[str] = []
    remainder = number
    for value, one, few, many, feminine in scales:
        group, remainder = divmod(remainder, value)
        if group:
            parts.extend(_triplet_words(group, feminine))
            parts.append(_plural(group, one, few, many))
    if remainder:
        parts.extend(_triplet_words(remainder, True))
    return " ".join(parts)


def _triplet_words(number: int, feminine: bool) -> list[str]:
    hundreds = [
        "",
        "сто",
        "двісті",
        "триста",
        "чотириста",
        "п'ятсот",
        "шістсот",
        "сімсот",
        "вісімсот",
        "дев'ятсот",
    ]
    tens = [
        "",
        "",
        "двадцять",
        "тридцять",
        "сорок",
        "п'ятдесят",
        "шістдесят",
        "сімдесят",
        "вісімдесят",
        "дев'яносто",
    ]
    teens = [
        "десять",
        "одинадцять",
        "дванадцять",
        "тринадцять",
        "чотирнадцять",
        "п'ятнадцять",
        "шістнадцять",
        "сімнадцять",
        "вісімнадцять",
        "дев'ятнадцять",
    ]
    ones = [
        "",
        "одна" if feminine else "один",
        "дві" if feminine else "два",
        "три",
        "чотири",
        "п'ять",
        "шість",
        "сім",
        "вісім",
        "дев'ять",
    ]
    result: list[str] = []
    hundred, remainder = divmod(number, 100)
    if hundred:
        result.append(hundreds[hundred])
    if 10 <= remainder <= 19:
        result.append(teens[remainder - 10])
        return result
    ten, one = divmod(remainder, 10)
    if ten:
        result.append(tens[ten])
    if one:
        result.append(ones[one])
    return result


def _plural(number: int, one: str, few: str, many: str) -> str:
    last_two = number % 100
    if 11 <= last_two <= 14:
        return many
    last = number % 10
    if last == 1:
        return one
    if 2 <= last <= 4:
        return few
    return many
