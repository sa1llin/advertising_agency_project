import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


@dataclass
class UserSession:
    login: str
    position: str
    role: str


USERS = {
    "admin": {
        "password": "admin123",
        "position": "Адміністратор системи",
        "role": "admin",
    },
    "manager": {
        "password": "manager123",
        "position": "Менеджер рекламного агентства",
        "role": "manager",
    },
}


MATERIAL_ICONS = {
    "assignment": (
        "M19 3h-4.18C14.4 1.84 13.3 1 12 1S9.6 1.84 9.18 3H5c-1.1 "
        "0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 "
        "2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 "
        "1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 "
        "14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"
    ),
    "list_alt": (
        "M19 5v14H5V5h14m0-2H5c-1.1 0-2 .9-2 "
        "2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 "
        "2-2V5c0-1.1-.9-2-2-2zM14 17H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"
    ),
    "groups": (
        "M12 12.75c1.63 0 3.07.39 4.24.9 1.08.48 "
        "1.76 1.56 1.76 2.73V18H6v-1.61c0-1.18.68-2.26 "
        "1.76-2.73 1.17-.52 2.61-.91 4.24-.91zM4 "
        "13c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 "
        "2 .9 2 2 2zm1.13 1.1c-.37-.06-.74-.1-1.13-.1-.99 "
        "0-1.93.21-2.78.58A2.01 2.01 0 0 0 0 "
        "16.43V18h4.5v-1.61c0-.83.23-1.61.63-2.29zM20 "
        "13c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 "
        "2 .9 2 2 2zm4 3.43c0-.81-.48-1.53-1.22-1.85A6.95 "
        "6.95 0 0 0 20 14c-.39 0-.76.04-1.13.1.4.68.63 "
        "1.46.63 2.29V18H24v-1.57zM12 6c1.66 0 3 1.34 "
        "3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3z"
    ),
    "bar_chart": "M5 9.2h3V19H5V9.2zM10.6 5h3v14h-3V5zm5.6 8h3v6h-3v-6z",
    "description": (
        "M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.89 "
        "2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 "
        "16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"
    ),
    "account_circle": (
        "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 "
        "10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 "
        "0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 "
        "1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 "
        "4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 "
        "1.94-3.5 3.22-6 3.22z"
    ),
    "history": (
        "M13 3c-4.97 0-9 4.03-9 9H1l4 "
        "4.01L9 12H6c0-3.86 3.14-7 7-7s7 3.14 "
        "7 7-3.14 7-7 7c-1.93 0-3.68-.78-4.95-2.05l-1.42 "
        "1.42C8.27 20 10.51 21 13 21c4.97 0 "
        "9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"
    ),
    "logout": (
        "M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 "
        "2.58L17 17l5-5zM4 5h8V3H4c-1.1 "
        "0-2 .9-2 2v14c0 1.1.9 2 2 "
        "2h8v-2H4V5z"
    ),
    "desktop_windows": (
        "M20 18c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2H4c-1.1 "
        "0-2 .9-2 2v10c0 1.1.9 2 2 2H0v2h24v-2h-4zM4 6h16v10H4V6z"
    ),
    "grid_view": (
        "M3 5v6h8V5H3zm6 4H5V7h4v2zm-6 "
        "10h8v-6H3v6zm2-4h4v2H5v-2zm8-10v6h8V5h-8zm6 "
        "4h-4V7h4v2zm-6 10h8v-6h-8v6zm2-4h4v2h-4v-2z"
    ),
    "print": (
        "M19 8H5c-1.66 0-3 1.34-3 3v6h4v4h12v-4h4v-6c0-1.66-1.34-3-3-3zM16 "
        "19H8v-5h8v5zm3-7c-.55 0-1-.45-1-1s.45-1 "
        "1-1 1 .45 1 1-.45 1-1 1zM18 3H6v4h12V3z"
    ),
}


def get_desktop_path(*parts: str) -> Path:
    return Path(__file__).resolve().parent.joinpath(*parts)


