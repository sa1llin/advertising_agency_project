from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from styles import DIALOG_STYLE
from utils.display import (
    format_date,
    format_datetime,
    format_money,
    order_status_label,
    order_type_label,
)


class OrderCardDialog(QDialog):
    def __init__(
        self,
        order: dict[str, object],
        client_name: str,
        manager_name: str,
        catalog: dict[str, object] | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Картка замовлення")
        self.setMinimumWidth(680)
        self.setStyleSheet(DIALOG_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        title = QLabel(str(order.get("order_number") or "Замовлення"))
        title.setObjectName("cardTitle")
        root.addWidget(title)

        form = QFormLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(9)
        values = [
            ("Клієнт", client_name),
            ("Менеджер", manager_name),
            ("Тип послуги", order_type_label(order.get("order_type"))),
            ("Статус", order_status_label(order.get("status"))),
            ("Дата замовлення", format_datetime(order.get("order_date"))),
            ("Початок розміщення", format_date(order.get("rental_start"))),
            ("Завершення розміщення", format_date(order.get("rental_end"))),
            ("Назва продукції", order.get("product_name")),
            ("Розмір", order.get("product_size")),
            ("Матеріал", order.get("material_type")),
            ("Кількість", order.get("quantity")),
            ("Тривалість ролика", _seconds(order.get("led_seconds"))),
            ("Тривалість блоку", _seconds(order.get("led_block_seconds"))),
            ("Сума без ПДВ", format_money(order.get("amount_without_vat"))),
            ("Знижка", _percent(order.get("discount_rate"))),
            ("Сума знижки", format_money(order.get("discount_amount"))),
            ("ПДВ", _percent(order.get("vat_rate"))),
            ("Сума ПДВ", format_money(order.get("vat_amount"))),
            ("Разом", format_money(order.get("total_amount"))),
            ("Коментар", order.get("comment")),
            ("Створено", format_datetime(order.get("created_at"))),
            ("Оновлено", format_datetime(order.get("updated_at"))),
        ]
        for label, value in values:
            value_label = QLabel(str(value if value not in (None, "") else "—"))
            value_label.setObjectName("cardValue")
            value_label.setWordWrap(True)
            value_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            form.addRow(label, value_label)
        root.addLayout(form)

        spaces = {
            item.get("id"): item
            for item in (catalog or {}).get("advertising_spaces", [])
            if isinstance(item, dict)
        }
        segments = order.get("segments", [])
        if isinstance(segments, list) and segments:
            segments_title = QLabel("Сегменти та пролонгації")
            segments_title.setObjectName("cardTitle")
            segments_title.setStyleSheet("font-size: 18px;")
            root.addWidget(segments_title)
            for index, segment in enumerate(segments, start=1):
                if not isinstance(segment, dict):
                    continue
                space = spaces.get(segment.get("advertising_space_id"), {})
                kind = (
                    "Пролонгація"
                    if segment.get("segment_kind") == "extension"
                    else "Основний"
                )
                parts = [
                    f"{index}. {kind}",
                    str(space.get("location") or segment.get("product_name") or ""),
                ]
                if segment.get("period_start"):
                    parts.append(
                        f"{format_date(segment.get('period_start'))} - "
                        f"{format_date(segment.get('period_end'))}"
                    )
                if segment.get("video_seconds"):
                    parts.append(
                        f"{segment.get('video_seconds')} с, "
                        f"{segment.get('impressions_per_day')} показів/день"
                    )
                if segment.get("quantity"):
                    parts.append(f"{segment.get('quantity')} шт.")
                parts.append(format_money(segment.get("subtotal")))
                segment_label = QLabel(" | ".join(part for part in parts if part))
                segment_label.setObjectName("cardValue")
                segment_label.setWordWrap(True)
                root.addWidget(segment_label)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText("Закрити")
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)


def _seconds(value: object) -> str:
    return f"{value} с" if value not in (None, "") else "—"


def _percent(value: object) -> str:
    return f"{value} %" if value not in (None, "") else "—"
