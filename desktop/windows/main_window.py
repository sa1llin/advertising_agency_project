from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from config import SIDEBAR_WIDTH, WINDOW_MIN_HEIGHT, WINDOW_MIN_WIDTH
from models.session import UserSession
from pages.all_orders_page import AllOrdersPage
from pages.clients_page import ClientsPage
from pages.new_orders_page import NewOrdersPage
from pages.placeholder_page import PlaceholderPage
from pages.reports_page import ReportsPage
from permissions import get_nav_items
from styles import MAIN_STYLE
from utils.icons import material_icon, material_pixmap


class MainWindow(QMainWindow):
    def __init__(self, session: UserSession):
        super().__init__()

        self.session = session
        self.nav_buttons: dict[str, QPushButton] = {}
        self.nav_icons: dict[str, str] = {}
        self.page_indexes: dict[str, int] = {}

        self.setWindowTitle("Creative Spark Agency CRM")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.setStyleSheet(MAIN_STYLE)

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

    def create_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(24, 28, 24, 28)
        layout.setSpacing(18)

        user_icon = QLabel()
        user_icon.setFixedSize(54, 54)
        user_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_icon.setPixmap(material_pixmap("account_circle", "#0b1635", 34))
        user_icon.setStyleSheet(
            """
            QLabel {
                background-color: #f8fafc;
                border-radius: 27px;
            }
            """
        )

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

        layout.addSpacing(18)
        layout.addLayout(user_row)
        layout.addSpacing(16)
        layout.addWidget(divider)
        layout.addSpacing(8)

        for item in get_nav_items(self.session.role):
            self.add_nav_button(
                layout=layout,
                page_key=str(item["key"]),
                title=str(item["title"]),
                icon_name=str(item["icon"]),
            )

        layout.addStretch()

        logout_button = QPushButton("Вийти")
        logout_button.setObjectName("navButton")
        logout_button.setIcon(material_icon("logout", "#ffffff", 22))
        logout_button.setIconSize(QSize(22, 22))
        logout_button.clicked.connect(self.logout)
        layout.addWidget(logout_button)

        return sidebar

    def create_content(self) -> QWidget:
        content = QWidget()
        content.setObjectName("content")

        layout = QVBoxLayout(content)
        layout.setContentsMargins(34, 34, 34, 34)
        layout.setSpacing(24)

        self.pages = QStackedWidget()

        for item in get_nav_items(self.session.role):
            key = str(item["key"])
            title = str(item["title"])
            subtitle = str(item["subtitle"])

            if key == "new_orders":
                page = NewOrdersPage()
            elif key == "all_orders":
                page = AllOrdersPage()
            elif key == "clients":
                page = ClientsPage()
            elif key == "reports":
                page = ReportsPage()
            else:
                page = PlaceholderPage(title, subtitle)

            self.page_indexes[key] = self.pages.count()
            self.pages.addWidget(page)

        layout.addWidget(self.pages)

        return content

    def add_nav_button(self, layout: QVBoxLayout, page_key: str, title: str, icon_name: str) -> None:
        button = QPushButton(title)
        button.setObjectName("navButton")
        button.setProperty("active", "false")
        button.setIcon(material_icon(icon_name, "#ffffff", 22))
        button.setIconSize(QSize(22, 22))
        button.clicked.connect(lambda: self.set_active_page(page_key))

        self.nav_buttons[page_key] = button
        self.nav_icons[page_key] = icon_name

        layout.addWidget(button)

    def set_active_page(self, page_key: str) -> None:
        page_index = self.page_indexes.get(page_key)

        if page_index is None:
            return

        self.pages.setCurrentIndex(page_index)

        for key, button in self.nav_buttons.items():
            is_active = key == page_key
            button.setProperty("active", "true" if is_active else "false")

            icon_color = "#ff7a1a" if is_active else "#ffffff"
            button.setIcon(material_icon(self.nav_icons[key], icon_color, 22))

            button.style().unpolish(button)
            button.style().polish(button)

    def logout(self) -> None:
        from windows.auth_window import AuthWindow

        self.auth_window = AuthWindow()
        self.auth_window.showMaximized()
        self.close()
