from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from PySide6.QtCore import QDate, QThreadPool
from PySide6.QtGui import QPageLayout, QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
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

from services.api_client import ApiClient
from services.api_worker import ApiWorker
from services.report_export import (
    ReportColumn,
    build_report_html,
    export_report_csv,
    export_report_xlsx,
)
from utils.display import (
    build_client_names,
    format_date,
    format_money,
    manager_label,
    order_type_label,
)
from widgets.empty_table import EmptyTable
from widgets.page_controls import PageHeader, SearchInput, Toolbar, ToolbarButton
from widgets.stat_card import StatCard

MONEY = Decimal("0.01")
LED_DAILY_CAPACITY_SECONDS = 18 * 60 * 60

REPORT_MODE_OPTIONS = [
    ("По замовленнях", "orders"),
    ("По клієнтах", "clients"),
    ("По площинах", "spaces"),
]

TYPE_OPTIONS = [
    ("Усі послуги", None),
    ("Білборд", "billboard"),
    ("LED-екран", "led"),
    ("Друкована продукція", "printing"),
]

PERIOD_OPTIONS = [
    ("За весь час", "all"),
    ("Поточний місяць", "current_month"),
    ("Попередній місяць", "previous_month"),
    ("Власний період", "custom"),
]

PRINT_PRODUCT_LABELS = {
    "business_card": "Візитки",
    "calendar": "Календарі",
    "flyer": "Флаєри",
    "wristband": "Браслети",
    "mug": "Чашки",
    "other": "Інша продукція",
}

ORDER_COLUMNS: list[ReportColumn] = [
    ("order_number", "Номер замовлення", "text"),
    ("client", "Клієнт", "text"),
    ("period", "Період", "text"),
    ("service", "Тип послуги", "text"),
    ("manager", "Менеджер", "text"),
    ("sale_amount", "Сума продажу", "money"),
    ("vat_amount", "ПДВ", "money"),
    ("discount_amount", "Знижка", "money"),
    ("total_amount", "Підсумкова сума", "money"),
]

CLIENT_COLUMNS: list[ReportColumn] = [
    ("client", "Клієнт", "text"),
    ("order_number", "Номер замовлення", "text"),
    ("products", "Продукція / розміщення", "text"),
    ("period", "Період", "text"),
    ("service", "Тип послуги", "text"),
    ("manager", "Менеджер", "text"),
    ("sale_amount", "Сума продажу", "money"),
    ("vat_amount", "ПДВ", "money"),
    ("discount_amount", "Знижка", "money"),
    ("total_amount", "Підсумкова сума", "money"),
]

SPACE_COLUMNS: list[ReportColumn] = [
    ("space", "Площина / адреса", "text"),
    ("service", "Тип", "text"),
    ("size", "Розмір", "text"),
    ("order_count", "Кількість замовлень", "integer"),
    ("orders", "Які замовлення", "text"),
    ("occupied_days", "Зайнято днів", "integer"),
    ("utilization", "Завантаження LED, %", "text"),
    ("income_amount", "Дохід без ПДВ", "money"),
]


