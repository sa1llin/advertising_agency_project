from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from dialogs.client_form_dialog import CLIENT_FORM_STYLE


class UserFormDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        user: dict[str, object] | None = None,
    ):
        super().__init__(parent)
        self.user = user or {}
        self.is_editing = user is not None

        self.setWindowTitle(
            "Редагування працівника" if self.is_editing else "Новий працівник"
        )
        self.setMinimumWidth(560)
        self.setStyleSheet(CLIENT_FORM_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        title = QLabel(self.windowTitle())
        title.setObjectName("dialogTitle")
        hint = QLabel(
            "Пароль має містити щонайменше 8 символів. "
            "Під час редагування залиште поле порожнім, щоб не змінювати пароль."
        )
        hint.setObjectName("dialogHint")
        hint.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(hint)

        form = QFormLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)

        self.username = QLineEdit()
        self.full_name = QLineEdit()
        self.role = QComboBox()
        self.role.addItem("Менеджер", "manager")
        self.role.addItem("Адміністратор", "admin")
        self.email = QLineEdit()
        self.phone = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.is_active = QCheckBox("Активний обліковий запис")
        self.is_active.setChecked(True)

        form.addRow("Логін *", self.username)
        form.addRow("ПІБ *", self.full_name)
        form.addRow("Роль *", self.role)
        form.addRow("Email", self.email)
        form.addRow("Телефон", self.phone)
        form.addRow("Пароль" + ("" if self.is_editing else " *"), self.password)
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

        self._fill_user()

    def _fill_user(self) -> None:
        if not self.user:
            return
        self.username.setText(str(self.user.get("username") or ""))
        self.username.setEnabled(False)
        self.full_name.setText(str(self.user.get("full_name") or ""))
        role_index = self.role.findData(self.user.get("role"))
        self.role.setCurrentIndex(max(role_index, 0))
        self.email.setText(str(self.user.get("email") or ""))
        self.phone.setText(str(self.user.get("phone") or ""))
        self.is_active.setChecked(bool(self.user.get("is_active", True)))

    def get_data(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "role": self.role.currentData(),
            "full_name": self.full_name.text().strip(),
            "email": self.email.text().strip() or None,
            "phone": self.phone.text().strip() or None,
            "is_active": self.is_active.isChecked(),
        }
        password = self.password.text()
        if password:
            payload["password"] = password
        if not self.is_editing:
            payload["username"] = self.username.text().strip()
        return payload

    def _validate_and_accept(self) -> None:
        username = self.username.text().strip()
        full_name = self.full_name.text().strip()
        password = self.password.text()
        errors: list[str] = []
        self.validation_label.hide()
        for field in (
            self.username,
            self.full_name,
            self.email,
            self.password,
        ):
            _mark_error(field, False)

        if len(username) < 2:
            errors.append("Вкажіть логін працівника.")
            _mark_error(self.username, True)
        if any(not (char.isalnum() or char in "_.-") for char in username):
            errors.append("Логін може містити лише літери, цифри, _, . та -.")
            _mark_error(self.username, True)
        if len(full_name) < 2:
            errors.append("Вкажіть ПІБ працівника.")
            _mark_error(self.full_name, True)
        if not self.is_editing and len(password) < 8:
            errors.append("Пароль має містити щонайменше 8 символів.")
            _mark_error(self.password, True)
        if self.is_editing and password and len(password) < 8:
            errors.append("Новий пароль має містити щонайменше 8 символів.")
            _mark_error(self.password, True)

        email = self.email.text().strip()
        if email and ("@" not in email or "." not in email.rsplit("@", 1)[-1]):
            errors.append("Вкажіть коректний email.")
            _mark_error(self.email, True)

        if errors:
            self.validation_label.setText("\n".join(errors))
            self.validation_label.show()
            return
        self.accept()


def _mark_error(widget: QWidget, enabled: bool) -> None:
    widget.setProperty("error", enabled)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
