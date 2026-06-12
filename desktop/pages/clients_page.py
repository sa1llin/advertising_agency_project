from collections.abc import Callable

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from dialogs.client_card_dialog import ClientCardDialog
from dialogs.client_form_dialog import ClientFormDialog
from services.api_client import ApiClient
from services.api_worker import ApiWorker
from utils.display import client_type_label, display_client_name
from widgets.empty_table import EmptyTable
from widgets.page_controls import PageHeader, SearchInput, Toolbar, ToolbarButton


class ClientsPage(QWidget):
    def __init__(self, api_client: ApiClient, user_role: str):
        super().__init__()

        self.api_client = api_client
        self.user_role = user_role
        self.thread_pool = QThreadPool.globalInstance()
        self._worker: ApiWorker | None = None
        self._loading = False
        self.clients: list[dict[str, object]] = []

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        create_button = ToolbarButton(
            "Створити клієнта",
            "add",
            "primary",
            190,
        )
        create_button.clicked.connect(self.create_client)
        header = PageHeader(
            "База клієнтів",
            "Перегляд, пошук і керування клієнтами рекламного агентства",
        )
        header.add_action(create_button)

        filters = Toolbar("filters")
        self.search_input = SearchInput(
            "Компанія, ПІБ, телефон або email",
            320,
        )
        self.search_input.textChanged.connect(self.apply_filter)
        filters.add_item(self.search_input)

        self.type_filter = QComboBox()
        self.type_filter.setObjectName("filterCombo")
        self.type_filter.setMinimumWidth(180)
        self.type_filter.addItem("Усі типи", None)
        self.type_filter.addItem("Фізична особа", "individual")
        self.type_filter.addItem("ФОП", "fop")
        self.type_filter.addItem("Юридична особа", "company")
        self.type_filter.currentIndexChanged.connect(self.apply_filter)
        filters.add_item(self.type_filter)

        self.status_filter = QComboBox()
        self.status_filter.setObjectName("filterCombo")
        self.status_filter.setMinimumWidth(170)
        self.status_filter.addItem("Усі статуси", None)
        self.status_filter.addItem("Активні", True)
        self.status_filter.addItem("Деактивовані", False)
        self.status_filter.currentIndexChanged.connect(self.apply_filter)
        filters.add_item(self.status_filter)
        filters.add_stretch()

        refresh_button = ToolbarButton("Оновити", "refresh", "secondary", 115)
        refresh_button.clicked.connect(self.refresh_data)
        filters.add_item(refresh_button)

        actions = Toolbar("actions")
        self.view_button = ToolbarButton(
            "Картка клієнта",
            "description",
            "secondary",
            155,
        )
        self.view_button.clicked.connect(self.view_client)
        actions.add_item(self.view_button)

        self.edit_button = ToolbarButton(
            "Редагувати",
            "edit",
            "secondary",
            135,
        )
        self.edit_button.clicked.connect(self.edit_client)
        actions.add_item(self.edit_button)

        self.delete_button = ToolbarButton(
            "Деактивувати",
            "delete",
            "danger",
            145,
        )
        self.delete_button.clicked.connect(self.delete_or_deactivate_client)
        if user_role != "admin":
            self.delete_button.setToolTip(
                "Менеджер може деактивувати клієнта, але не видалити його з бази."
            )
        actions.add_item(self.delete_button)
        actions.add_stretch()

        self.table = EmptyTable(
            headers=[
                "Тип",
                "Назва компанії / ПІБ",
                "Телефон",
                "Email",
                "Юридична адреса",
                "Статус",
            ],
            column_widths=[145, 280, 170, 220, 300, 110],
            status_columns=[5],
            empty_text="Клієнтів за обраними фільтрами немає",
        )
        self.table.itemSelectionChanged.connect(self._update_action_state)
        self.table.itemDoubleClicked.connect(lambda item: self.view_client())

        self.status_label = QLabel()
        self.status_label.setObjectName("emptyTableHint")

        layout.addWidget(header)
        layout.addWidget(filters)
        layout.addWidget(actions)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.status_label)

        self._update_action_state()

    def refresh_data(self) -> None:
        if self._loading:
            return

        self._loading = True
        self.status_label.setText("Завантаження всіх клієнтів з backend...")
        self._worker = ApiWorker(self.api_client.get_all_clients)
        self._worker.signals.result.connect(self._apply_data)
        self._worker.signals.error.connect(self._show_load_error)
        self._worker.signals.finished.connect(self._finish_loading)
        self.thread_pool.start(self._worker)

    def _apply_data(self, payload: object) -> None:
        if not isinstance(payload, list):
            self._show_load_error("Backend повернув некоректні дані клієнтів.")
            return

        self.clients = [client for client in payload if isinstance(client, dict)]
        self.apply_filter()

    def apply_filter(self) -> None:
        search = self.search_input.text().strip().casefold()
        selected_type = self.type_filter.currentData()
        selected_status = self.status_filter.currentData()
        filtered_clients: list[dict[str, object]] = []

        for client in self.clients:
            if selected_type and client.get("client_type") != selected_type:
                continue
            if (
                selected_status is not None
                and bool(client.get("is_active")) != selected_status
            ):
                continue

            searchable_values = (
                client.get("company_name"),
                client.get("full_name"),
                client.get("phone"),
                client.get("email"),
            )
            searchable_text = " ".join(
                str(value or "") for value in searchable_values
            ).casefold()
            if search and search not in searchable_text:
                continue

            filtered_clients.append(client)

        rows = [
            [
                client_type_label(client.get("client_type")),
                display_client_name(client),
                client.get("phone") or "—",
                client.get("email") or "—",
                client.get("legal_address") or "—",
                "Активний" if client.get("is_active") else "Неактивний",
            ]
            for client in filtered_clients
        ]
        self.table.set_rows(rows)

        self.table.set_row_ids(
            [client.get("id") for client in filtered_clients]
        )

        self.status_label.setText(
            f"Показано клієнтів: {len(filtered_clients)} з {len(self.clients)}"
        )
        self._update_action_state()

    def create_client(self) -> None:
        if self._loading:
            return

        dialog = ClientFormDialog(self)
        if not dialog.exec():
            return

        payload = dialog.get_data()
        self._run_mutation(
            lambda: self.api_client.create_client(payload),
            "Клієнта успішно додано.",
        )

    def edit_client(self) -> None:
        client = self._selected_client()
        if client is None:
            return

        dialog = ClientFormDialog(self, client)
        if not dialog.exec():
            return

        client_id = client.get("id")
        if not isinstance(client_id, int):
            return

        payload = dialog.get_data()
        self._run_mutation(
            lambda: self.api_client.update_client(client_id, payload),
            "Дані клієнта оновлено.",
        )

    def view_client(self) -> None:
        client = self._selected_client()
        if client is None:
            return
        ClientCardDialog(client, self).exec()

    def delete_or_deactivate_client(self) -> None:
        client = self._selected_client()
        if client is None:
            return

        client_id = client.get("id")
        if not isinstance(client_id, int):
            return

        new_status = not bool(client.get("is_active"))
        action = "відновити" if new_status else "деактивувати"
        answer = QMessageBox.question(
            self,
            "Зміна статусу клієнта",
            (
                f"{action.capitalize()} клієнта «{display_client_name(client)}»?\n\n"
                "Запис і пов'язані замовлення залишаться в базі."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self._run_mutation(
            lambda: self.api_client.update_client(
                client_id,
                {"is_active": new_status},
            ),
            "Клієнта відновлено." if new_status else "Клієнта деактивовано.",
        )

    def _run_mutation(
        self,
        operation: Callable[[], object],
        success_message: str,
    ) -> None:
        if self._loading:
            return

        self._loading = True
        self.status_label.setText("Збереження змін...")
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
    ) -> list[dict[str, object]]:
        operation()
        return self.api_client.get_all_clients()

    def _apply_mutation_result(
        self,
        payload: object,
        success_message: str,
    ) -> None:
        self._apply_data(payload)
        self.status_label.setText(success_message)

    def _selected_client(self) -> dict[str, object] | None:
        row_index = self.table.currentRow()
        if row_index < 0:
            QMessageBox.information(
                self,
                "Оберіть клієнта",
                "Спочатку оберіть клієнта в таблиці.",
            )
            return None

        item = self.table.item(row_index, 0)
        client_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        for client in self.clients:
            if client.get("id") == client_id:
                return client

        QMessageBox.warning(
            self,
            "Клієнта не знайдено",
            "Оновіть список і повторіть операцію.",
        )
        return None

    def _update_action_state(self) -> None:
        has_selection = self.table.currentRow() >= 0
        self.view_button.setEnabled(has_selection and not self._loading)
        self.edit_button.setEnabled(has_selection and not self._loading)
        self.delete_button.setEnabled(has_selection and not self._loading)
        selected = self._selected_client_without_message()
        self.delete_button.setText(
            "Відновити"
            if selected is not None and not selected.get("is_active")
            else "Деактивувати"
        )

    def _selected_client_without_message(self) -> dict[str, object] | None:
        row_index = self.table.currentRow()
        item = self.table.item(row_index, 0) if row_index >= 0 else None
        client_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        return next(
            (client for client in self.clients if client.get("id") == client_id),
            None,
        )

    def _show_load_error(self, message: str) -> None:
        self.clients = []
        self.table.setRowCount(0)
        self.status_label.setText(f"Помилка завантаження: {message}")

    def _show_operation_error(self, message: str) -> None:
        self.status_label.setText(f"Операцію не виконано: {message}")
        QMessageBox.warning(self, "Операцію не виконано", message)

    def _finish_loading(self) -> None:
        self._loading = False
        self._worker = None
        self._update_action_state()
