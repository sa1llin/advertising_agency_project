from PySide6.QtCore import QSize, Qt, QThreadPool, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from config import (
    APPLICATION_POLL_INTERVAL_MS,
    SIDEBAR_WIDTH,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
)
from models.session import UserSession
from pages.all_orders_page import AllOrdersPage
from pages.analytics_page import AnalyticsPage
from pages.clients_page import ClientsPage
from pages.logs_page import LogsPage
from pages.new_orders_page import NewOrdersPage
from pages.placeholder_page import PlaceholderPage
from pages.reports_page import ReportsPage
from pages.users_page import UsersPage
from permissions import get_nav_items
from services.api_client import ApiClient
from services.application_tracker import NewApplicationTracker
from services.api_worker import ApiWorker
from styles import MAIN_STYLE
from utils.display import application_service_label
from utils.icons import material_icon, material_pixmap


class MainWindow(QMainWindow):
    def __init__(self, session: UserSession, api_client: ApiClient):
        super().__init__()

        self.session = session
        self.nav_buttons: dict[str, QPushButton] = {}
        self.nav_icons: dict[str, str] = {}
        self.page_indexes: dict[str, int] = {}
        self.api_client = api_client
        self.thread_pool = QThreadPool.globalInstance()
        self._notification_worker: ApiWorker | None = None
        self.application_tracker = NewApplicationTracker()
        self._notification_popup: QMessageBox | None = None
        self.application_timer: QTimer | None = None
        self.tray_icon: QSystemTrayIcon | None = None

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
        if self.session.role == "manager":
            self._setup_application_notifications()

    def create_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(22, 24, 22, 24)
        layout.setSpacing(14)

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

        user_name = QLabel(self.session.full_name)
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
        layout.setContentsMargins(36, 36, 36, 32)
        layout.setSpacing(20)

        self.pages = QStackedWidget()

        for item in get_nav_items(self.session.role):
            key = str(item["key"])
            title = str(item["title"])
            subtitle = str(item["subtitle"])

            if key == "new_orders":
                page = NewOrdersPage(self.api_client, self.session.role)
            elif key == "all_orders":
                page = AllOrdersPage(self.api_client, self.session.role)
            elif key == "clients":
                page = ClientsPage(self.api_client, self.session.role)
            elif key == "analytics":
                page = AnalyticsPage(self.api_client, self.session.role)
            elif key == "reports":
                page = ReportsPage(self.api_client)
            elif key == "users":
                page = UsersPage(self.api_client, self.session.user_id)
            elif key == "logs":
                page = LogsPage(self.api_client)
            else:
                page = PlaceholderPage(title, subtitle)

            self.page_indexes[key] = self.pages.count()
            self.pages.addWidget(page)

        layout.addWidget(self.pages)

        return content

    def add_nav_button(
        self, layout: QVBoxLayout, page_key: str, title: str, icon_name: str
    ) -> None:
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
        current_page = self.pages.currentWidget()
        refresh_data = getattr(current_page, "refresh_data", None)
        if callable(refresh_data):
            refresh_data()

        for key, button in self.nav_buttons.items():
            is_active = key == page_key
            button.setProperty("active", "true" if is_active else "false")

            icon_color = "#ff7a1a" if is_active else "#ffffff"
            button.setIcon(material_icon(self.nav_icons[key], icon_color, 22))

            button.style().unpolish(button)
            button.style().polish(button)

    def logout(self) -> None:
        from windows.auth_window import AuthWindow

        try:
            self.api_client.logout()
        except Exception:
            pass
        self.auth_window = AuthWindow()
        self.auth_window.showMaximized()
        self.close()

    def _setup_application_notifications(self) -> None:
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(
                material_icon("assignment", "#ff7a1a", 24),
                self,
            )
            self.tray_icon.setToolTip("Creative Spark Agency CRM")
            self.tray_icon.messageClicked.connect(
                lambda: self.set_active_page("new_orders")
            )
            self.tray_icon.show()

        self.application_timer = QTimer(self)
        self.application_timer.setInterval(APPLICATION_POLL_INTERVAL_MS)
        self.application_timer.timeout.connect(self._poll_new_applications)
        self.application_timer.start()
        QTimer.singleShot(0, self._poll_new_applications)

    def _poll_new_applications(self) -> None:
        if self._notification_worker is not None:
            return
        self._notification_worker = ApiWorker(
            lambda: self.api_client.get_applications(
                status="new",
                limit=500,
            )
        )
        self._notification_worker.signals.result.connect(self._handle_application_poll)
        self._notification_worker.signals.finished.connect(
            self._finish_application_poll
        )
        self.thread_pool.start(self._notification_worker)

    def _handle_application_poll(self, payload: object) -> None:
        if not isinstance(payload, list):
            return
        applications = [item for item in payload if isinstance(item, dict)]
        new_applications = self.application_tracker.update(applications)
        if not new_applications:
            return
        self._show_new_application_notification(new_applications)

        page_index = self.page_indexes.get("new_orders")
        page = self.pages.widget(page_index) if page_index is not None else None
        refresh_data = getattr(page, "refresh_data", None)
        if callable(refresh_data):
            refresh_data()

    def _show_new_application_notification(
        self,
        applications: list[dict[str, object]],
    ) -> None:
        count = len(applications)
        if count == 1:
            application = applications[0]
            message = (
                f"{application.get('full_name') or 'Новий клієнт'}: "
                f"{application_service_label(application.get('service_type'))}"
            )
        else:
            message = f"Надійшло нових заявок: {count}"

        QApplication.alert(self, 8000)
        if self.tray_icon is not None:
            self.tray_icon.showMessage(
                "Нова заявка з сайту",
                message,
                QSystemTrayIcon.MessageIcon.Information,
                8000,
            )
            return

        popup = QMessageBox(self)
        popup.setWindowTitle("Нова заявка з сайту")
        popup.setText(message)
        popup.setIcon(QMessageBox.Icon.Information)
        popup.setStandardButtons(QMessageBox.StandardButton.Ok)
        popup.setWindowModality(Qt.WindowModality.NonModal)
        popup.show()
        self._notification_popup = popup
        QTimer.singleShot(8000, popup.close)

    def _finish_application_poll(self) -> None:
        self._notification_worker = None

    def closeEvent(self, event) -> None:
        if self.application_timer is not None:
            self.application_timer.stop()
        if self.tray_icon is not None:
            self.tray_icon.hide()
        super().closeEvent(event)
