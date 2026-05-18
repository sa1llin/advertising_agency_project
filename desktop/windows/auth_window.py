from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from data.users import authorize_user
from styles import AUTH_STYLE
from windows.main_window import MainWindow


class AuthWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.main_window: MainWindow | None = None

        self.setWindowTitle("Creative Spark Agency CRM — Авторизація")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(AUTH_STYLE)

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(460)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(42, 42, 42, 42)
        card_layout.setSpacing(18)

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

        login_button = QPushButton("Увійти")
        login_button.setObjectName("loginButton")
        login_button.clicked.connect(self.authorize)

        hint = QLabel("Тестові дані: admin / admin123 або manager / manager123")
        hint.setObjectName("hint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setWordWrap(True)

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(12)
        card_layout.addWidget(login_label)
        card_layout.addWidget(self.login_input)
        card_layout.addWidget(password_label)
        card_layout.addWidget(self.password_input)
        card_layout.addSpacing(10)
        card_layout.addWidget(login_button)
        card_layout.addWidget(hint)

        root.addWidget(card)

        self.password_input.returnPressed.connect(self.authorize)

    def authorize(self) -> None:
        login = self.login_input.text().strip()
        password = self.password_input.text().strip()

        session = authorize_user(login, password)

        if session is None:
            QMessageBox.warning(
                self,
                "Помилка авторизації",
                "Невірний логін або пароль.",
            )
            return

        self.main_window = MainWindow(session)
        self.main_window.showMaximized()
        self.close()
