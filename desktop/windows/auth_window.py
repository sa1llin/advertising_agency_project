from PySide6.QtCore import QSettings, QThreadPool, Qt
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config import API_BASE_URL, API_TIMEOUT_SECONDS
from data.users import authorize_user
from services.api_client import ApiClient
from services.api_worker import ApiWorker
from styles import AUTH_STYLE
from utils.icons import material_icon
from windows.main_window import MainWindow


class AuthWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.main_window: MainWindow | None = None
        self.api_client = ApiClient(API_BASE_URL, API_TIMEOUT_SECONDS)
        self.thread_pool = QThreadPool.globalInstance()
        self._worker: ApiWorker | None = None
        self._loading = False
        self.settings = QSettings("Creative Spark Agency", "CRM")

        self.setWindowTitle("Creative Spark Agency CRM — Авторизація")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(AUTH_STYLE)

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(520)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(48, 44, 48, 44)
        card_layout.setSpacing(16)

        brand = QLabel("CREATIVE SPARK AGENCY CRM")
        brand.setObjectName("brandLabel")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Авторизація")
        title.setObjectName("authTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Вхід до системи керування замовленнями")
        subtitle.setObjectName("authSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        login_label = QLabel("Логін")
        login_label.setObjectName("fieldLabel")

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Введіть логін")

        password_label = QLabel("Пароль")
        password_label.setObjectName("fieldLabel")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введіть пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_action = self.password_input.addAction(
            material_icon("visibility", "#6F7D95", 20),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        self.password_action.setToolTip("Показати пароль")
        self.password_action.triggered.connect(self.toggle_password_visibility)

        self.error_label = QLabel()
        self.error_label.setObjectName("errorLabel")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        self.login_button = QPushButton("Увійти")
        self.login_button.setObjectName("loginButton")
        self.login_button.clicked.connect(self.authorize)

        card_layout.addWidget(brand)
        card_layout.addSpacing(4)
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(14)
        card_layout.addWidget(login_label)
        card_layout.addWidget(self.login_input)
        card_layout.addWidget(password_label)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(self.error_label)
        card_layout.addSpacing(8)
        card_layout.addWidget(self.login_button)

        root.addWidget(card)

        self.login_input.setText(str(self.settings.value("last_login", "")))
        self.login_input.returnPressed.connect(self.authorize)
        self.password_input.returnPressed.connect(self.authorize)
        if self.login_input.text():
            self.password_input.setFocus()
        else:
            self.login_input.setFocus()

    def authorize(self) -> None:
        if self._loading:
            return

        login = self.login_input.text().strip()
        password = self.password_input.text()
        self._clear_error()
        if not login or not password:
            self._show_auth_error("Введіть логін і пароль.")
            return

        self._set_loading(True)
        self._worker = ApiWorker(
            lambda: authorize_user(self.api_client, login, password)
        )
        self._worker.signals.result.connect(self._open_main_window)
        self._worker.signals.error.connect(self._show_auth_error)
        self._worker.signals.finished.connect(self._finish_authorization)
        self.thread_pool.start(self._worker)

    def _open_main_window(self, session: object) -> None:
        if session is None:
            self._show_auth_error("Невірний логін або пароль.")
            return
        self.settings.setValue("last_login", self.login_input.text().strip())
        self.main_window = MainWindow(session, self.api_client)
        self.main_window.showMaximized()
        self.close()

    def _show_auth_error(self, message: str) -> None:
        text = (
            "Невірний логін або пароль."
            if "401" in message or "авторизац" in message.casefold()
            else message
        )
        self.error_label.setText(text)
        self.error_label.show()
        for field in (self.login_input, self.password_input):
            field.setProperty("error", True)
            self._repolish(field)
        self.password_input.selectAll()
        self.password_input.setFocus()

    def _clear_error(self) -> None:
        self.error_label.hide()
        for field in (self.login_input, self.password_input):
            field.setProperty("error", False)
            self._repolish(field)

    def _set_loading(self, loading: bool) -> None:
        self._loading = loading
        self.login_input.setEnabled(not loading)
        self.password_input.setEnabled(not loading)
        self.login_button.setEnabled(not loading)
        self.login_button.setText("Перевірка..." if loading else "Увійти")
        QApplication.processEvents()

    def _finish_authorization(self) -> None:
        self._worker = None
        if self.isVisible():
            self._set_loading(False)

    def toggle_password_visibility(self) -> None:
        is_hidden = (
            self.password_input.echoMode() == QLineEdit.EchoMode.Password
        )
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Normal
            if is_hidden
            else QLineEdit.EchoMode.Password
        )
        icon_name = "visibility_off" if is_hidden else "visibility"
        self.password_action.setIcon(
            material_icon(icon_name, "#6F7D95", 20)
        )
        self.password_action.setToolTip(
            "Приховати пароль" if is_hidden else "Показати пароль"
        )

    @staticmethod
    def _repolish(widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
