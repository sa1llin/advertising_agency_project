from collections.abc import Callable

from PySide6.QtCore import QDate, Qt, QThreadPool
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from dialogs.application_card_dialog import ApplicationCardDialog
from dialogs.order_form_dialog import OrderFormDialog
from services.api_client import ApiClient, ApiError
from services.api_worker import ApiWorker
from utils.display import (
    application_service_label,
    application_status_label,
    format_datetime,
)
from widgets.empty_table import EmptyTable
from widgets.page_controls import PageHeader, SearchInput, Toolbar, ToolbarButton
from widgets.stat_card import StatCard


STATUS_OPTIONS = [
    ("Усі статуси", None),
    ("Нові", "new"),
    ("Оброблені", "processed"),
    ("Відхилені", "rejected"),
]


class NewOrdersPage(QWidget):
    def __init__(self, api_client: ApiClient, user_role: str = "admin"):
        super().__init__()
        self.api_client = api_client
        self.user_role = user_role
        self.thread_pool = QThreadPool.globalInstance()
        self._worker: ApiWorker | None = None
        self._loading = False
        self.applications: list[dict[str, object]] = []
        self.filtered_applications: list[dict[str, object]] = []
        self.clients: list[dict[str, object]] = []
        self.managers: list[dict[str, object]] = []
        self.catalog: dict[str, object] = {
            "advertising_spaces": [],
            "pricing_items": [],
        }

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(0, 0, 0, 0)

        header = PageHeader(
            "Нові заявки",
            "Звернення із сайту: перегляд, обробка та створення замовлень",
        )
        layout.addWidget(header)

        stats_grid = QGridLayout()
        stats_grid.setSpacing(20)
        self.total_card = StatCard("assignment", "Нові заявки", "0", True)
        self.billboard_card = StatCard("desktop_windows", "Білборд", "0")
        self.led_card = StatCard("grid_view", "LED", "0")
        self.printing_card = StatCard("print", "Друк", "0")
        self.total_card.clicked.connect(
            lambda: self._apply_stat_filter(None)
        )
        self.billboard_card.clicked.connect(
            lambda: self._apply_stat_filter("billboard")
        )
        self.led_card.clicked.connect(
            lambda: self._apply_stat_filter("led")
        )
        self.printing_card.clicked.connect(
            lambda: self._apply_stat_filter("printing")
        )
        stats_grid.addWidget(self.total_card, 0, 0)
        stats_grid.addWidget(self.billboard_card, 0, 1)
        stats_grid.addWidget(self.led_card, 0, 2)
        stats_grid.addWidget(self.printing_card, 0, 3)
        layout.addLayout(stats_grid)

        filters = Toolbar("filters")
        self.search_input = SearchInput("Ім'я, телефон, email або послуга", 240)
        self.search_input.textChanged.connect(self.apply_filter)
        filters.add_item(self.search_input)

        self.status_filter = QComboBox()
        self.status_filter.setObjectName("filterCombo")
        self.status_filter.setMinimumWidth(135)
        for label, value in STATUS_OPTIONS:
            self.status_filter.addItem(label, value)
        self.status_filter.setCurrentIndex(self.status_filter.findData("new"))
        self.status_filter.currentIndexChanged.connect(self.apply_filter)
        filters.add_item(self.status_filter)

        self.service_filter = QComboBox()
        self.service_filter.setObjectName("filterCombo")
        self.service_filter.setMinimumWidth(145)
        self.service_filter.addItem("Усі послуги", None)
        self.service_filter.addItem("Білборд", "billboard")
        self.service_filter.addItem("LED-екран", "led")
        self.service_filter.addItem("Друк", "printing")
        self.service_filter.addItem("Інша послуга", "other")
        self.service_filter.currentIndexChanged.connect(self.apply_filter)
        filters.add_item(self.service_filter)

        self.show_hidden = QCheckBox("Показувати приховані")
        self.show_hidden.toggled.connect(self.refresh_data)
        filters.add_item(self.show_hidden)
        filters.add_stretch()

        refresh_button = ToolbarButton("Оновити", "refresh", "secondary", 100)
        refresh_button.clicked.connect(self.refresh_data)
        filters.add_item(refresh_button)
        layout.addWidget(filters)

        actions_panel = QFrame()
        actions_panel.setObjectName("actionBar")
        actions_layout = QVBoxLayout(actions_panel)
        actions_layout.setContentsMargins(14, 10, 14, 10)
        actions_layout.setSpacing(8)

        creation_actions = Toolbar()
        self.view_button = ToolbarButton(
            "Переглянути",
            "description",
            "secondary",
            130,
        )
        self.view_button.clicked.connect(self.view_application)
        creation_actions.add_item(self.view_button)

        self.create_client_button = ToolbarButton(
            "Створити клієнта",
            "person_add",
            "secondary",
            165,
        )
        self.create_client_button.clicked.connect(self.create_client)
        creation_actions.add_item(self.create_client_button)

        self.create_order_button = ToolbarButton(
            "Створити замовлення",
            "add_shopping_cart",
            "primary",
            190,
        )
        self.create_order_button.clicked.connect(self.create_order)
        creation_actions.add_item(self.create_order_button)
        creation_actions.add_stretch()
        actions_layout.addWidget(creation_actions)

        workflow_actions = Toolbar()
        self.status_action = QComboBox()
        self.status_action.setObjectName("filterCombo")
        self.status_action.setMinimumWidth(155)
        for label, value in STATUS_OPTIONS[1:]:
            self.status_action.addItem(label, value)
        workflow_actions.add_item(self.status_action)

        self.change_status_button = ToolbarButton(
            "Змінити статус",
            "sync_alt",
            "secondary",
            145,
        )
        self.change_status_button.clicked.connect(self.change_status)
        workflow_actions.add_item(self.change_status_button)

        self.hide_button = ToolbarButton(
            "Приховати",
            "visibility_off",
            "secondary",
            125,
        )
        self.hide_button.clicked.connect(self.hide_application)
        workflow_actions.add_item(self.hide_button)

        if self.user_role == "admin":
            self.delete_button = ToolbarButton(
                "Видалити",
                "delete",
                "danger",
                115,
            )
            self.delete_button.clicked.connect(self.delete_application)
            workflow_actions.add_item(self.delete_button)
        else:
            self.delete_button = None
        workflow_actions.add_stretch()
        actions_layout.addWidget(workflow_actions)
        layout.addWidget(actions_panel)

        self.table = EmptyTable(
            headers=[
                "Ім'я",
                "Телефон",
                "Email",
                "Послуга",
                "Дата",
                "Статус",
                "Результат",
            ],
            column_widths=[200, 155, 210, 180, 155, 125, 180],
            status_columns=[5],
            center_columns=[4],
            empty_text="Нових заявок за обраними фільтрами немає",
        )
        self.table.itemSelectionChanged.connect(self._update_action_state)
        self.table.itemDoubleClicked.connect(lambda item: self.view_application())
        layout.addWidget(self.table, 1)

        self.status_label = QLabel()
        self.status_label.setObjectName("emptyTableHint")
        layout.addWidget(self.status_label)
        self._update_action_state()

    def refresh_data(self) -> None:
        if self._loading:
            return
        self._loading = True
        self.status_label.setText("Завантаження заявок з БД...")
        self._worker = ApiWorker(self._load_data)
        self._worker.signals.result.connect(self._apply_data)
        self._worker.signals.error.connect(self._show_error)
        self._worker.signals.finished.connect(self._finish_loading)
        self.thread_pool.start(self._worker)

    def _load_data(self) -> dict[str, object]:
        return {
            "applications": self.api_client.get_all_applications(
                include_hidden=self.show_hidden.isChecked()
            ),
            "clients": self.api_client.get_all_clients(),
            "managers": self.api_client.get_managers(),
            "catalog": self.api_client.get_order_catalog(),
        }

    def _apply_data(self, payload: object) -> None:
        if not isinstance(payload, dict):
            self._show_error("Backend повернув некоректні дані заявок.")
            return
        applications = payload.get("applications", [])
        clients = payload.get("clients", [])
        managers = payload.get("managers", [])
        catalog = payload.get("catalog", {})
        if (
            not isinstance(applications, list)
            or not isinstance(clients, list)
            or not isinstance(managers, list)
            or not isinstance(catalog, dict)
        ):
            self._show_error("Backend повернув некоректні довідники.")
            return
        self.applications = [item for item in applications if isinstance(item, dict)]
        self.clients = [item for item in clients if isinstance(item, dict)]
        self.managers = [item for item in managers if isinstance(item, dict)]
        self.catalog = catalog
        self._update_stats()
        self.apply_filter()

    def apply_filter(self) -> None:
        search = self.search_input.text().strip().casefold()
        selected_status = self.status_filter.currentData()
        selected_service = self.service_filter.currentData()
        filtered: list[dict[str, object]] = []
        for application in self.applications:
            if selected_status and application.get("status") != selected_status:
                continue
            if (
                selected_service
                and application.get("service_type") != selected_service
            ):
                continue
            searchable = " ".join(
                str(application.get(key) or "")
                for key in (
                    "full_name",
                    "phone",
                    "email",
                    "service_type",
                    "comment",
                )
            )
            searchable += " " + application_service_label(
                application.get("service_type")
            )
            if search and search not in searchable.casefold():
                continue
            filtered.append(application)

        self.filtered_applications = filtered
        self.table.set_rows(
            [
                [
                    application.get("full_name") or "—",
                    application.get("phone") or "—",
                    application.get("email") or "—",
                    application_service_label(application.get("service_type")),
                    format_datetime(application.get("submitted_at")),
                    application_status_label(application.get("status")),
                    self._result_text(application),
                ]
                for application in filtered
            ]
        )
        self.table.set_row_ids(
            [application.get("id") for application in filtered]
        )
        self.status_label.setText(
            f"Показано заявок: {len(filtered)} з {len(self.applications)}"
        )
        self._update_action_state()

    def view_application(self) -> None:
        application = self._selected_application()
        if application is not None:
            ApplicationCardDialog(application, self).exec()

    def create_client(self) -> None:
        application = self._selected_application()
        if application is None:
            return
        application_id = application.get("id")
        if not isinstance(application_id, int):
            return
        if application.get("client_id"):
            QMessageBox.information(
                self,
                "Клієнт вже створений",
                "Ця заявка вже прив'язана до клієнта.",
            )
            return
        self._run_mutation(
            lambda: self.api_client.create_client_from_application(application_id),
            "Клієнта створено та прив'язано до заявки.",
        )

    def create_order(self) -> None:
        application = self._selected_application()
        if application is None:
            return
        application_id = application.get("id")
        if not isinstance(application_id, int):
            return
        if application.get("order_id"):
            QMessageBox.information(
                self,
                "Замовлення вже створене",
                "Ця заявка вже перетворена на замовлення.",
            )
            return

        if not application.get("client_id"):
            answer = QMessageBox.question(
                self,
                "Створити клієнта",
                "Для замовлення потрібен клієнт. Створити його автоматично з даних заявки?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            try:
                client = self.api_client.create_client_from_application(application_id)
            except ApiError as error:
                self._show_operation_error(str(error))
                return
            self.clients.append(client)
            application["client_id"] = client.get("id")

        dialog = OrderFormDialog(
            self.clients,
            self.managers,
            self.user_role,
            self.catalog,
            self,
        )
        self._prefill_order_dialog(dialog, application)
        if not dialog.exec():
            return
        payload = dialog.get_data()
        self._run_mutation(
            lambda: self._create_and_link_order(application_id, payload),
            "Замовлення створено, заявку позначено як оброблену.",
        )

    def change_status(self) -> None:
        application = self._selected_application()
        if application is None:
            return
        application_id = application.get("id")
        new_status = self.status_action.currentData()
        if not isinstance(application_id, int) or not isinstance(new_status, str):
            return
        self._run_mutation(
            lambda: self.api_client.update_application_status(
                application_id,
                new_status,
            ),
            "Статус заявки оновлено.",
        )

    def hide_application(self) -> None:
        application = self._selected_application()
        if application is None:
            return
        application_id = application.get("id")
        if not isinstance(application_id, int):
            return
        if application.get("status") == "new":
            QMessageBox.information(
                self,
                "Заявка ще не оброблена",
                "Спочатку змініть статус на «Оброблена» або «Відхилена».",
            )
            return
        hidden = not bool(application.get("is_hidden"))
        self._run_mutation(
            lambda: self.api_client.set_application_hidden(application_id, hidden),
            "Заявку приховано." if hidden else "Заявку повернуто до списку.",
        )

    def delete_application(self) -> None:
        application = self._selected_application()
        if application is None:
            return
        application_id = application.get("id")
        if not isinstance(application_id, int):
            return
        answer = QMessageBox.warning(
            self,
            "Видалення заявки",
            f"Повністю видалити заявку #{application_id}? Цю дію не можна скасувати.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._run_mutation(
                lambda: self.api_client.delete_application(application_id),
                "Заявку видалено.",
            )

    def _create_and_link_order(
        self,
        application_id: int,
        payload: dict[str, object],
    ) -> dict[str, object]:
        order = self.api_client.create_order(payload)
        order_id = order.get("id")
        if not isinstance(order_id, int):
            raise ApiError("Backend не повернув ID створеного замовлення.")
        return self.api_client.link_application_order(application_id, order_id)

    def _prefill_order_dialog(
        self,
        dialog: OrderFormDialog,
        application: dict[str, object],
    ) -> None:
        client_index = dialog.client_combo.findData(application.get("client_id"))
        if client_index >= 0:
            dialog.client_combo.setCurrentIndex(client_index)
        service_type = application.get("service_type")
        if service_type in ("billboard", "led", "printing"):
            type_index = dialog.order_type.findData(service_type)
            if type_index >= 0:
                dialog.order_type.setCurrentIndex(type_index)

        calculation = application.get("calculation_data")
        if (
            application.get("source") == "calculator"
            and isinstance(calculation, dict)
            and calculation.get("service_type") == service_type
            and dialog.segment_editors
        ):
            editor = dialog.segment_editors[0]
            if service_type in ("billboard", "led"):
                space_index = editor.space_combo.findData(
                    calculation.get("advertising_space_id")
                )
                if space_index >= 0:
                    editor.space_combo.setCurrentIndex(space_index)
                _set_qdate(editor.period_start, calculation.get("period_start"))
                _set_qdate(editor.period_end, calculation.get("period_end"))
                if service_type == "billboard":
                    editor.need_printing.setChecked(
                        bool(calculation.get("need_printing"))
                    )
                else:
                    editor.video_seconds.setValue(
                        int(calculation.get("video_seconds") or 10)
                    )
                    editor.impressions_per_day.setValue(
                        int(calculation.get("impressions_per_day") or 100)
                    )
            elif service_type == "printing":
                _set_combo_value(
                    editor.product_type,
                    calculation.get("product_type"),
                )
                if calculation.get("product_type") == "other":
                    editor.custom_product_name.setText(
                        str(calculation.get("product_name") or "")
                    )
                _set_combo_value(
                    editor.material,
                    calculation.get("material_code"),
                )
                _set_combo_value(editor.size, calculation.get("size_code"))
                _set_combo_value(editor.color, calculation.get("color_mode"))
                editor.quantity.setValue(
                    int(calculation.get("quantity") or 1)
                )
            editor.update_estimate()

        comment_parts = [str(application.get("comment") or "").strip()]
        if (
            application.get("source") == "calculator"
            and application.get("estimated_total") is not None
        ):
            comment_parts.append(
                f"Орієнтовна сума з калькулятора сайту: "
                f"{application['estimated_total']} грн"
            )
        dialog.comment.setPlainText(
            "\n".join(part for part in comment_parts if part)
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

    def _selected_application(self) -> dict[str, object] | None:
        application = self._selected_application_without_message()
        if application is None:
            QMessageBox.information(
                self,
                "Оберіть заявку",
                "Спочатку оберіть заявку в таблиці.",
            )
        return application

    def _selected_application_without_message(self) -> dict[str, object] | None:
        row = self.table.currentRow()
        item = self.table.item(row, 0) if row >= 0 else None
        application_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        return next(
            (
                application
                for application in self.applications
                if application.get("id") == application_id
            ),
            None,
        )

    def _update_stats(self) -> None:
        new_items = [
            item
            for item in self.applications
            if item.get("status") == "new" and not item.get("is_hidden")
        ]
        self.total_card.set_value(len(new_items))
        self.billboard_card.set_value(
            sum(item.get("service_type") == "billboard" for item in new_items)
        )
        self.led_card.set_value(
            sum(item.get("service_type") == "led" for item in new_items)
        )
        self.printing_card.set_value(
            sum(item.get("service_type") == "printing" for item in new_items)
        )

    def _apply_stat_filter(self, service_type: object) -> None:
        status_index = self.status_filter.findData("new")
        if status_index >= 0:
            self.status_filter.setCurrentIndex(status_index)
        service_index = self.service_filter.findData(service_type)
        if service_index >= 0:
            self.service_filter.setCurrentIndex(service_index)
        self.apply_filter()

    def _update_action_state(self) -> None:
        selected = self._selected_application_without_message()
        enabled = selected is not None and not self._loading
        self.view_button.setEnabled(enabled)
        self.create_client_button.setEnabled(
            enabled and selected is not None and not selected.get("client_id")
        )
        self.create_order_button.setEnabled(
            enabled and selected is not None and not selected.get("order_id")
        )
        self.status_action.setEnabled(enabled)
        self.change_status_button.setEnabled(enabled)
        self.hide_button.setEnabled(
            enabled and selected is not None and selected.get("status") != "new"
        )
        if self.delete_button is not None:
            self.delete_button.setEnabled(enabled)

    @staticmethod
    def _result_text(application: dict[str, object]) -> str:
        if application.get("order_id"):
            return f"Замовлення #{application['order_id']}"
        if application.get("client_id"):
            return f"Клієнт #{application['client_id']}"
        return "—"

    def _show_error(self, message: str) -> None:
        self.applications = []
        self.filtered_applications = []
        self.table.setRowCount(0)
        self.status_label.setText(f"Помилка завантаження: {message}")

    def _show_operation_error(self, message: str) -> None:
        self.status_label.setText(f"Операцію не виконано: {message}")
        QMessageBox.warning(self, "Операцію не виконано", message)

    def _finish_loading(self) -> None:
        self._loading = False
        self._worker = None
        self._update_action_state()


def _set_combo_value(combo: QComboBox, value: object) -> None:
    index = combo.findData(value)
    if index >= 0:
        combo.setCurrentIndex(index)


def _set_qdate(field, value: object) -> None:
    if not value:
        return
    parsed = QDate.fromString(str(value)[:10], "yyyy-MM-dd")
    if parsed.isValid():
        field.setDate(parsed)
