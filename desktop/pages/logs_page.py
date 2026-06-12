from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from services.api_client import ApiClient
from services.api_worker import ApiWorker
from utils.display import format_datetime
from widgets.empty_table import EmptyTable
from widgets.page_controls import PageHeader, SearchInput, Toolbar, ToolbarButton


ACTION_LABELS = {
    "login": "Вхід у систему",
    "logout": "Вихід із системи",
    "user_created": "Створено працівника",
    "user_updated": "Оновлено працівника",
    "client_created": "Створено клієнта",
    "client_updated": "Оновлено клієнта",
    "client_deleted": "Видалено клієнта",
    "order_created": "Створено замовлення",
    "order_updated": "Оновлено замовлення",
    "order_status_updated": "Змінено статус замовлення",
    "order_prolonged": "Пролонговано замовлення",
    "order_deleted": "Видалено замовлення",
}


class LogsPage(QWidget):
    def __init__(self, api_client: ApiClient):
        super().__init__()
        self.api_client = api_client
        self.thread_pool = QThreadPool.globalInstance()
        self._worker: ApiWorker | None = None
        self._loading = False
        self.logs: list[dict[str, object]] = []

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)
        header = PageHeader("Логи системи", "Журнал дій працівників у CRM")

        toolbar = Toolbar("filters")
        self.search_input = SearchInput("Пошук за працівником або дією", 360)
        self.search_input.textChanged.connect(self.apply_filter)
        toolbar.add_item(self.search_input)
        toolbar.add_stretch()
        refresh_button = ToolbarButton("Оновити", "refresh", "secondary", 115)
        refresh_button.clicked.connect(self.refresh_data)
        toolbar.add_item(refresh_button)

        self.table = EmptyTable(
            headers=["Дата", "Працівник", "Дія", "Об'єкт", "ID", "Деталі"],
            column_widths=[165, 170, 220, 130, 80, 360],
            center_columns=[0, 4],
            empty_text="У журналі ще немає записів",
        )
        self.status_label = QLabel()
        self.status_label.setObjectName("emptyTableHint")
        layout.addWidget(header)
        layout.addWidget(toolbar)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.status_label)

    def refresh_data(self) -> None:
        if self._loading:
            return
        self._loading = True
        self.status_label.setText("Завантаження журналу...")
        self._worker = ApiWorker(self.api_client.get_logs)
        self._worker.signals.result.connect(self._apply_data)
        self._worker.signals.error.connect(self._show_error)
        self._worker.signals.finished.connect(self._finish_loading)
        self.thread_pool.start(self._worker)

    def _apply_data(self, payload: object) -> None:
        if not isinstance(payload, list):
            self._show_error("Backend повернув некоректний журнал.")
            return
        self.logs = [entry for entry in payload if isinstance(entry, dict)]
        self.apply_filter()

    def apply_filter(self) -> None:
        search = self.search_input.text().strip().casefold()
        filtered = [
            entry
            for entry in self.logs
            if not search
            or search
            in " ".join(
                str(entry.get(field) or "")
                for field in ("username", "action", "entity_name", "details")
            ).casefold()
        ]
        self.table.set_rows(
            [
                [
                    format_datetime(entry.get("created_at")),
                    entry.get("username") or "Система",
                    ACTION_LABELS.get(
                        str(entry.get("action")),
                        entry.get("action") or "—",
                    ),
                    entry.get("entity_name") or "—",
                    entry.get("entity_id") or "—",
                    entry.get("details") or "—",
                ]
                for entry in filtered
            ]
        )
        self.status_label.setText(f"Показано записів: {len(filtered)}")

    def _show_error(self, message: str) -> None:
        self.table.setRowCount(0)
        self.status_label.setText(f"Помилка завантаження: {message}")

    def _finish_loading(self) -> None:
        self._loading = False
        self._worker = None