def material_icon(icon_name: str, color: str = "#ffffff", size: int = 24) -> QIcon:
    path = MATERIAL_ICONS.get(icon_name, MATERIAL_ICONS["assignment"])

    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24">
        <path fill="{color}" d="{path}"/>
    </svg>
    """

    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)


def material_pixmap(icon_name: str, color: str = "#0b1635", size: int = 28) -> QPixmap:
    return material_icon(icon_name, color, size).pixmap(size, size)


class AuthWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Creative Spark Agency CRM — Авторизація")
        self.setMinimumSize(1100, 700)

        self.setStyleSheet("""
            QWidget {
                background-color: #f4f7fb;
                color: #0b1635;
                font-family: Segoe UI;
            }

            QFrame#loginCard {
                background-color: #ffffff;
                border-radius: 28px;
                border: 1px solid #e6ebf2;
            }

            QLabel#brandTitle {
                font-size: 30px;
                font-weight: 800;
                color: #0b1635;
            }

            QLabel#subtitle {
                font-size: 16px;
                color: #6b7890;
            }

            QLabel#fieldLabel {
                font-size: 14px;
                font-weight: 600;
                color: #243453;
            }

            QLineEdit {
                min-height: 46px;
                border-radius: 14px;
                border: 1px solid #dbe3ee;
                background-color: #f8fafc;
                padding-left: 16px;
                padding-right: 16px;
                font-size: 15px;
            }

            QLineEdit:focus {
                border: 1px solid #ff6a00;
                background-color: #ffffff;
            }

            QPushButton#loginButton {
                min-height: 48px;
                border-radius: 16px;
                background-color: #ff6a00;
                color: white;
                font-size: 16px;
                font-weight: 700;
            }

            QPushButton#loginButton:hover {
                background-color: #e85f00;
            }

            QLabel#hint {
                color: #7a8699;
                font-size: 13px;
            }
        """)

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(460)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(42, 42, 42, 42)
        card_layout.setSpacing(18)

        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_path = get_desktop_path("assets", "logo.png")
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            logo.setPixmap(
                pixmap.scaled(
                    210,
                    90,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            logo.setText("Creative Spark\nAgency CRM")
            logo.setObjectName("brandTitle")

        subtitle = QLabel("Авторизація користувача")
        subtitle.setObjectName("subtitle")
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

        hint = QLabel("Тестові дані: admin / admin123")
        hint.setObjectName("hint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(logo)
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

    def authorize(self):
        login = self.login_input.text().strip()
        password = self.password_input.text().strip()

        user = USERS.get(login)

        if not user or user["password"] != password:
            QMessageBox.warning(
                self,
                "Помилка авторизації",
                "Невірний логін або пароль.",
            )
            return

        session = UserSession(
            login=login,
            position=user["position"],
            role=user["role"],
        )

        self.main_window = MainWindow(session)
        self.main_window.showMaximized()
        self.close()


class MainWindow(QMainWindow):
    def __init__(self, session: UserSession):
        super().__init__()

        self.session = session
        self.setWindowTitle("Creative Spark Agency CRM")
        self.setMinimumSize(1280, 760)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f4f7fb;
            }

            QWidget {
                font-family: Segoe UI;
                color: #0b1635;
            }

            QFrame#sidebar {
                background-color: #001b3a;
                border: none;
            }

            QLabel#userName {
                color: white;
                font-size: 17px;
                font-weight: 700;
            }

            QLabel#userPosition {
                color: #c6d0e0;
                font-size: 14px;
            }

            QPushButton#navButton {
                min-height: 48px;
                border: none;
                border-radius: 12px;
                padding-left: 16px;
                text-align: left;
                color: white;
                background-color: transparent;
                font-size: 15px;
                font-weight: 600;
            }

            QPushButton#navButton:hover {
                background-color: rgba(255, 255, 255, 0.10);
            }

            QPushButton#navButton[active="true"] {
                background-color: rgba(255, 106, 0, 0.18);
                color: #ff7a1a;
                border-left: 4px solid #ff6a00;
            }

            QWidget#content {
                background-color: #f4f7fb;
            }

            QLabel#pageTitle {
                font-size: 30px;
                font-weight: 800;
                color: #0b1635;
            }

            QLabel#pageSubtitle {
                font-size: 16px;
                color: #6b7890;
            }

            QFrame#statCard {
                background-color: #ffffff;
                border-radius: 18px;
                border: 1px solid #e7edf5;
            }

            QLabel#statIcon {
                background-color: #f3f5f8;
                border-radius: 14px;
                qproperty-alignment: AlignCenter;
            }

            QLabel#statTitle {
                font-size: 15px;
                font-weight: 700;
                color: #0b1635;
            }

            QLabel#statValue {
                font-size: 30px;
                font-weight: 900;
                color: #0b1635;
            }

            QLabel#emptyTableHint {
                color: #7a8699;
                font-size: 14px;
                padding-left: 6px;
            }

            QTableWidget {
                background-color: #ffffff;
                border-radius: 18px;
                border: 1px solid #e7edf5;
                gridline-color: #e9eef5;
                font-size: 14px;
                selection-background-color: #fff1e8;
                selection-color: #0b1635;
            }

            QHeaderView::section {
                background-color: #ffffff;
                color: #18315c;
                font-size: 14px;
                font-weight: 700;
                border: none;
                border-bottom: 1px solid #e7edf5;
                padding: 12px;
            }

            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eef2f7;
            }

            QPushButton#actionButton {
                border: none;
                color: #0b2a66;
                background-color: transparent;
                font-size: 14px;
                font-weight: 700;
            }

            QPushButton#actionButton:hover {
                color: #ff6a00;
            }
        """)

        self.nav_buttons = {}
        self.nav_icons = {}

        central = QWidget()
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = self.create_sidebar()
        content = self.create_content()

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content, 1)

        self.setCentralWidget(central)

        self.set_active_page("new_orders")

    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(270)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(24, 28, 24, 28)
        layout.setSpacing(18)

        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_path = get_desktop_path("assets", "logo.png")
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            logo.setPixmap(
                pixmap.scaled(
                    190,
                    82,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            logo.setText("Creative Spark Agency")
            logo.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 18px;
                    font-weight: 800;
                }
            """)

        user_icon = QLabel()
        user_icon.setFixedSize(54, 54)
        user_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_icon.setPixmap(material_pixmap("account_circle", "#0b1635", 34))
        user_icon.setStyleSheet("""
            QLabel {
                background-color: #f8fafc;
                border-radius: 27px;
            }
        """)

        user_name = QLabel(self.session.login)
        user_name.setObjectName("userName")

        user_position = QLabel(self.session.position)
        user_position.setObjectName("userPosition")
        user_position.setWordWrap(True)

        user_info = QVBoxLayout()
        user_info.setSpacing(4)
        user_info.addWidget(user_name)
        user_info.addWidget(user_position)

        user_row = QHBoxLayout()
        user_row.setSpacing(14)
        user_row.addWidget(user_icon)
        user_row.addLayout(user_info)

        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: rgba(255,255,255,0.18);")

        layout.addWidget(logo)
        layout.addSpacing(14)
        layout.addLayout(user_row)
        layout.addSpacing(16)
        layout.addWidget(divider)
        layout.addSpacing(8)

        self.add_nav_button(layout, "new_orders", "Нові замовлення", "assignment")
        self.add_nav_button(layout, "all_orders", "Усі замовлення", "list_alt")
        self.add_nav_button(layout, "clients", "База клієнтів", "groups")
        self.add_nav_button(layout, "analytics", "Аналітика", "bar_chart")
        self.add_nav_button(layout, "reports", "Звіти", "description")

        if self.session.role == "admin":
            self.add_nav_button(layout, "users", "Користувачі", "account_circle")
            self.add_nav_button(layout, "logs", "Логи системи", "history")

        layout.addStretch()

        logout_button = QPushButton("Вийти")
        logout_button.setObjectName("navButton")
        logout_button.setIcon(material_icon("logout", "#ffffff", 22))
        logout_button.setIconSize(QSize(22, 22))
        logout_button.clicked.connect(self.logout)
        layout.addWidget(logout_button)

        return sidebar

    def add_nav_button(self, layout, page_key, text, icon_name):
        button = QPushButton(text)
        button.setObjectName("navButton")
        button.setProperty("active", "false")
        button.setIcon(material_icon(icon_name, "#ffffff", 22))
        button.setIconSize(QSize(22, 22))
        button.clicked.connect(lambda: self.set_active_page(page_key))

        self.nav_buttons[page_key] = button
        self.nav_icons[page_key] = icon_name

        layout.addWidget(button)

    def create_content(self):
        content = QWidget()
        content.setObjectName("content")

        layout = QVBoxLayout(content)
        layout.setContentsMargins(34, 34, 34, 34)
        layout.setSpacing(24)

        self.pages = QStackedWidget()

        self.pages.addWidget(self.create_new_orders_page())
        self.pages.addWidget(self.create_placeholder_page("Усі замовлення", "Повний список замовлень агентства"))
        self.pages.addWidget(self.create_placeholder_page("База клієнтів", "Клієнти, компанії та контактні особи"))
        self.pages.addWidget(self.create_placeholder_page("Аналітика", "Показники продажів, доходів та популярних послуг"))
        self.pages.addWidget(self.create_placeholder_page("Звіти", "Формування звітів та друк документів"))

        if self.session.role == "admin":
            self.pages.addWidget(self.create_placeholder_page("Користувачі", "Керування адміністраторами та менеджерами"))
            self.pages.addWidget(self.create_placeholder_page("Логи системи", "Журнал дій користувачів у CRM"))

        layout.addWidget(self.pages)

        return content

    def create_new_orders_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(22)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Нові замовлення")
        title.setObjectName("pageTitle")

        subtitle = QLabel("Заявки на зворотний зв’язок, що надійшли з сайту")
        subtitle.setObjectName("pageSubtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        stats_grid = QGridLayout()
        stats_grid.setSpacing(20)

        stats_grid.addWidget(self.create_stat_card("assignment", "Нові заявки", "0", True), 0, 0)
        stats_grid.addWidget(self.create_stat_card("desktop_windows", "Білборд", "0"), 0, 1)
        stats_grid.addWidget(self.create_stat_card("grid_view", "LED", "0"), 0, 2)
        stats_grid.addWidget(self.create_stat_card("print", "Друк", "0"), 0, 3)

        layout.addLayout(stats_grid)

        table = self.create_orders_table()
        layout.addWidget(table, 1)

        empty_hint = QLabel("Дані будуть завантажуватися з бази даних після підключення API.")
        empty_hint.setObjectName("emptyTableHint")
        layout.addWidget(empty_hint)

        return page

    def create_stat_card(self, icon_name, title, value, orange=False):
        card = QFrame()
        card.setObjectName("statCard")
        card.setMinimumHeight(104)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(18)

        icon_label = QLabel()
        icon_label.setObjectName("statIcon")
        icon_label.setFixedSize(58, 58)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_color = "#ff6a00" if orange else "#0b1635"
        icon_label.setPixmap(material_pixmap(icon_name, icon_color, 30))

        if orange:
            icon_label.setStyleSheet("""
                QLabel {
                    background-color: #fff0df;
                    border-radius: 14px;
                }
            """)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setObjectName("statTitle")

        value_label = QLabel(value)
        value_label.setObjectName("statValue")

        if orange:
            value_label.setStyleSheet("color: #ff6a00;")

        text_layout.addWidget(title_label)
        text_layout.addWidget(value_label)

        layout.addWidget(icon_label)
        layout.addLayout(text_layout)
        layout.addStretch()

        return card

    def create_orders_table(self):
        table = QTableWidget()
        table.setColumnCount(5)
        table.setRowCount(0)

        table.setHorizontalHeaderLabels([
            "Замовник",
            "Дата та час замовлення",
            "Послуга",
            "Статус",
            "Дія",
        ])

        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setAlternatingRowColors(False)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        table.horizontalHeader().setStretchLastSection(True)
        table.setColumnWidth(0, 260)
        table.setColumnWidth(1, 250)
        table.setColumnWidth(2, 230)
        table.setColumnWidth(3, 160)
        table.setColumnWidth(4, 230)

        table.setMinimumHeight(430)

        return table

    def create_placeholder_page(self, title_text, subtitle_text):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel(title_text)
        title.setObjectName("pageTitle")

        subtitle = QLabel(subtitle_text)
        subtitle.setObjectName("pageSubtitle")

        card = QFrame()
        card.setObjectName("statCard")
        card.setMinimumHeight(220)

        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        message = QLabel("Розділ буде реалізовано на наступному етапі")
        message.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(message)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        layout.addWidget(card)
        layout.addStretch()

        return page

    def set_active_page(self, page_key):
        page_order = {
            "new_orders": 0,
            "all_orders": 1,
            "clients": 2,
            "analytics": 3,
            "reports": 4,
            "users": 5,
            "logs": 6,
        }

        index = page_order.get(page_key, 0)
        self.pages.setCurrentIndex(index)

        for key, button in self.nav_buttons.items():
            is_active = key == page_key
            button.setProperty("active", "true" if is_active else "false")

            icon_color = "#ff7a1a" if is_active else "#ffffff"
            button.setIcon(material_icon(self.nav_icons[key], icon_color, 22))

            button.style().unpolish(button)
            button.style().polish(button)

    def open_order(self, customer):
        QMessageBox.information(
            self,
            "Обробка заявки",
            f"Відкриття заявки клієнта:\n{customer}\n\n"
            "На наступному етапі тут буде форма перегляду та обробки заявки.",
        )

    def logout(self):
        self.auth_window = AuthWindow()
        self.auth_window.showMaximized()
        self.close()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Creative Spark Agency CRM")

    window = AuthWindow()
    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()