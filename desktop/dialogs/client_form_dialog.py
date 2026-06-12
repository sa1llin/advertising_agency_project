from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from styles import DIALOG_STYLE

CLIENT_FORM_STYLE = DIALOG_STYLE


class ClientFormDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        client: dict[str, object] | None = None,
    ):
        super().__init__(parent)

        self.client = client or {}
        self.setWindowTitle(
            "Редагування клієнта" if client is not None else "Новий клієнт"
        )
        self.setMinimumWidth(620)
        self.setStyleSheet(CLIENT_FORM_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        title = QLabel(self.windowTitle())
        title.setObjectName("dialogTitle")
        hint = QLabel(
            "Поля з позначкою * обов'язкові. Для фізичної особи юридична адреса не обов'язкова."
        )
        hint.setObjectName("dialogHint")
        hint.setWordWrap(True)

        root.addWidget(title)
        root.addWidget(hint)

        form = QFormLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)

        self.client_type = QComboBox()
        self.client_type.addItem("Фізична особа", "individual")
        self.client_type.addItem("ФОП", "fop")
        self.client_type.addItem("Юридична особа", "company")
        self.client_type.currentIndexChanged.connect(self._update_field_requirements)

        self.full_name = QLineEdit()
        self.company_name = QLineEdit()
        self.phone = QLineEdit()
        self.email = QLineEdit()
        self.legal_address = QLineEdit()
        self.tax_number = QLineEdit()
        self.comment = QTextEdit()
        self.comment.setMaximumHeight(100)
        self.is_active = QCheckBox("Активний клієнт")
        self.is_active.setChecked(True)

        self.company_label = QLabel("Назва компанії")
        self.address_label = QLabel("Юридична адреса")

        form.addRow("Тип клієнта *", self.client_type)
        form.addRow("ПІБ / контактна особа *", self.full_name)
        form.addRow(self.company_label, self.company_name)
        form.addRow("Телефон *", self.phone)
        form.addRow("Email", self.email)
        form.addRow(self.address_label, self.legal_address)
        form.addRow("Податковий номер", self.tax_number)
        form.addRow("Коментар", self.comment)
        form.addRow("Статус", self.is_active)
        root.addLayout(form)

        self.validation_label = QLabel()
        self.validation_label.setObjectName("validationError")
        self.validation_label.setWordWrap(True)
        self.validation_label.hide()
        root.addWidget(self.validation_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Зберегти")
        buttons.button(QDialogButtonBox.StandardButton.Save).setObjectName(
            "dialogPrimary"
        )
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Скасувати")
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self._fill_client()
        self._update_field_requirements()

    def get_data(self) -> dict[str, object]:
        return {
            "client_type": self.client_type.currentData(),
            "full_name": self.full_name.text().strip(),
            "company_name": self.company_name.text().strip() or None,
            "phone": self.phone.text().strip(),
            "email": self.email.text().strip() or None,
            "legal_address": self.legal_address.text().strip() or None,
            "tax_number": self.tax_number.text().strip() or None,
            "comment": self.comment.toPlainText().strip() or None,
            "is_active": self.is_active.isChecked(),
        }

    def _fill_client(self) -> None:
        if not self.client:
            return

        client_type = str(self.client.get("client_type") or "individual")
        type_index = self.client_type.findData(client_type)
        self.client_type.setCurrentIndex(max(type_index, 0))
        self.full_name.setText(str(self.client.get("full_name") or ""))
        self.company_name.setText(str(self.client.get("company_name") or ""))
        self.phone.setText(str(self.client.get("phone") or ""))
        self.email.setText(str(self.client.get("email") or ""))
        self.legal_address.setText(str(self.client.get("legal_address") or ""))
        self.tax_number.setText(str(self.client.get("tax_number") or ""))
        self.comment.setPlainText(str(self.client.get("comment") or ""))
        self.is_active.setChecked(bool(self.client.get("is_active", True)))

    def _update_field_requirements(self) -> None:
        is_organization = self.client_type.currentData() in ("fop", "company")
        self.company_label.setText(
            "Назва компанії *" if is_organization else "Назва компанії"
        )
        self.address_label.setText(
            "Юридична адреса *"
            if is_organization
            else "Юридична адреса (необов'язково)"
        )

    def _validate_and_accept(self) -> None:
        data = self.get_data()
        errors: list[str] = []
        self.validation_label.hide()
        fields = (
            self.full_name,
            self.company_name,
            self.phone,
            self.email,
            self.legal_address,
        )
        for field in fields:
            _mark_error(field, False)

        if len(str(data["full_name"])) < 2:
            errors.append("Вкажіть ПІБ або контактну особу.")
            _mark_error(self.full_name, True)
        if len(str(data["phone"])) < 5:
            errors.append("Вкажіть коректний телефон.")
            _mark_error(self.phone, True)

        email = str(data["email"] or "")
        if email and ("@" not in email or "." not in email.rsplit("@", 1)[-1]):
            errors.append("Вкажіть коректний email.")
            _mark_error(self.email, True)

        if data["client_type"] in ("fop", "company"):
            if not data["company_name"]:
                errors.append("Для ФОП або юридичної особи потрібна назва.")
                _mark_error(self.company_name, True)
            if not data["legal_address"]:
                errors.append("Для ФОП або юридичної особи потрібна юридична адреса.")
                _mark_error(self.legal_address, True)

        if errors:
            self.validation_label.setText("\n".join(errors))
            self.validation_label.show()
            return

        self.accept()


def _mark_error(widget: QWidget, enabled: bool) -> None:
    widget.setProperty("error", enabled)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
