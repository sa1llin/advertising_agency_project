from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path

from PySide6.QtCore import QDate, Qt, QThreadPool
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFrame,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from dialogs.order_card_dialog import OrderCardDialog
from dialogs.order_form_dialog import OrderFormDialog
from services.api_client import ApiClient
from services.api_worker import ApiWorker
from services.invoice_service import (
    InvoiceError,
    generate_invoice,
    invoice_file_name,
)
from utils.display import (
    build_client_names,
    format_datetime,
    format_money,
    order_status_label,
    order_type_label,
)
from widgets.empty_table import EmptyTable
from widgets.page_controls import (
    FilterChip,
    PageHeader,
    SearchInput,
    Toolbar,
    ToolbarButton,
)

STATUS_OPTIONS = [
    ("Усі статуси", None),
    ("Нове", "new"),
    ("У роботі", "in_progress"),
    ("Призупинено", "paused"),
    ("Завершено", "completed"),
    ("Скасовано", "cancelled"),
]

TYPE_OPTIONS = [
    ("Усі послуги", None),
    ("Білборд", "billboard"),
    ("LED-екран", "led"),
    ("Друкована продукція", "printing"),
]


class AllOrdersPage(QWidget):
    def __init__(self, api_client: ApiClient, user_role: str = "admin"):
        super().__init__()
        self.api_client = api_client
        self.user_role = user_role
        self.thread_pool = QThreadPool.globalInstance()
        self._worker: ApiWorker | None = None
        self._loading = False
        self.orders: list[dict[str, object]] = []
        self.filtered_orders: list[dict[str, object]] = []
        self.clients: list[dict[str, object]] = []
        self.managers: list[dict[str, object]] = []
        self.client_names: dict[int, str] = {}
        self.manager_names: dict[int, str] = {}
        self.catalog: dict[str, object] = {
            "advertising_spaces": [],
            "pricing_items": [],
        }

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(0, 0, 0, 0)

        create_button = ToolbarButton(
            "Створити замовлення",
            "add",
            "primary",
            190,
        )
        create_button.clicked.connect(self.create_order)
        header = PageHeader(
            "Усі замовлення",
            "Створення, пошук і керування замовленнями агентства",
        )
        header.add_action(create_button)

        filters_panel = QFrame()
        filters_panel.setObjectName("filterBar")
        filters_layout = QVBoxLayout(filters_panel)
        filters_layout.setContentsMargins(14, 10, 14, 10)
        filters_layout.setSpacing(8)

        filters = Toolbar()
        self.search_input = SearchInput(
            "Номер, клієнт, послуга або менеджер",
            330,
        )
        self.search_input.textChanged.connect(self.apply_filter)
        filters.add_item(self.search_input)

        self.status_filter = self._filter_combo(STATUS_OPTIONS, 160)
        self.status_filter.currentIndexChanged.connect(self._status_filter_changed)
        filters.add_item(self.status_filter)

        self.type_filter = self._filter_combo(TYPE_OPTIONS, 190)
        self.type_filter.currentIndexChanged.connect(self.apply_filter)
        filters.add_item(self.type_filter)
        filters.add_stretch()

        refresh_button = ToolbarButton("Оновити", "refresh", "secondary", 115)
        refresh_button.clicked.connect(self.refresh_data)
        filters.add_item(refresh_button)
        filters_layout.addWidget(filters)

        date_filters = Toolbar()
        self.date_mode = self._filter_combo(
            [
                ("Усі дати", "all"),
                ("Конкретна дата", "date"),
                ("Період", "period"),
            ],
            170,
        )
        self.date_mode.currentIndexChanged.connect(self._update_date_filter)
        date_filters.add_item(self.date_mode)

        self.date_from = self._date_filter()
        self.date_from.setDate(QDate.currentDate())
        self.date_from.dateChanged.connect(self.apply_filter)
        date_filters.add_item(self.date_from)

        self.date_to = self._date_filter()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.dateChanged.connect(self.apply_filter)
        date_filters.add_item(self.date_to)
        date_filters.add_stretch()
        filters_layout.addWidget(date_filters)

        quick_filters = Toolbar()
        self.status_chips: list[FilterChip] = []
        for label, value in [
            ("Усі", None),
            ("Нові", "new"),
            ("У роботі", "in_progress"),
            ("Завершені", "completed"),
            ("Скасовані", "cancelled"),
        ]:
            chip = FilterChip(label, value)
            chip.clicked.connect(
                lambda checked=False, current=value: self._set_quick_status(current)
            )
            self.status_chips.append(chip)
            quick_filters.add_item(chip)
        self.status_chips[0].setChecked(True)
        quick_filters.add_stretch()

        actions = Toolbar("actions")
        self.view_button = ToolbarButton(
            "Переглянути",
            "description",
            "secondary",
            130,
        )
        self.view_button.clicked.connect(self.view_order)
        actions.add_item(self.view_button)

        self.invoice_button = ToolbarButton(
            "Рахунок-фактура",
            "receipt_long",
            "secondary",
            165,
        )
        self.invoice_button.clicked.connect(self.create_invoice)
        actions.add_item(self.invoice_button)

        self.edit_button = ToolbarButton(
            "Редагувати",
            "edit",
            "secondary",
            130,
        )
        self.edit_button.clicked.connect(self.edit_order)
        actions.add_item(self.edit_button)

        self.status_action = self._filter_combo(
            [(label, value) for label, value in STATUS_OPTIONS if value],
            160,
        )
        actions.add_item(self.status_action)
        self.change_status_button = ToolbarButton(
            "Змінити статус",
            "sync_alt",
            "secondary",
            150,
        )
        self.change_status_button.clicked.connect(self.change_order_status)
        actions.add_item(self.change_status_button)

        self.prolong_button = ToolbarButton(
            "Пролонгувати",
            "event_repeat",
            "secondary",
            145,
        )
        self.prolong_button.clicked.connect(self.prolong_order)
        actions.add_item(self.prolong_button)

        if self.user_role == "admin":
            self.delete_button = ToolbarButton(
                "Видалити",
                "delete",
                "danger",
                115,
            )
            self.delete_button.clicked.connect(self.delete_selected_order)
            actions.add_item(self.delete_button)
        else:
            self.delete_button = None

        actions.add_stretch()

        self.table = EmptyTable(
            headers=[
                "Номер замовлення",
                "Тип послуги",
                "Дата",
                "Клієнт",
                "Статус",
                "Сума",
                "Менеджер",
            ],
            column_widths=[165, 175, 155, 220, 155, 150, 210],
            status_columns=[4],
            money_columns=[5],
            center_columns=[2],
            empty_text="Замовлень за обраними фільтрами немає",
        )
        self.table.itemSelectionChanged.connect(self._update_action_state)
        self.table.itemDoubleClicked.connect(lambda item: self.view_order())

        self.status_label = QLabel()
        self.status_label.setObjectName("emptyTableHint")

        layout.addWidget(header)
        layout.addWidget(filters_panel)
        layout.addWidget(quick_filters)
        layout.addWidget(actions)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.status_label)

        self._update_date_filter()
        self._update_action_state()

    def refresh_data(self) -> None:
        if self._loading:
            return
        self._loading = True
        self.status_label.setText("Завантаження всіх замовлень із БД...")
        self._worker = ApiWorker(self._load_data)
        self._worker.signals.result.connect(self._apply_data)
        self._worker.signals.error.connect(self._show_error)
        self._worker.signals.finished.connect(self._finish_loading)
        self.thread_pool.start(self._worker)

    def _load_data(self) -> dict[str, object]:
        clients = self.api_client.get_all_clients()
        return {
            "orders": self.api_client.get_all_orders(),
            "clients": clients,
            "client_names": build_client_names(clients),
            "managers": self.api_client.get_managers(),
            "catalog": self.api_client.get_order_catalog(),
        }

    def _apply_data(self, payload: object) -> None:
        if not isinstance(payload, dict):
            self._show_error("Backend повернув некоректні дані замовлень.")
            return

        orders = payload.get("orders", [])
        clients = payload.get("clients", [])
        client_names = payload.get("client_names", {})
        managers = payload.get("managers", [])
        catalog = payload.get("catalog", {})
        if (
            not isinstance(orders, list)
            or not isinstance(clients, list)
            or not isinstance(client_names, dict)
            or not isinstance(managers, list)
            or not isinstance(catalog, dict)
        ):
            self._show_error("Backend повернув некоректні довідники замовлень.")
            return

        self.orders = [item for item in orders if isinstance(item, dict)]
        self.clients = [item for item in clients if isinstance(item, dict)]
        self.managers = [item for item in managers if isinstance(item, dict)]
        self.catalog = catalog
        self.client_names = {
            key: str(value)
            for key, value in client_names.items()
            if isinstance(key, int)
        }
        self.manager_names = {
            manager["id"]: str(
                manager.get("full_name") or manager.get("username") or "—"
            )
            for manager in self.managers
            if isinstance(manager.get("id"), int)
        }
        self.apply_filter()

    def apply_filter(self) -> None:
        search = self.search_input.text().strip().casefold()
        selected_status = self.status_filter.currentData()
        selected_type = self.type_filter.currentData()
        date_mode = self.date_mode.currentData()
        date_from = self.date_from.date().toPython()
        date_to = self.date_to.date().toPython()

        filtered: list[dict[str, object]] = []
        for order in self.orders:
            if selected_status and order.get("status") != selected_status:
                continue
            if selected_type and order.get("order_type") != selected_type:
                continue

            order_date = self._order_date(order)
            if date_mode == "date" and order_date != date_from:
                continue
            if date_mode == "period":
                period_start, period_end = sorted((date_from, date_to))
                if order_date is None or not period_start <= order_date <= period_end:
                    continue

            client_name = self._client_name(order)
            manager_name = self._manager_name(order)
            searchable = " ".join(
                [
                    str(order.get("order_number") or ""),
                    client_name,
                    str(order.get("order_type") or ""),
                    order_type_label(order.get("order_type")),
                    manager_name,
                ]
            ).casefold()
            if search and search not in searchable:
                continue
            filtered.append(order)

        self.filtered_orders = filtered
        self.table.set_rows(
            [
                [
                    order.get("order_number") or "—",
                    order_type_label(order.get("order_type")),
                    format_datetime(order.get("order_date")),
                    self._client_name(order),
                    order_status_label(order.get("status")),
                    format_money(order.get("total_amount")),
                    self._manager_name(order),
                ]
                for order in filtered
            ]
        )
        self.table.set_row_ids([order.get("id") for order in filtered])

        self.status_label.setText(
            f"Показано замовлень: {len(filtered)} з {len(self.orders)}"
        )
        self._update_action_state()

    def create_order(self) -> None:
        if self._loading:
            return
        if not self.clients:
            QMessageBox.information(
                self,
                "Немає клієнтів",
                "Спочатку додайте хоча б одного клієнта.",
            )
            return
        dialog = OrderFormDialog(
            self.clients,
            self.managers,
            self.user_role,
            self.catalog,
            self,
        )
        if dialog.exec():
            self._run_mutation(
                lambda: self.api_client.create_order(dialog.get_data()),
                "Замовлення створено. Номер сформовано автоматично.",
            )

    def edit_order(self) -> None:
        order = self._selected_order()
        if order is None:
            return
        dialog = OrderFormDialog(
            self.clients,
            self.managers,
            self.user_role,
            self.catalog,
            self,
            order,
        )
        if not dialog.exec():
            return
        order_id = order.get("id")
        if isinstance(order_id, int):
            self._run_mutation(
                lambda: self.api_client.update_order(order_id, dialog.get_data()),
                "Зміни замовлення збережено в БД.",
            )

    def prolong_order(self) -> None:
        order = self._selected_order()
        if order is None:
            return
        if order.get("order_type") not in ("billboard", "led"):
            QMessageBox.information(
                self,
                "Пролонгація недоступна",
                "Пролонгація передбачена для білбордів та LED-екранів.",
            )
            return
        order_id = order.get("id")
        if not isinstance(order_id, int):
            return
        dialog = OrderFormDialog(
            self.clients,
            self.managers,
            self.user_role,
            self.catalog,
            self,
            order,
            prolong_only=True,
        )
        if dialog.exec():
            payload = dialog.get_data()
            segments = payload.get("segments", [])
            if isinstance(segments, list):
                self._run_mutation(
                    lambda: self.api_client.prolong_order(order_id, segments),
                    "Замовлення пролонговано, новий період додано.",
                )

    def view_order(self) -> None:
        order = self._selected_order()
        if order is None:
            return
        OrderCardDialog(
            order,
            self._client_name(order),
            self._manager_name(order),
            self.catalog,
            self,
        ).exec()

    def create_invoice(self) -> None:
        order = self._selected_order()
        if order is None:
            return
        client = self._client_for_order(order)
        if client is None:
            QMessageBox.warning(
                self,
                "Рахунок не сформовано",
                "Не знайдено дані клієнта для вибраного замовлення.",
            )
            return

        default_name = invoice_file_name(order)
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Зберегти рахунок-фактуру",
            default_name,
            "PDF (*.pdf);;PNG (*.png)",
        )
        if not path:
            return
        destination = Path(path)
        if selected_filter.startswith("PNG"):
            destination = destination.with_suffix(".png")
        else:
            destination = destination.with_suffix(".pdf")

        try:
            saved_path = generate_invoice(
                destination,
                order,
                client,
                self._manager_name(order),
                self.catalog,
            )
        except (InvoiceError, OSError) as error:
            QMessageBox.warning(
                self,
                "Рахунок не сформовано",
                str(error),
            )
            return

        self.status_label.setText(f"Рахунок-фактуру збережено: {saved_path}")
        QMessageBox.information(
            self,
            "Рахунок сформовано",
            f"Рахунок-фактуру успішно збережено:\n{saved_path}",
        )

    def change_order_status(self) -> None:
        order = self._selected_order()
        if order is None:
            return
        order_id = order.get("id")
        new_status = self.status_action.currentData()
        if not isinstance(order_id, int) or not isinstance(new_status, str):
            return
        if order.get("status") == new_status:
            self.status_label.setText("У замовлення вже обраний цей статус.")
            return
        self._run_mutation(
            lambda: self.api_client.update_order_status(order_id, new_status),
            "Статус замовлення оновлено.",
        )

    def delete_selected_order(self) -> None:
        order = self._selected_order()
        if order is None:
            return
        order_id = order.get("id")
        if not isinstance(order_id, int):
            return
        answer = QMessageBox.warning(
            self,
            "Видалення замовлення",
            f"Видалити замовлення {order.get('order_number', order_id)}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._run_mutation(
            lambda: self.api_client.delete_order(order_id),
            "Замовлення видалено.",
        )

    def _run_mutation(
        self,
        operation: Callable[[], object],
        success_message: str,
    ) -> None:
        if self._loading:
            return
        self._loading = True
        self.status_label.setText("Збереження змін у БД...")
        self._worker = ApiWorker(lambda: self._mutate_and_reload(operation))
        self._worker.signals.result.connect(
            lambda payload: self._apply_mutation_result(payload, success_message)
        )
        self._worker.signals.error.connect(self._show_operation_error)
        self._worker.signals.finished.connect(self._finish_loading)
        self.thread_pool.start(self._worker)

    def _mutate_and_reload(
        self,
        operation: Callable[[], object],
    ) -> dict[str, object]:
        operation()
        return self._load_data()

    def _apply_mutation_result(self, payload: object, message: str) -> None:
        self._apply_data(payload)
        self.status_label.setText(message)

    def _selected_order(self) -> dict[str, object] | None:
        row = self.table.currentRow()
        item = self.table.item(row, 0) if row >= 0 else None
        order_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not isinstance(order_id, int):
            QMessageBox.information(
                self,
                "Оберіть замовлення",
                "Спочатку оберіть замовлення в таблиці.",
            )
            return None
        return next(
            (order for order in self.orders if order.get("id") == order_id),
            None,
        )

    def _selected_order_without_message(self) -> dict[str, object] | None:
        row = self.table.currentRow()
        item = self.table.item(row, 0) if row >= 0 else None
        order_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        return next(
            (order for order in self.orders if order.get("id") == order_id),
            None,
        )

    def _update_action_state(self) -> None:
        enabled = (
            self._selected_order_without_message() is not None and not self._loading
        )
        self.view_button.setEnabled(enabled)
        self.invoice_button.setEnabled(enabled)
        self.edit_button.setEnabled(enabled)
        self.status_action.setEnabled(enabled)
        self.change_status_button.setEnabled(enabled)
        selected = self._selected_order_without_message()
        self.prolong_button.setEnabled(
            enabled
            and selected is not None
            and selected.get("order_type") in ("billboard", "led")
            and selected.get("status") not in ("completed", "cancelled")
        )
        if self.delete_button is not None:
            self.delete_button.setEnabled(enabled)

    def _update_date_filter(self) -> None:
        mode = self.date_mode.currentData()
        self.date_from.setVisible(mode in ("date", "period"))
        self.date_to.setVisible(mode == "period")
        self.apply_filter()

    def _set_quick_status(self, status: object) -> None:
        index = self.status_filter.findData(status)
        if index >= 0:
            self.status_filter.setCurrentIndex(index)
        for chip in self.status_chips:
            chip.setChecked(chip.value == status)

    def _status_filter_changed(self) -> None:
        status = self.status_filter.currentData()
        for chip in self.status_chips:
            chip.setChecked(chip.value == status)
        self.apply_filter()

    def _client_name(self, order: dict[str, object]) -> str:
        client_id = order.get("client_id")
        if isinstance(client_id, int):
            return self.client_names.get(client_id, f"Клієнт #{client_id}")
        return "—"

    def _client_for_order(
        self,
        order: dict[str, object],
    ) -> dict[str, object] | None:
        client_id = order.get("client_id")
        return next(
            (client for client in self.clients if client.get("id") == client_id),
            None,
        )

    def _manager_name(self, order: dict[str, object]) -> str:
        manager_id = order.get("manager_id")
        if isinstance(manager_id, int):
            return self.manager_names.get(manager_id, f"Менеджер #{manager_id}")
        return "Не призначено"

    @staticmethod
    def _order_date(order: dict[str, object]) -> date | None:
        value = order.get("order_date")
        if isinstance(value, datetime):
            return value.date()
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
        except ValueError:
            return None

    @staticmethod
    def _filter_combo(
        options: list[tuple[str, object]],
        min_width: int,
    ) -> QComboBox:
        combo = QComboBox()
        combo.setObjectName("filterCombo")
        combo.setMinimumWidth(min_width)
        for label, value in options:
            combo.addItem(label, value)
        return combo

    @staticmethod
    def _date_filter() -> QDateEdit:
        field = QDateEdit()
        field.setObjectName("filterCombo")
        field.setCalendarPopup(True)
        field.setDisplayFormat("dd.MM.yyyy")
        field.setMinimumWidth(135)
        return field

    def _show_error(self, message: str) -> None:
        self.orders = []
        self.filtered_orders = []
        self.table.setRowCount(0)
        self.status_label.setText(f"Помилка завантаження: {message}")

    def _show_operation_error(self, message: str) -> None:
        self.status_label.setText(f"Операцію не виконано: {message}")
        QMessageBox.warning(self, "Операцію не виконано", message)

    def _finish_loading(self) -> None:
        self._loading = False
        self._worker = None
        self._update_action_state()
