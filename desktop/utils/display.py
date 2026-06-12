from datetime import date, datetime
from decimal import Decimal, InvalidOperation

ORDER_TYPE_LABELS = {
    "billboard": "Білборд",
    "led": "LED",
    "printing": "Друк",
}

ORDER_STATUS_LABELS = {
    "new": "Нове",
    "in_progress": "У роботі",
    "paused": "Призупинено",
    "completed": "Завершено",
    "cancelled": "Скасовано",
}

CLIENT_TYPE_LABELS = {
    "individual": "Фізична особа",
    "fop": "ФОП",
    "company": "Юридична особа",
}

APPLICATION_STATUS_LABELS = {
    "new": "Нова",
    "processed": "Оброблена",
    "rejected": "Відхилена",
}

APPLICATION_SERVICE_LABELS = {
    "billboard": "Білборд",
    "led": "LED-екран",
    "printing": "Друкована продукція",
    "other": "Інша послуга",
}


def display_client_name(client: dict[str, object]) -> str:
    company_name = str(client.get("company_name") or "").strip()
    full_name = str(client.get("full_name") or "").strip()
    return company_name or full_name or f"Клієнт #{client.get('id', '?')}"


def build_client_names(clients: list[dict[str, object]]) -> dict[int, str]:
    result: dict[int, str] = {}
    for client in clients:
        client_id = client.get("id")
        if isinstance(client_id, int):
            result[client_id] = display_client_name(client)
    return result


def client_type_label(value: object) -> str:
    raw_value = str(value or "")
    return CLIENT_TYPE_LABELS.get(raw_value, raw_value or "—")


def order_type_label(value: object) -> str:
    raw_value = str(value or "")
    return ORDER_TYPE_LABELS.get(raw_value, raw_value or "—")


def order_status_label(value: object) -> str:
    raw_value = str(value or "")
    return ORDER_STATUS_LABELS.get(raw_value, raw_value or "—")


def application_status_label(value: object) -> str:
    raw_value = str(value or "")
    return APPLICATION_STATUS_LABELS.get(raw_value, raw_value or "—")


def application_service_label(value: object) -> str:
    raw_value = str(value or "")
    return APPLICATION_SERVICE_LABELS.get(raw_value, raw_value or "—")


def format_datetime(value: object) -> str:
    parsed = _parse_datetime(value)
    return parsed.strftime("%d.%m.%Y %H:%M") if parsed is not None else "—"


def format_date(value: object) -> str:
    parsed = _parse_date(value)
    return parsed.strftime("%d.%m.%Y") if parsed is not None else "—"


def format_period(start: object, end: object, fallback: object = None) -> str:
    start_text = format_date(start)
    end_text = format_date(end)
    if start_text != "—" or end_text != "—":
        return f"{start_text} — {end_text}"
    return format_date(fallback)


def format_money(value: object) -> str:
    try:
        amount = Decimal(str(value or "0"))
    except InvalidOperation:
        return "—"
    return f"{amount:,.2f} грн".replace(",", " ")


def manager_label(value: object) -> str:
    return f"Менеджер #{value}" if isinstance(value, int) else "Не призначено"


def _parse_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_date(value: object) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None
