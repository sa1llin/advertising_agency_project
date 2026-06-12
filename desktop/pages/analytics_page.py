from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from services.api_client import ApiClient
from services.api_worker import ApiWorker
from utils.display import format_money
from widgets.stat_card import StatCard
from widgets.empty_table import EmptyTable
from widgets.page_controls import PageHeader, ToolbarButton


class AnalyticsPage(QWidget):
    def __init__(self, api_client: ApiClient, user_role: str = "admin"):
        super().__init__()
        self.api_client = api_client
        self.user_role = user_role
        self.thread_pool = QThreadPool.globalInstance()
        self._worker: ApiWorker | None = None
        self._loading = False

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)
        refresh_button = ToolbarButton("Оновити", "refresh", "secondary", 115)
        refresh_button.clicked.connect(self.refresh_data)
        header = PageHeader(
            "Аналітика",
            "Ваші ключові показники роботи"
            if user_role == "manager"
            else "Ключові показники роботи рекламного агентства",
        )
        header.add_action(refresh_button)

        cards = QGridLayout()
        cards.setSpacing(18)
        prefix = "Мої " if user_role == "manager" else ""
        self.orders_card = StatCard("list_alt", f"{prefix}замовлення", "0", True)
        self.clients_card = StatCard("groups", f"{prefix}клієнти", "0")
        self.managers_card = StatCard(
            "manage_accounts",
            "Поточний менеджер" if user_role == "manager" else "Активні менеджери",
            "0",
        )
        self.revenue_card = StatCard("payments", f"{prefix}дохід", "0 грн")
        cards.addWidget(self.orders_card, 0, 0)
        cards.addWidget(self.clients_card, 0, 1)
        cards.addWidget(self.managers_card, 0, 2)
        cards.addWidget(self.revenue_card, 0, 3)

        self.table = EmptyTable(
            headers=["Показник", "Нові", "У роботі", "Завершені", "Скасовані"],
            column_widths=[240, 150, 150, 150, 150],
            min_height=220,
            center_columns=[1, 2, 3, 4],
            empty_text="Аналітичні дані ще не завантажені",
        )
        self.status_label = QLabel()
        self.status_label.setObjectName("emptyTableHint")

        layout.addWidget(header)
        layout.addLayout(cards)
        layout.addWidget(self.table)
        layout.addWidget(self.status_label)
        layout.addStretch()

    def refresh_data(self) -> None:
        if self._loading:
            return
        self._loading = True
        self.status_label.setText("Завантаження аналітики...")
        self._worker = ApiWorker(self.api_client.get_analytics_summary)
        self._worker.signals.result.connect(self._apply_data)
        self._worker.signals.error.connect(self._show_error)
        self._worker.signals.finished.connect(self._finish_loading)
        self.thread_pool.start(self._worker)

    def _apply_data(self, payload: object) -> None:
        if not isinstance(payload, dict):
            self._show_error("Backend повернув некоректні дані аналітики.")
            return
        self.orders_card.set_value(payload.get("orders_total", 0))
        self.clients_card.set_value(payload.get("clients_total", 0))
        self.managers_card.set_value(payload.get("active_managers", 0))
        self.revenue_card.set_value(format_money(payload.get("total_revenue")))
        statuses = payload.get("orders_by_status", {})
        if not isinstance(statuses, dict):
            statuses = {}
        self.table.set_rows(
            [[
                "Кількість замовлень",
                statuses.get("new", 0),
                statuses.get("in_progress", 0),
                statuses.get("completed", 0),
                statuses.get("cancelled", 0),
            ]]
        )
        self.status_label.setText("Аналітику оновлено.")

    def _show_error(self, message: str) -> None:
        self.status_label.setText(f"Помилка завантаження: {message}")

    def _finish_loading(self) -> None:
        self._loading = False
        self._worker = None