class ReportsPage(QWidget):
    def __init__(self, api_client: ApiClient):
        super().__init__()

        self.api_client = api_client
        self.thread_pool = QThreadPool.globalInstance()
        self._worker: ApiWorker | None = None
        self._loading = False
        self.orders: list[dict[str, object]] = []
        self.filtered_orders: list[dict[str, object]] = []
        self.report_rows: list[dict[str, object]] = []
        self.client_names: dict[int, str] = {}
        self.manager_names: dict[int, str] = {}
        self.spaces: dict[int, dict[str, object]] = {}
        self.current_columns = ORDER_COLUMNS
        self.totals = _empty_order_totals()

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        self.generate_button = ToolbarButton(
            "Сформувати звіт",
            "add_circle",
            "primary",
            180,
        )
        self.generate_button.clicked.connect(self.generate_report)
        header = PageHeader(
            "Звіти",
            "Замовлення, активність клієнтів і ефективність рекламних площин",
        )
        header.add_action(self.generate_button)

        filters_panel = QFrame()
        filters_panel.setObjectName("filterBar")
        filters_layout = QVBoxLayout(filters_panel)
        filters_layout.setContentsMargins(14, 10, 14, 10)
        filters_layout.setSpacing(8)

        primary_filters = Toolbar()
        self.report_mode = QComboBox()
        self.report_mode.setObjectName("filterCombo")
        self.report_mode.setMinimumWidth(190)
        for label, value in REPORT_MODE_OPTIONS:
            self.report_mode.addItem(label, value)
        self.report_mode.currentIndexChanged.connect(self._report_mode_changed)
        primary_filters.add_item(self.report_mode)

        self.search_input = SearchInput(
            "Номер замовлення, клієнт або менеджер",
            280,
        )
        self.search_input.returnPressed.connect(self.generate_report)
        primary_filters.add_item(self.search_input)

        self.entity_filter = QComboBox()
        self.entity_filter.setObjectName("filterCombo")
        self.entity_filter.setMinimumWidth(260)
        self.entity_filter.currentIndexChanged.connect(self._filter_changed)
        primary_filters.add_item(self.entity_filter)
        primary_filters.add_stretch()

        refresh_button = ToolbarButton("Оновити дані", "refresh", "secondary", 130)
        refresh_button.clicked.connect(self.refresh_data)
        primary_filters.add_item(refresh_button)
        filters_layout.addWidget(primary_filters)

        secondary_filters = Toolbar()
        self.type_filter = QComboBox()
        self.type_filter.setObjectName("filterCombo")
        self.type_filter.setMinimumWidth(180)
        for label, value in TYPE_OPTIONS:
            self.type_filter.addItem(label, value)
        self.type_filter.currentIndexChanged.connect(self._filter_changed)
        secondary_filters.add_item(self.type_filter)

        self.period_filter = QComboBox()
        self.period_filter.setObjectName("filterCombo")
        self.period_filter.setMinimumWidth(190)
        for label, value in PERIOD_OPTIONS:
            self.period_filter.addItem(label, value)
        self.period_filter.currentIndexChanged.connect(self._period_filter_changed)
        secondary_filters.add_item(self.period_filter)
        secondary_filters.add_stretch()
        filters_layout.addWidget(secondary_filters)

        self.custom_period_bar = Toolbar()
        self.custom_period_bar.add_item(QLabel("Період з"))
        self.date_from = _date_filter()
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.custom_period_bar.add_item(self.date_from)
        self.custom_period_bar.add_item(QLabel("по"))
        self.date_to = _date_filter()
        self.date_to.setDate(QDate.currentDate())
        self.custom_period_bar.add_item(self.date_to)
        self.custom_period_bar.add_stretch()
        filters_layout.addWidget(self.custom_period_bar)
        self.date_from.dateChanged.connect(self._filter_changed)
        self.date_to.dateChanged.connect(self._filter_changed)

        actions = Toolbar("actions")
        self.print_button = ToolbarButton("Друк", "print", "secondary", 105)
        self.print_button.clicked.connect(self.print_report)
        actions.add_item(self.print_button)
        self.export_button = ToolbarButton(
            "Експорт",
            "download",
            "secondary",
            130,
        )
        self.export_button.clicked.connect(self.export_report)
        actions.add_item(self.export_button)
        actions.add_stretch()

        cards = Toolbar()
        self.first_card = StatCard("payments", "Сума продажу", "0.00 грн", True)
        self.second_card = StatCard("description", "ПДВ", "0.00 грн")
        self.third_card = StatCard("sync_alt", "Знижки", "0.00 грн")
        self.fourth_card = StatCard(
            "bar_chart",
            "Підсумкова сума",
            "0.00 грн",
        )
        self.sales_card = self.first_card
        self.vat_card = self.second_card
        self.discount_card = self.third_card
        self.total_card = self.fourth_card
        cards.add_item(self.first_card)
        cards.add_item(self.second_card)
        cards.add_item(self.third_card)
        cards.add_item(self.fourth_card)

        self.table = EmptyTable(
            headers=[header for _, header, _ in ORDER_COLUMNS],
            column_widths=[155, 210, 180, 165, 190, 135, 110, 110, 150],
            money_columns=[5, 6, 7, 8],
            center_columns=[2],
            empty_text="За обраними параметрами замовлень немає",
        )

        self.status_label = QLabel("Оберіть параметри та сформуйте звіт.")
        self.status_label.setObjectName("emptyTableHint")

        layout.addWidget(header)
        layout.addWidget(filters_panel)
        layout.addWidget(actions)
        layout.addWidget(cards)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.status_label)

        self._report_mode_changed()
        self._update_period_controls()
        self._update_action_state()

    def refresh_data(self) -> None:
        if self._loading:
            return

        self._loading = True
        self._update_action_state()
        self.status_label.setText("Завантаження даних для звіту...")
        self._worker = ApiWorker(self._load_data)
        self._worker.signals.result.connect(self._apply_data)
        self._worker.signals.error.connect(self._show_error)
        self._worker.signals.finished.connect(self._finish_loading)
        self.thread_pool.start(self._worker)

    def _load_data(self) -> dict[str, object]:
        clients = self.api_client.get_all_clients()
        return {
            "orders": self.api_client.get_all_orders(),
            "client_names": build_client_names(clients),
            "managers": self.api_client.get_managers(),
            "catalog": self.api_client.get_order_catalog(
                include_inactive=True,
            ),
        }

    def _apply_data(self, payload: object) -> None:
        if not isinstance(payload, dict):
            self._show_error("Backend повернув некоректні дані звіту.")
            return

        orders = payload.get("orders", [])
        client_names = payload.get("client_names", {})
        managers = payload.get("managers", [])
        catalog = payload.get("catalog", {})
        if (
            not isinstance(orders, list)
            or not isinstance(client_names, dict)
            or not isinstance(managers, list)
            or not isinstance(catalog, dict)
        ):
            self._show_error("Backend повернув некоректні довідники звіту.")
            return

        self.orders = [order for order in orders if isinstance(order, dict)]
        self.client_names = {
            key: str(value)
            for key, value in client_names.items()
            if isinstance(key, int)
        }
        self.manager_names = {
            manager["id"]: str(
                manager.get("full_name") or manager.get("username") or "—"
            )
            for manager in managers
            if isinstance(manager, dict) and isinstance(manager.get("id"), int)
        }
        spaces = catalog.get("advertising_spaces", [])
        self.spaces = {
            space["id"]: space
            for space in spaces
            if isinstance(space, dict) and isinstance(space.get("id"), int)
        }
        self._fill_entity_filter(preserve_selection=True)
        self.generate_report()

    def generate_report(self) -> None:
        mode = str(self.report_mode.currentData() or "orders")
        period_start, period_end = self._selected_period()
        base_orders = self._filtered_source_orders(period_start, period_end)

        if mode == "clients":
            rows = self._client_report_rows(base_orders)
            totals = _client_totals(rows)
        elif mode == "spaces":
            rows = self._space_report_rows(
                base_orders,
                period_start,
                period_end,
            )
            totals = _space_totals(rows)
        else:
            rows = [self._order_report_row(order) for order in base_orders]
            totals = _order_totals(rows)

        search = self.search_input.text().strip().casefold()
        if search:
            rows = [
                row
                for row in rows
                if search
                in " ".join(str(value or "") for value in row.values()).casefold()
            ]
            if mode == "clients":
                totals = _client_totals(rows)
            elif mode == "spaces":
                totals = _space_totals(rows)
            else:
                totals = _order_totals(rows)

        self.filtered_orders = base_orders
        self.report_rows = rows
        self.totals = totals
        self._set_table_rows(mode, rows)
        self._update_summary(mode)
        self.status_label.setText(self._status_text(mode))
        self._update_action_state()

    def _filtered_source_orders(
        self,
        period_start: date | None,
        period_end: date | None,
    ) -> list[dict[str, object]]:
        selected_type = self.type_filter.currentData()
        mode = self.report_mode.currentData()
        entity_id = self.entity_filter.currentData()
        filtered: list[dict[str, object]] = []
        for order in self.orders:
            if order.get("status") == "cancelled":
                continue
            if selected_type and order.get("order_type") != selected_type:
                continue
            if mode == "clients" and entity_id is not None:
                if order.get("client_id") != entity_id:
                    continue
            order_start, order_end = _order_period(order)
            if not _periods_overlap(
                order_start,
                order_end,
                period_start,
                period_end,
            ):
                continue
            filtered.append(order)
        return filtered

    def _order_report_row(
        self,
        order: dict[str, object],
    ) -> dict[str, object]:
        order_start, order_end = _order_period(order)
        financial = _order_financials(order)
        return {
            "order_number": order.get("order_number") or "—",
            "client": self._client_name(order),
            "period": _period_text(order_start, order_end),
            "service": order_type_label(order.get("order_type")),
            "manager": self._manager_name(order),
            **financial,
        }

    def _client_report_rows(
        self,
        orders: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for order in orders:
            order_start, order_end = _order_period(order)
            rows.append(
                {
                    "client_id": order.get("client_id"),
                    "client": self._client_name(order),
                    "order_number": order.get("order_number") or "—",
                    "products": self._order_product_summary(order),
                    "period": _period_text(order_start, order_end),
                    "service": order_type_label(order.get("order_type")),
                    "manager": self._manager_name(order),
                    **_order_financials(order),
                }
            )
        return sorted(
            rows,
            key=lambda row: (
                str(row["client"]).casefold(),
                str(row["order_number"]).casefold(),
            ),
        )

    def _order_product_summary(self, order: dict[str, object]) -> str:
        order_type = str(order.get("order_type") or "")
        segments = order.get("segments")
        segment_rows = (
            [segment for segment in segments if isinstance(segment, dict)]
            if isinstance(segments, list)
            else []
        )

        if order_type == "printing":
            products = [
                _printing_product_label(segment, order) for segment in segment_rows
            ]
            if not products:
                products = [_printing_product_label({}, order)]
            return "; ".join(dict.fromkeys(products))

        placements: list[str] = []
        for segment in segment_rows:
            space_id = segment.get("advertising_space_id")
            space = self.spaces.get(space_id, {}) if isinstance(space_id, int) else {}
            label = (
                _space_label(space_id, space)
                if isinstance(space_id, int)
                else order_type_label(order_type)
            )
            size = str(space.get("size") or "").strip()
            placement = f"{order_type_label(order_type)}: {label}"
            if size and size.casefold() not in placement.casefold():
                placement += f" ({size})"
            if order_type == "billboard" and segment.get("need_printing"):
                placement += ", друк плаката"
            if order_type == "led":
                video_seconds = segment.get("video_seconds")
                impressions = segment.get("impressions_per_day")
                if video_seconds:
                    placement += f", ролик {video_seconds} с"
                if impressions:
                    placement += f", {impressions} показів/день"
            placements.append(placement)

        return "; ".join(dict.fromkeys(placements)) or order_type_label(order_type)

    def _space_report_rows(
        self,
        orders: list[dict[str, object]],
        period_start: date | None,
        period_end: date | None,
    ) -> list[dict[str, object]]:
        selected_space_id = (
            self.entity_filter.currentData()
            if self.report_mode.currentData() == "spaces"
            else None
        )
        groups: dict[int, dict[str, object]] = {}
        for order in orders:
            segments = order.get("segments")
            if not isinstance(segments, list):
                continue
            discount_factor = _discount_factor(order)
            for segment in segments:
                if not isinstance(segment, dict):
                    continue
                space_id = segment.get("advertising_space_id")
                if not isinstance(space_id, int):
                    continue
                if selected_space_id is not None and space_id != selected_space_id:
                    continue
                segment_start = _parse_date(segment.get("period_start"))
                segment_end = _parse_date(segment.get("period_end"))
                overlap = _intersection(
                    segment_start,
                    segment_end,
                    period_start,
                    period_end,
                )
                if overlap is None:
                    continue

                overlap_start, overlap_end = overlap
                occupied_dates = set(_date_range(overlap_start, overlap_end))
                total_segment_days = (
                    (segment_end - segment_start).days + 1
                    if segment_start is not None and segment_end is not None
                    else len(occupied_dates)
                )
                overlap_ratio = (
                    Decimal(len(occupied_dates)) / Decimal(total_segment_days)
                    if total_segment_days > 0
                    else Decimal("0")
                )
                base_income = _decimal(segment.get("rental_cost")) + _decimal(
                    segment.get("placement_cost")
                )
                if base_income == 0:
                    base_income = _decimal(segment.get("subtotal"))
                income = base_income * discount_factor * overlap_ratio

                space = self.spaces.get(space_id, {})
                space_type = str(
                    space.get("space_type") or order.get("order_type") or ""
                )
                group = groups.setdefault(
                    space_id,
                    {
                        "space": _space_label(space_id, space),
                        "space_type": space_type,
                        "service": order_type_label(space_type),
                        "size": space.get("size") or "—",
                        "order_numbers": set(),
                        "occupied_dates": set(),
                        "led_seconds_by_date": {},
                        "income_amount": Decimal("0"),
                    },
                )
                group["order_numbers"].add(str(order.get("order_number") or "—"))
                group["occupied_dates"].update(occupied_dates)
                if space_type == "led":
                    daily_seconds = int(segment.get("video_seconds") or 0) * int(
                        segment.get("impressions_per_day") or 0
                    )
                    for occupied_date in occupied_dates:
                        group["led_seconds_by_date"][occupied_date] = (
                            group["led_seconds_by_date"].get(
                                occupied_date,
                                0,
                            )
                            + daily_seconds
                        )
                group["income_amount"] += income

        rows: list[dict[str, object]] = []
        for group in groups.values():
            occupied_dates = group["occupied_dates"]
            denominator = _utilization_denominator(
                occupied_dates,
                period_start,
                period_end,
            )
            occupied_days = len(occupied_dates)
            utilization = "—"
            if group["space_type"] == "led":
                reserved_seconds = sum(group["led_seconds_by_date"].values())
                capacity = LED_DAILY_CAPACITY_SECONDS * denominator
                utilization_value = (
                    Decimal(reserved_seconds) * 100 / Decimal(capacity)
                    if capacity > 0
                    else Decimal("0")
                )
                utilization = f"{utilization_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f} %"
            order_numbers = sorted(group["order_numbers"])
            rows.append(
                {
                    "space": group["space"],
                    "service": group["service"],
                    "size": group["size"],
                    "order_count": len(order_numbers),
                    "orders": ", ".join(order_numbers),
                    "occupied_days": occupied_days,
                    "utilization": utilization,
                    "income_amount": group["income_amount"].quantize(
                        MONEY,
                        rounding=ROUND_HALF_UP,
                    ),
                }
            )
        return sorted(rows, key=lambda row: str(row["space"]).casefold())

    def export_report(self) -> None:
        if not self.report_rows:
            QMessageBox.information(
                self,
                "Немає даних",
                "Сформуйте непорожній звіт перед експортом.",
            )
            return

        mode = str(self.report_mode.currentData() or "orders")
        default_name = (
            f"{_report_slug(mode)}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        )
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Експорт звіту",
            default_name,
            "Excel (*.xlsx);;CSV (*.csv)",
        )
        if not path:
            return

        common = {
            "period_label": self._period_label(),
            "rows": self.report_rows,
            "totals": self.totals,
            "report_title": self._report_title(),
            "columns": self.current_columns,
        }
        try:
            if selected_filter.startswith("CSV") or Path(path).suffix.lower() == ".csv":
                if Path(path).suffix.lower() != ".csv":
                    path += ".csv"
                export_report_csv(path, **common)
            else:
                if Path(path).suffix.lower() != ".xlsx":
                    path += ".xlsx"
                export_report_xlsx(path, **common)
        except Exception as error:
            QMessageBox.warning(
                self,
                "Експорт не виконано",
                f"Не вдалося зберегти звіт:\n{error}",
            )
            return

        self.status_label.setText(f"Звіт експортовано: {path}")
        QMessageBox.information(
            self,
            "Експорт завершено",
            f"Звіт успішно збережено:\n{path}",
        )

    def print_report(self) -> None:
        if not self.report_rows:
            QMessageBox.information(
                self,
                "Немає даних",
                "Сформуйте непорожній звіт перед друком.",
            )
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageOrientation(QPageLayout.Orientation.Landscape)
        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle(self._report_title())
        if not dialog.exec():
            return

        document = QTextDocument(self)
        document.setDocumentMargin(18)
        document.setHtml(
            build_report_html(
                self._period_label(),
                self.report_rows,
                self.totals,
                report_title=self._report_title(),
                columns=self.current_columns,
            )
        )
        document.print_(printer)
        self.status_label.setText("Звіт передано на друк.")

    def _set_table_rows(
        self,
        mode: str,
        rows: list[dict[str, object]],
    ) -> None:
        if mode == "clients":
            self.current_columns = CLIENT_COLUMNS
            self.table.configure_columns(
                [header for _, header, _ in CLIENT_COLUMNS],
                [220, 165, 360, 190, 150, 190, 140, 110, 110, 150],
                money_columns=[6, 7, 8, 9],
                center_columns=[1, 3, 4],
                empty_text="Замовлень клієнтів за обраними параметрами немає",
            )
        elif mode == "spaces":
            self.current_columns = SPACE_COLUMNS
            self.table.configure_columns(
                [header for _, header, _ in SPACE_COLUMNS],
                [300, 130, 100, 120, 240, 115, 130, 155],
                money_columns=[7],
                center_columns=[1, 2, 3, 5, 6],
                empty_text="Площин за обраними параметрами немає",
            )
        else:
            self.current_columns = ORDER_COLUMNS
            self.table.configure_columns(
                [header for _, header, _ in ORDER_COLUMNS],
                [155, 210, 180, 165, 190, 135, 110, 110, 150],
                money_columns=[5, 6, 7, 8],
                center_columns=[2],
                empty_text="Замовлень за обраними параметрами немає",
            )

        self.table.set_rows(
            [
                [
                    _table_value(row.get(key), value_type)
                    for key, _, value_type in self.current_columns
                ]
                for row in rows
            ]
        )

    def _update_summary(self, mode: str) -> None:
        if mode == "clients":
            self.first_card.set_title("Клієнтів")
            self.first_card.set_value(
                len({row.get("client_id") for row in self.report_rows})
            )
            self.second_card.set_title("Замовлень")
            self.second_card.set_value(int(self.totals["order_count"]))
            self.third_card.set_title("Сума продажу")
            self.third_card.set_value(format_money(self.totals["sale_amount"]))
            self.fourth_card.set_title("Підсумкова сума")
            self.fourth_card.set_value(format_money(self.totals["total_amount"]))
            return
        if mode == "spaces":
            self.first_card.set_title("Площин")
            self.first_card.set_value(len(self.report_rows))
            self.second_card.set_title("Замовлень")
            self.second_card.set_value(int(self.totals["order_count"]))
            self.third_card.set_title("Зайнято днів")
            self.third_card.set_value(int(self.totals["occupied_days"]))
            self.fourth_card.set_title("Дохід без ПДВ")
            self.fourth_card.set_value(format_money(self.totals["income_amount"]))
            return

        self.first_card.set_title("Сума продажу")
        self.first_card.set_value(format_money(self.totals["sale_amount"]))
        self.second_card.set_title("ПДВ")
        self.second_card.set_value(format_money(self.totals["vat_amount"]))
        self.third_card.set_title("Знижки")
        self.third_card.set_value(format_money(self.totals["discount_amount"]))
        self.fourth_card.set_title("Підсумкова сума")
        self.fourth_card.set_value(format_money(self.totals["total_amount"]))

    def _status_text(self, mode: str) -> str:
        if mode == "clients":
            client_count = len({row.get("client_id") for row in self.report_rows})
            return (
                f"Клієнтів: {client_count}. "
                f"Замовлень: {int(self.totals['order_count'])}. "
                f"Підсумкова сума: {format_money(self.totals['total_amount'])}."
            )
        if mode == "spaces":
            return (
                f"Площин: {len(self.report_rows)}. "
                f"Зайнято днів: {int(self.totals['occupied_days'])}. "
                f"Дохід без ПДВ: {format_money(self.totals['income_amount'])}."
            )
        return (
            f"Сформовано: {len(self.report_rows)} замовлень. "
            f"Період: {self._period_label()}. "
            f"Підсумкова сума: {format_money(self.totals['total_amount'])}."
        )

    def _client_name(self, order: dict[str, object]) -> str:
        client_id = order.get("client_id")
        if isinstance(client_id, int):
            return self.client_names.get(client_id, f"Клієнт #{client_id}")
        return "—"

    def _manager_name(self, order: dict[str, object]) -> str:
        manager_id = order.get("manager_id")
        if isinstance(manager_id, int):
            return self.manager_names.get(
                manager_id,
                manager_label(manager_id),
            )
        return "Не призначено"

    def _selected_period(self) -> tuple[date | None, date | None]:
        mode = self.period_filter.currentData()
        today = QDate.currentDate()
        if mode == "current_month":
            start = QDate(today.year(), today.month(), 1)
            return start.toPython(), start.addMonths(1).addDays(-1).toPython()
        if mode == "previous_month":
            start = QDate(today.year(), today.month(), 1).addMonths(-1)
            return start.toPython(), start.addMonths(1).addDays(-1).toPython()
        if mode == "custom":
            start, end = sorted(
                (self.date_from.date().toPython(), self.date_to.date().toPython())
            )
            return start, end
        return None, None

    def _period_label(self) -> str:
        start, end = self._selected_period()
        if start is None or end is None:
            return "за весь час"
        return f"{format_date(start)} — {format_date(end)}"

    def _report_title(self) -> str:
        mode = self.report_mode.currentData()
        if mode == "clients":
            return "Звіт по клієнтах"
        if mode == "spaces":
            return "Звіт по рекламних площинах"
        return "Звіт по замовленнях"

    def _report_mode_changed(self) -> None:
        mode = self.report_mode.currentData()
        self.entity_filter.setVisible(mode in ("clients", "spaces"))
        if mode == "clients":
            self.search_input.setPlaceholderText("Клієнт, номер замовлення або послуга")
        elif mode == "spaces":
            self.search_input.setPlaceholderText("Адреса, розмір або номер замовлення")
        else:
            self.search_input.setPlaceholderText(
                "Номер замовлення, клієнт або менеджер"
            )
        self._fill_entity_filter(preserve_selection=False)
        if self.orders:
            self.generate_report()

    def _fill_entity_filter(self, *, preserve_selection: bool = True) -> None:
        mode = self.report_mode.currentData()
        selected_id = self.entity_filter.currentData() if preserve_selection else None
        self.entity_filter.blockSignals(True)
        self.entity_filter.clear()
        if mode == "clients":
            self.entity_filter.addItem("Усі клієнти", None)
            for client_id, name in sorted(
                self.client_names.items(),
                key=lambda item: item[1].casefold(),
            ):
                self.entity_filter.addItem(name, client_id)
        elif mode == "spaces":
            self.entity_filter.addItem("Усі площини", None)
            for space_id, space in sorted(
                self.spaces.items(),
                key=lambda item: _space_label(*item).casefold(),
            ):
                self.entity_filter.addItem(
                    _space_label(space_id, space),
                    space_id,
                )
        if selected_id is not None:
            selected_index = self.entity_filter.findData(selected_id)
            if selected_index >= 0:
                self.entity_filter.setCurrentIndex(selected_index)
        self.entity_filter.blockSignals(False)

    def _period_filter_changed(self) -> None:
        self._update_period_controls()
        self._filter_changed()

    def _filter_changed(self) -> None:
        if self.orders and not self._loading:
            self.generate_report()

    def _update_period_controls(self) -> None:
        self.custom_period_bar.setVisible(self.period_filter.currentData() == "custom")

    def _update_action_state(self) -> None:
        has_data = bool(self.report_rows) and not self._loading
        self.generate_button.setEnabled(not self._loading)
        self.print_button.setEnabled(has_data)
        self.export_button.setEnabled(has_data)

    def _show_error(self, message: str) -> None:
        self.orders = []
        self.filtered_orders = []
        self.report_rows = []
        mode = str(self.report_mode.currentData() or "orders")
        if mode == "clients":
            self.totals = _client_totals([])
        elif mode == "spaces":
            self.totals = _space_totals([])
        else:
            self.totals = _empty_order_totals()
        self.table.setRowCount(0)
        self._update_summary(mode)
        self.status_label.setText(f"Помилка завантаження: {message}")
        self._update_action_state()

    def _finish_loading(self) -> None:
        self._loading = False
        self._worker = None
        self._update_action_state()


def _date_filter() -> QDateEdit:
    field = QDateEdit()
    field.setObjectName("filterCombo")
    field.setCalendarPopup(True)
    field.setDisplayFormat("dd.MM.yyyy")
    field.setMinimumWidth(145)
    return field


def _order_period(
    order: dict[str, object],
) -> tuple[date | None, date | None]:
    periods: list[tuple[date, date]] = []
    segments = order.get("segments")
    if isinstance(segments, list):
        for segment in segments:
            if not isinstance(segment, dict):
                continue
            start = _parse_date(segment.get("period_start"))
            end = _parse_date(segment.get("period_end"))
            if start is not None and end is not None:
                periods.append((start, end))

    if periods:
        return min(item[0] for item in periods), max(item[1] for item in periods)

    rental_start = _parse_date(order.get("rental_start"))
    rental_end = _parse_date(order.get("rental_end"))
    if rental_start is not None or rental_end is not None:
        return rental_start or rental_end, rental_end or rental_start

    order_date = _parse_date(order.get("order_date"))
    return order_date, order_date


def _order_financials(order: dict[str, object]) -> dict[str, Decimal]:
    total_amount = _decimal(order.get("total_amount"))
    vat_amount = _decimal(order.get("vat_amount"))
    discount_amount = _decimal(order.get("discount_amount"))
    sale_amount = _decimal(
        order.get("amount_without_vat"),
        fallback=total_amount + discount_amount - vat_amount,
    )
    return {
        "sale_amount": sale_amount,
        "vat_amount": vat_amount,
        "discount_amount": discount_amount,
        "total_amount": total_amount,
    }


def _periods_overlap(
    item_start: date | None,
    item_end: date | None,
    filter_start: date | None,
    filter_end: date | None,
) -> bool:
    if filter_start is None or filter_end is None:
        return True
    if item_start is None or item_end is None:
        return False
    return item_end >= filter_start and item_start <= filter_end


def _intersection(
    item_start: date | None,
    item_end: date | None,
    filter_start: date | None,
    filter_end: date | None,
) -> tuple[date, date] | None:
    if item_start is None or item_end is None:
        return None
    start = max(item_start, filter_start) if filter_start is not None else item_start
    end = min(item_end, filter_end) if filter_end is not None else item_end
    return (start, end) if start <= end else None


def _date_range(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _utilization_denominator(
    occupied_dates: set[date],
    period_start: date | None,
    period_end: date | None,
) -> int:
    if period_start is not None and period_end is not None:
        return (period_end - period_start).days + 1
    if not occupied_dates:
        return 0
    return (max(occupied_dates) - min(occupied_dates)).days + 1


def _discount_factor(order: dict[str, object]) -> Decimal:
    sale_amount = _decimal(order.get("amount_without_vat"))
    discount = _decimal(order.get("discount_amount"))
    if sale_amount <= 0:
        return Decimal("1")
    return max((sale_amount - discount) / sale_amount, Decimal("0"))


def _space_label(space_id: int, space: dict[str, object]) -> str:
    title = str(space.get("title") or "").strip()
    location = str(space.get("location") or "").strip()
    if title and location and title.casefold() not in location.casefold():
        return f"{title} — {location}"
    return location or title or f"Площина #{space_id}"


def _printing_product_label(
    segment: dict[str, object],
    order: dict[str, object],
) -> str:
    product_type = str(segment.get("product_type") or "").strip()
    name = str(
        segment.get("product_name")
        or order.get("product_name")
        or PRINT_PRODUCT_LABELS.get(product_type)
        or product_type
        or "Друкована продукція"
    ).strip()
    details: list[str] = []
    quantity = segment.get("quantity") or order.get("quantity")
    if quantity:
        details.append(f"{quantity} шт.")
    size = str(segment.get("size_code") or order.get("product_size") or "").strip()
    if size:
        details.append(f"розмір {size}")
    material = str(
        segment.get("material_code") or order.get("material_type") or ""
    ).strip()
    if material:
        details.append(f"матеріал {material}")
    return f"{name} ({', '.join(details)})" if details else name


def _parse_date(value: object) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _period_text(start: date | None, end: date | None) -> str:
    if start is None and end is None:
        return "—"
    return f"{format_date(start)} — {format_date(end)}"


def _decimal(value: object, fallback: Decimal = Decimal("0")) -> Decimal:
    if value is None:
        return fallback
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return fallback


def _empty_order_totals() -> dict[str, Decimal]:
    return {
        "sale_amount": Decimal("0"),
        "vat_amount": Decimal("0"),
        "discount_amount": Decimal("0"),
        "total_amount": Decimal("0"),
    }


def _order_totals(rows: list[dict[str, object]]) -> dict[str, Decimal]:
    totals = _empty_order_totals()
    for row in rows:
        for key in totals:
            totals[key] += _decimal(row.get(key))
    return totals


def _client_totals(rows: list[dict[str, object]]) -> dict[str, Decimal]:
    totals = {
        "order_count": Decimal(len(rows)),
        **_empty_order_totals(),
    }
    for row in rows:
        for key in _empty_order_totals():
            totals[key] += _decimal(row.get(key))
    return totals


def _space_totals(rows: list[dict[str, object]]) -> dict[str, Decimal]:
    totals = {
        "order_count": Decimal("0"),
        "occupied_days": Decimal("0"),
        "income_amount": Decimal("0"),
    }
    for row in rows:
        for key in totals:
            totals[key] += _decimal(row.get(key))
    return totals


def _table_value(value: object, value_type: str) -> str:
    if value_type == "money":
        return format_money(value)
    if value_type == "number":
        return f"{_decimal(value):.2f} %"
    if value_type == "integer":
        return str(int(_decimal(value)))
    return str(value or "—")


def _report_slug(mode: str) -> str:
    return {
        "clients": "zvit_klienty",
        "spaces": "zvit_ploshchyny",
    }.get(mode, "zvit_zamovlennia")
