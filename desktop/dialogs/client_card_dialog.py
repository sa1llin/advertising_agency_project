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
from utils.display import client_type_label, format_datetime


class ClientCardDialog(QDialog):
    def __init__(
        self,
        client: dict[str, object],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self.setWindowTitle("Картка клієнта")
        self.setMinimumWidth(620)
        self.setStyleSheet(DIALOG_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        title = QLabel(
            str(client.get("company_name") or client.get("full_name") or "Клієнт")
        )
        title.setObjectName("cardTitle")
        root.addWidget(title)

        form = QFormLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(10)

        values = [
            ("ID", client.get("id")),
            ("Тип", client_type_label(client.get("client_type"))),
            ("ПІБ / контактна особа", client.get("full_name")),
            ("Назва компанії", client.get("company_name")),
            ("Телефон", client.get("phone")),
            ("Email", client.get("email")),
            ("Юридична адреса", client.get("legal_address")),
            ("Податковий номер", client.get("tax_number")),
            ("Статус", "Активний" if client.get("is_active") else "Неактивний"),
            ("Створено", format_datetime(client.get("created_at"))),
            ("Оновлено", format_datetime(client.get("updated_at"))),
            ("Коментар", client.get("comment")),
        ]

        for label, value in values:
            value_label = QLabel(str(value or "—"))
            value_label.setObjectName("cardValue")
            value_label.setWordWrap(True)
            value_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            form.addRow(label, value_label)

        root.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText("Закрити")
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)
