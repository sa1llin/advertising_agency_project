from collections.abc import Callable

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtWidgets import QLabel, QMessageBox, QVBoxLayout, QWidget

from dialogs.user_form_dialog import UserFormDialog
from services.api_client import ApiClient
from services.api_worker import ApiWorker
from utils.display import format_datetime
from widgets.empty_table import EmptyTable
from widgets.page_controls import PageHeader, SearchInput, Toolbar, ToolbarButton


ROLE_LABELS = {
    "admin": "Адміністратор",
    "manager": "Менеджер",
}


class UsersPage(QWidget):
    def __init__(self, api_client: ApiClient, current_user_id: int):
        super().__init__()
        self.api_client = api_client
        self.current_user_id = current_user_id
        self.thread_pool = QThreadPool.globalInstance()
        self._worker: ApiWorker | None = None
        self._loading = False
        self.users: list[dict[str, object]] = []

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        create_button = ToolbarButton(
            "Додати працівника",
            "person_add",
            "primary",
            185,
        )
        create_button.clicked.connect(self.create_user)
        header = PageHeader(
            "Працівники",
            "Створення облікових записів і керування правами доступу",
        )
        header.add_action(create_button)

        toolbar = Toolbar("filters")
        self.search_input = SearchInput("Пошук за ПІБ, логіном або email", 360)
        self.search_input.textChanged.connect(self.apply_filter)
        toolbar.add_item(self.search_input)
        toolbar.add_stretch()
        refresh_button = ToolbarButton("Оновити", "refresh", "secondary", 115)
        refresh_button.clicked.connect(self.refresh_data)
        toolbar.add_item(refresh_button)
        actions = Toolbar("actions")
        self.edit_button = ToolbarButton("Редагувати", "edit", "secondary", 135)
        self.edit_button.clicked.connect(self.edit_user)
        actions.add_item(self.edit_button)
        self.toggle_button = ToolbarButton(
            "Змінити статус",
            "manage_accounts",
            "secondary",
            155,
        )
        self.toggle_button.clicked.connect(self.toggle_user_status)
        actions.add_item(self.toggle_button)
        actions.add_stretch()

        self.table = EmptyTable(
            headers=["ПІБ", "Логін", "Роль", "Email", "Телефон", "Статус", "Створено"],
            column_widths=[220, 150, 145, 210, 160, 115, 150],
            status_columns=[5],
            center_columns=[6],
            empty_text="Працівників за пошуковим запитом немає",
        )
        self.table.itemSelectionChanged.connect(self._update_action_state)

        self.status_label = QLabel()
        self.status_label.setObjectName("emptyTableHint")
        layout.addWidget(header)
        layout.addWidget(toolbar)
        layout.addWidget(actions)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.status_label)
        self._update_action_state()

    def refresh_data(self) -> None:
        if self._loading:
            return
        self._loading = True
        self.status_label.setText("Завантаження працівників...")
        self._worker = ApiWorker(self.api_client.get_users)
        self._worker.signals.result.connect(self._apply_data)
        self._worker.signals.error.connect(self._show_error)
        self._worker.signals.finished.connect(self._finish_loading)
        self.thread_pool.start(self._worker)

    def _apply_data(self, payload: object) -> None:
        if not isinstance(payload, list):
            self._show_error("Backend повернув некоректні дані працівників.")
            return
        self.users = [user for user in payload if isinstance(user, dict)]
        self.apply_filter()

    def apply_filter(self) -> None:
        search = self.search_input.text().strip().casefold()
        filtered = [
            user
            for user in self.users
            if not search
            or search
            in " ".join(
                str(user.get(field) or "")
                for field in ("full_name", "username", "email", "phone")
            ).casefold()
        ]
        self.table.set_rows(
            [
                [
                    user.get("full_name") or "—",
                    user.get("username") or "—",
                    ROLE_LABELS.get(str(user.get("role")), user.get("role") or "—"),
                    user.get("email") or "—",
                    user.get("phone") or "—",
                    "Активний" if user.get("is_active") else "Неактивний",
                    format_datetime(user.get("created_at")),
                ]
                for user in filtered
            ]
        )
        self.table.set_row_ids([user.get("id") for user in filtered])
        self.status_label.setText(
            f"Показано працівників: {len(filtered)} з {len(self.users)}"
        )
        self._update_action_state()

    def create_user(self) -> None:
        dialog = UserFormDialog(self)
        if dialog.exec():
            self._run_mutation(
                lambda: self.api_client.create_user(dialog.get_data()),
                "Працівника додано.",
            )

    def edit_user(self) -> None:
        user = self._selected_user()
        if user is None:
            return
        dialog = UserFormDialog(self, user)
        if not dialog.exec():
            return
        user_id = user.get("id")
        if isinstance(user_id, int):
            self._run_mutation(
                lambda: self.api_client.update_user(user_id, dialog.get_data()),
                "Дані працівника оновлено.",
            )

    def toggle_user_status(self) -> None:
        user = self._selected_user()
        if user is None:
            return
        user_id = user.get("id")
        if not isinstance(user_id, int):
            return
        new_status = not bool(user.get("is_active"))
        action = "активувати" if new_status else "деактивувати"
        answer = QMessageBox.question(
            self,
            "Зміна статусу",
            f"Ви справді хочете {action} обліковий запис {user.get('username')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._run_mutation(
            lambda: self.api_client.update_user(user_id, {"is_active": new_status}),
            "Статус працівника оновлено.",
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
        self._worker.signals.error.connect(self._show_error)
        self._worker.signals.finished.connect(self._finish_loading)
        self.thread_pool.start(self._worker)

    def _mutate_and_reload(
        self,
        operation: Callable[[], object],
    ) -> list[dict[str, object]]:
        operation()
        return self.api_client.get_users()

    def _apply_mutation_result(self, payload: object, message: str) -> None:
        self._apply_data(payload)
        self.status_label.setText(message)

    def _selected_user(self) -> dict[str, object] | None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Оберіть працівника", "Оберіть рядок у таблиці.")
            return None
        item = self.table.item(row, 0)
        user_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        return next((user for user in self.users if user.get("id") == user_id), None)

    def _update_action_state(self) -> None:
        selected = self._selected_user_without_message()
        enabled = selected is not None and not self._loading
        self.edit_button.setEnabled(enabled)
        self.toggle_button.setEnabled(
            enabled and selected.get("id") != self.current_user_id
            if selected is not None
            else False
        )

    def _selected_user_without_message(self) -> dict[str, object] | None:
        row = self.table.currentRow()
        item = self.table.item(row, 0) if row >= 0 else None
        user_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        return next((user for user in self.users if user.get("id") == user_id), None)

    def _show_error(self, message: str) -> None:
        self.status_label.setText(f"Операцію не виконано: {message}")
        QMessageBox.warning(self, "Операцію не виконано", message)

    def _finish_loading(self) -> None:
        self._loading = False
        self._worker = None
        self._update_action_state()
