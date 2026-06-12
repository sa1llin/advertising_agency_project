from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QTextEdit,
    QVBoxLayout,
)

from dialogs.client_form_dialog import CLIENT_FORM_STYLE
from utils.display import (
    application_service_label,
    application_status_label,
    format_datetime,
    format_money,
)


class ApplicationCardDialog(QDialog):
    def __init__(
        self,
        application: dict[str, object],
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(f"Заявка з сайту #{application.get('id', '')}")
        self.setMinimumWidth(560)
        self.setStyleSheet(CLIENT_FORM_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel(self.windowTitle())
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(10)
        fields = [
            (
                "Джерело",
                "Калькулятор сайту"
                if application.get("source") == "calculator"
                else "Форма зворотного зв'язку",
            ),
            ("Ім'я", application.get("full_name") or "—"),
            ("Телефон", application.get("phone") or "—"),
            ("Email", application.get("email") or "—"),
            (
                "Послуга",
                application_service_label(application.get("service_type")),
            ),
            ("Статус", application_status_label(application.get("status"))),
            ("Надіслано", format_datetime(application.get("submitted_at"))),
            (
                "Орієнтовна сума",
                format_money(application.get("estimated_total"))
                if application.get("estimated_total") is not None
                else "—",
            ),
            (
                "Клієнт",
                f"#{application['client_id']}"
                if application.get("client_id")
                else "Не створено",
            ),
            (
                "Замовлення",
                f"#{application['order_id']}"
                if application.get("order_id")
                else "Не створено",
            ),
        ]
        for label, value in fields:
            value_label = QLabel(str(value))
            value_label.setWordWrap(True)
            form.addRow(label, value_label)
        layout.addLayout(form)

        calculation_data = application.get("calculation_data")
        if isinstance(calculation_data, dict):
            calculation = QTextEdit()
            calculation.setReadOnly(True)
            calculation.setPlainText(_calculation_text(calculation_data))
            calculation.setMinimumHeight(150)
            layout.addWidget(QLabel("Дані з калькулятора"))
            layout.addWidget(calculation)

        comment = QTextEdit()
        comment.setReadOnly(True)
        comment.setPlainText(str(application.get("comment") or "Коментар відсутній"))
        comment.setMinimumHeight(120)
        layout.addWidget(QLabel("Коментар клієнта"))
        layout.addWidget(comment)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText("Закрити")
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


def _calculation_text(data: dict[str, object]) -> str:
    service_type = data.get("service_type")
    lines: list[str] = []
    if service_type in ("billboard", "led"):
        lines.extend(
            [
                f"Адреса: {data.get('location') or '—'}",
                f"Розмір: {data.get('size') or '—'}",
                (
                    f"Період: {data.get('period_start') or '—'} — "
                    f"{data.get('period_end') or '—'}"
                ),
                f"Кількість днів: {data.get('days') or '—'}",
            ]
        )
        if service_type == "billboard":
            lines.append(
                "Друк плаката: "
                + ("так" if data.get("need_printing") else "ні")
            )
        else:
            lines.extend(
                [
                    f"Тривалість ролика: {data.get('video_seconds') or '—'} сек",
                    (
                        "Показів на день: "
                        f"{data.get('impressions_per_day') or '—'}"
                    ),
                ]
            )
    elif service_type == "printing":
        lines.extend(
            [
                f"Продукція: {data.get('product_name') or '—'}",
                f"Кількість: {data.get('quantity') or '—'}",
                f"Матеріал: {data.get('material_name') or '—'}",
                f"Розмір: {data.get('size_name') or '—'}",
                f"Кольоровість: {data.get('color_name') or '—'}",
            ]
        )

    rows = data.get("price_rows")
    if isinstance(rows, list) and rows:
        lines.append("")
        lines.append("Складові розрахунку:")
        for row in rows:
            if isinstance(row, dict):
                lines.append(
                    f"• {row.get('label') or 'Позиція'}: "
                    f"{row.get('amount') or 0} грн"
                )
    lines.append("")
    lines.append(f"Орієнтовна сума: {data.get('estimated_total') or 0} грн")
    return "\n".join(lines)
