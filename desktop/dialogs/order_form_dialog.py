from datetime import date, timedelta
from decimal import Decimal

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from styles import DIALOG_STYLE
from utils.display import display_client_name


ORDER_TYPES = [
    ("Білборд", "billboard"),
    ("LED-екран", "led"),
    ("Друкована продукція", "printing"),
]

ORDER_STATUSES = [
    ("Нове", "new"),
    ("У роботі", "in_progress"),
    ("Призупинено", "paused"),
    ("Завершено", "completed"),
    ("Скасовано", "cancelled"),
]


class SegmentEditor(QFrame):
    def __init__(
        self,
        order_type: str,
        catalog: dict[str, object],
        on_changed,
        parent: QWidget | None = None,
        data: dict[str, object] | None = None,
    ):
        super().__init__(parent)
        self.order_type = order_type
        self.catalog = catalog
        self.data = data or {}
        self.on_changed = on_changed
        self.setObjectName("segmentCard")

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)

        title = QLabel(
            "Період та рекламна площина"
            if order_type in ("billboard", "led")
            else "Параметри друкованої продукції"
        )
        title.setObjectName("sectionTitle")
        root.addWidget(title)

        form = QGridLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(12)
        form.setColumnStretch(1, 1)
        form.setColumnStretch(3, 1)

        self.space_combo = QComboBox()
        self.size_label = QLabel("—")
        self.size_label.setObjectName("cardValue")
        self.period_start = _date_edit()
        self.period_end = _date_edit()
        self.period_end.setDate(QDate.currentDate().addDays(7))
        self.need_printing = QCheckBox("Потрібен друк плаката")
        self.video_seconds = QSpinBox()
        self.video_seconds.setRange(1, 600)
        self.video_seconds.setValue(10)
        self.impressions_per_day = QSpinBox()
        self.impressions_per_day.setRange(1, 100_000)
        self.impressions_per_day.setValue(100)

        self.product_type = QComboBox()
        self.custom_product_name = QLineEdit()
        self.custom_product_name.setPlaceholderText("Вкажіть назву продукції")
        self.material = QComboBox()
        self.size = QComboBox()
        self.color = QComboBox()
        self.quantity = QSpinBox()
        self.quantity.setRange(1, 1_000_000)
        self.quantity.setValue(1)

        if order_type in ("billboard", "led"):
            self._fill_spaces()
            _add_wide_row(form, 0, "Адреса площини *", self.space_combo)
            _add_grid_field(form, 1, 0, "Розмір із БД", self.size_label)
            _add_grid_field(form, 1, 2, "Початок *", self.period_start)
            _add_grid_field(form, 2, 0, "Завершення *", self.period_end)
            if order_type == "billboard":
                form.addWidget(QLabel("Додаткова послуга"), 2, 2)
                form.addWidget(self.need_printing, 2, 3)
            else:
                _add_grid_field(
                    form,
                    2,
                    2,
                    "Тривалість ролика, с *",
                    self.video_seconds,
                )
                _add_grid_field(
                    form,
                    3,
                    0,
                    "Показів на день *",
                    self.impressions_per_day,
                )
        else:
            self._fill_price_combo(self.product_type, "print_product")
            self._fill_price_combo(self.material, "print_material")
            self._fill_price_combo(self.size, "print_size")
            self._fill_price_combo(self.color, "print_color")
            _add_grid_field(form, 0, 0, "Тип продукції *", self.product_type)
            _add_grid_field(form, 0, 2, "Кількість *", self.quantity)
            _add_wide_row(form, 1, "Назва іншої продукції", self.custom_product_name)
            _add_grid_field(form, 2, 0, "Матеріал *", self.material)
            _add_grid_field(form, 2, 2, "Розмір *", self.size)
            _add_grid_field(form, 3, 0, "Кольоровість *", self.color)

        root.addLayout(form)

        self.error_label = QLabel()
        self.error_label.setObjectName("validationError")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        root.addWidget(self.error_label)

        total_row = QHBoxLayout()
        total_caption = QLabel("Вартість сегмента")
        total_caption.setObjectName("summaryLabel")
        self.segment_total = QLabel("0.00 грн")
        self.segment_total.setObjectName("summaryValue")
        total_row.addWidget(total_caption)
        total_row.addStretch()
        total_row.addWidget(self.segment_total)
        root.addLayout(total_row)

        self._connect_changes()
        self._fill_data()
        self._update_space_size()
        self._update_custom_product()
        self.update_estimate()

    def get_data(self, segment_kind: str = "initial") -> dict[str, object]:
        payload: dict[str, object] = {"segment_kind": segment_kind}
        if self.order_type in ("billboard", "led"):
            payload.update(
                {
                    "advertising_space_id": self.space_combo.currentData(),
                    "period_start": self.period_start.date().toString("yyyy-MM-dd"),
                    "period_end": self.period_end.date().toString("yyyy-MM-dd"),
                    "need_printing": (
                        self.need_printing.isChecked()
                        if self.order_type == "billboard"
                        else False
                    ),
                }
            )
            if self.order_type == "led":
                payload["video_seconds"] = self.video_seconds.value()
                payload["impressions_per_day"] = self.impressions_per_day.value()
        else:
            product_code = self.product_type.currentData()
            payload.update(
                {
                    "product_type": product_code,
                    "product_name": (
                        self.custom_product_name.text().strip()
                        if product_code == "other"
                        else self.product_type.currentText()
                    ),
                    "material_code": self.material.currentData(),
                    "size_code": self.size.currentData(),
                    "color_mode": self.color.currentData(),
                    "quantity": self.quantity.value(),
                }
            )
        return payload

    def estimate(self) -> Decimal:
        if self.order_type == "billboard":
            space = self._selected_space()
            if not space:
                return Decimal("0")
            days = self._days()
            total = Decimal(str(space.get("base_price") or 0)) * days
            if self.need_printing.isChecked():
                price = self._price("billboard_print", str(space.get("size")))
                total += Decimal(str(price.get("amount") or 0)) if price else 0
            return total

        if self.order_type == "led":
            space = self._selected_space()
            if not space:
                return Decimal("0")
            return (
                Decimal(str(space.get("base_price") or 0))
                * self._days()
                * self.video_seconds.value()
                * self.impressions_per_day.value()
            )

        quantity = self.quantity.value()
        values = [
            self._combo_amount(self.product_type, "print_product"),
            self._combo_amount(self.material, "print_material"),
            self._combo_amount(self.size, "print_size"),
            self._combo_amount(self.color, "print_color"),
        ]
        return sum(values, Decimal("0")) * quantity

    def update_estimate(self) -> None:
        self.segment_total.setText(_money_text(self.estimate()))
        self.on_changed()

    def set_default_period(
        self,
        start: date,
        end: date,
        space_id: int | None = None,
    ) -> None:
        self.period_start.setDate(_qdate(start))
        self.period_end.setDate(_qdate(end))
        if space_id is not None:
            _set_combo_data(self.space_combo, space_id)

    def set_error(self, message: str | None) -> None:
        self.error_label.setText(message or "")
        self.error_label.setVisible(bool(message))

    def clear_field_errors(self) -> None:
        self.set_error(None)
        for field in (
            self.space_combo,
            self.period_start,
            self.period_end,
            self.custom_product_name,
        ):
            _mark_error(field, False)

    def _fill_spaces(self) -> None:
        for space in self.catalog.get("advertising_spaces", []):
            if (
                isinstance(space, dict)
                and space.get("space_type") == self.order_type
                and space.get("is_active", True)
            ):
                self.space_combo.addItem(
                    f"{space.get('location')} ({space.get('size') or 'розмір не вказано'})",
                    space.get("id"),
                )

    def _fill_price_combo(self, combo: QComboBox, category: str) -> None:
        for item in self.catalog.get("pricing_items", []):
            if (
                isinstance(item, dict)
                and item.get("category") == category
                and item.get("is_active", True)
            ):
                combo.addItem(str(item.get("label")), item.get("code"))

    def _fill_data(self) -> None:
        if not self.data:
            return
        _set_combo_data(self.space_combo, self.data.get("advertising_space_id"))
        _set_date(self.period_start, self.data.get("period_start"))
        _set_date(self.period_end, self.data.get("period_end"))
        self.need_printing.setChecked(bool(self.data.get("need_printing")))
        self.video_seconds.setValue(int(self.data.get("video_seconds") or 10))
        self.impressions_per_day.setValue(
            int(self.data.get("impressions_per_day") or 100)
        )
        _set_combo_data(self.product_type, self.data.get("product_type"))
        self.custom_product_name.setText(str(self.data.get("product_name") or ""))
        _set_combo_data(self.material, self.data.get("material_code"))
        _set_combo_data(self.size, self.data.get("size_code"))
        _set_combo_data(self.color, self.data.get("color_mode"))
        self.quantity.setValue(int(self.data.get("quantity") or 1))

    def _connect_changes(self) -> None:
        self.space_combo.currentIndexChanged.connect(self._update_space_size)
        self.space_combo.currentIndexChanged.connect(self.update_estimate)
        self.period_start.dateChanged.connect(self.update_estimate)
        self.period_end.dateChanged.connect(self.update_estimate)
        self.need_printing.toggled.connect(self.update_estimate)
        self.video_seconds.valueChanged.connect(self.update_estimate)
        self.impressions_per_day.valueChanged.connect(self.update_estimate)
        self.product_type.currentIndexChanged.connect(self._update_custom_product)
        self.product_type.currentIndexChanged.connect(self.update_estimate)
        self.material.currentIndexChanged.connect(self.update_estimate)
        self.size.currentIndexChanged.connect(self.update_estimate)
        self.color.currentIndexChanged.connect(self.update_estimate)
        self.quantity.valueChanged.connect(self.update_estimate)

    def _update_space_size(self) -> None:
        space = self._selected_space()
        self.size_label.setText(str(space.get("size") or "—") if space else "—")

    def _update_custom_product(self) -> None:
        self.custom_product_name.setVisible(
            self.product_type.currentData() == "other"
        )

    def _selected_space(self) -> dict[str, object] | None:
        space_id = self.space_combo.currentData()
        return next(
            (
                space
                for space in self.catalog.get("advertising_spaces", [])
                if isinstance(space, dict) and space.get("id") == space_id
            ),
            None,
        )

    def _price(self, category: str, code: str) -> dict[str, object] | None:
        return next(
            (
                item
                for item in self.catalog.get("pricing_items", [])
                if isinstance(item, dict)
                and item.get("category") == category
                and item.get("code") == code
            ),
            None,
        )

    def _combo_amount(self, combo: QComboBox, category: str) -> Decimal:
        code = combo.currentData()
        for item in self.catalog.get("pricing_items", []):
            if (
                isinstance(item, dict)
                and item.get("category") == category
                and item.get("code") == code
            ):
                return Decimal(str(item.get("amount") or 0))
        return Decimal("0")

    def _days(self) -> int:
        return max(
            self.period_start.date().daysTo(self.period_end.date()) + 1,
            0,
        )


class OrderFormDialog(QDialog):
    def __init__(
        self,
        clients: list[dict[str, object]],
        managers: list[dict[str, object]],
        user_role: str,
        catalog: dict[str, object] | None = None,
        parent: QWidget | None = None,
        order: dict[str, object] | None = None,
        prolong_only: bool = False,
    ):
        super().__init__(parent)
        self.order = order or {}
        self.user_role = user_role
        self.catalog = catalog or {"advertising_spaces": [], "pricing_items": []}
        self.is_editing = order is not None and not prolong_only
        self.prolong_only = prolong_only
        self.segment_editors: list[SegmentEditor] = []
        self._filling = True

        self.setWindowTitle(
            "Пролонгація замовлення"
            if prolong_only
            else ("Редагування замовлення" if order else "Нове замовлення")
        )
        self.setMinimumSize(880, 720)
        self.resize(980, 820)
        self.setStyleSheet(DIALOG_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(28, 24, 28, 16)
        header_layout.setSpacing(6)

        title = QLabel(self.windowTitle())
        title.setObjectName("dialogTitle")
        hint = QLabel(
            "Ціни завантажені з БД. Сервер повторно перевірить і перерахує "
            "вартість перед збереженням."
        )
        hint.setObjectName("dialogHint")
        hint.setWordWrap(True)
        header_layout.addWidget(title)
        header_layout.addWidget(hint)
        root.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        form_content = QWidget()
        self.form_layout = QVBoxLayout(form_content)
        self.form_layout.setContentsMargins(28, 8, 28, 24)
        self.form_layout.setSpacing(18)
        scroll.setWidget(form_content)
        root.addWidget(scroll, 1)

        self.client_combo = QComboBox()
        for client in sorted(clients, key=display_client_name):
            if isinstance(client.get("id"), int):
                self.client_combo.addItem(display_client_name(client), client["id"])

        self.manager_combo = QComboBox()
        self.manager_combo.addItem("Оберіть менеджера", None)
        current_manager_id = self.order.get("manager_id")
        for manager in managers:
            manager_id = manager.get("id")
            if isinstance(manager_id, int) and (
                manager.get("is_active", True) or manager_id == current_manager_id
            ):
                suffix = "" if manager.get("is_active", True) else " (неактивний)"
                self.manager_combo.addItem(
                    f"{manager.get('full_name') or manager.get('username')}{suffix}",
                    manager_id,
                )

        self.order_type = QComboBox()
        for label, value in ORDER_TYPES:
            self.order_type.addItem(label, value)
        self.status = QComboBox()
        for label, value in ORDER_STATUSES:
            self.status.addItem(label, value)

        basic_section, basic_layout = _form_section(
            "Основна інформація",
            "Клієнт, відповідальний менеджер, тип послуги та поточний статус.",
        )
        basic_grid = QGridLayout()
        basic_grid.setHorizontalSpacing(18)
        basic_grid.setVerticalSpacing(12)
        basic_grid.setColumnStretch(1, 1)
        basic_grid.setColumnStretch(3, 1)
        _add_wide_row(basic_grid, 0, "Клієнт *", self.client_combo)
        row = 1
        if user_role == "admin":
            _add_grid_field(
                basic_grid,
                row,
                0,
                "Менеджер *",
                self.manager_combo,
            )
            _add_grid_field(
                basic_grid,
                row,
                2,
                "Тип послуги *",
                self.order_type,
            )
            row += 1
        else:
            _add_wide_row(basic_grid, row, "Тип послуги *", self.order_type)
            row += 1
        if not prolong_only:
            _add_grid_field(basic_grid, row, 0, "Статус *", self.status)
        basic_layout.addLayout(basic_grid)
        self.form_layout.addWidget(basic_section)

        segments_section, segments_layout = _form_section(
            "Періоди та адреси",
            "Для перехідного періоду додайте окремий сегмент на кожен місяць або адресу.",
        )
        segment_toolbar = QHBoxLayout()
        segment_toolbar.addStretch()
        self.remove_segment_button = QPushButton("Видалити останній")
        self.remove_segment_button.setObjectName("dangerButton")
        self.add_segment_button = QPushButton("+ Додати період / адресу")
        self.add_segment_button.setObjectName("outlineButton")
        self.remove_segment_button.clicked.connect(self.remove_last_segment)
        self.add_segment_button.clicked.connect(self.add_segment)
        segment_toolbar.addWidget(self.remove_segment_button)
        segment_toolbar.addWidget(self.add_segment_button)
        segments_layout.addLayout(segment_toolbar)

        self.segment_container = QWidget()
        self.segment_layout = QVBoxLayout(self.segment_container)
        self.segment_layout.setContentsMargins(0, 0, 0, 0)
        self.segment_layout.setSpacing(12)
        self.segment_layout.addStretch()
        segments_layout.addWidget(self.segment_container)
        self.form_layout.addWidget(segments_section)

        finance_section, finance_layout = _form_section(
            "Фінансовий розрахунок",
            "База розраховується з тарифів у БД; знижка та ПДВ застосовуються до всього замовлення.",
        )
        finance_grid = QGridLayout()
        finance_grid.setHorizontalSpacing(18)
        finance_grid.setVerticalSpacing(12)
        finance_grid.setColumnStretch(1, 1)
        finance_grid.setColumnStretch(3, 1)
        self.vat_rate = _percent_spin(20)
        self.discount_rate = _percent_spin(0)
        _add_grid_field(finance_grid, 0, 0, "ПДВ, %", self.vat_rate)
        _add_grid_field(finance_grid, 0, 2, "Знижка, %", self.discount_rate)
        self.comment = QTextEdit()
        self.comment.setPlaceholderText("Додаткова інформація для менеджера")
        self.comment.setMaximumHeight(90)
        if not prolong_only:
            finance_grid.addWidget(QLabel("Коментар"), 1, 0)
            finance_grid.addWidget(self.comment, 1, 1, 1, 3)
        finance_layout.addLayout(finance_grid)
        self.form_layout.addWidget(finance_section)

        summary = QFrame()
        summary.setObjectName("summaryCard")
        summary_layout = QGridLayout(summary)
        summary_layout.setContentsMargins(20, 18, 20, 18)
        summary_layout.setHorizontalSpacing(24)
        summary_layout.setVerticalSpacing(8)

        self.subtotal_value = _summary_value()
        self.discount_value = _summary_value()
        self.vat_value = _summary_value()
        self.total_value = QLabel("0.00 грн")
        self.total_value.setObjectName("totalValue")
        self.total_preview = self.total_value
        _add_summary_item(summary_layout, 0, "База", self.subtotal_value)
        _add_summary_item(summary_layout, 1, "Знижка", self.discount_value)
        _add_summary_item(summary_layout, 2, "ПДВ", self.vat_value)
        total_label = QLabel("Разом")
        total_label.setObjectName("totalLabel")
        summary_layout.addWidget(total_label, 0, 6)
        summary_layout.addWidget(self.total_value, 1, 6)
        summary_layout.setColumnStretch(5, 1)
        self.form_layout.addWidget(summary)

        self.validation_label = QLabel()
        self.validation_label.setObjectName("validationError")
        self.validation_label.setWordWrap(True)
        self.validation_label.hide()
        self.form_layout.addWidget(self.validation_label)

        footer = QFrame()
        footer.setObjectName("dialogFooter")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(28, 16, 28, 18)
        footer_layout.setSpacing(12)
        footer_layout.addStretch()

        cancel_button = QPushButton("Скасувати")
        save_button = QPushButton(
            "Пролонгувати" if prolong_only else "Зберегти"
        )
        save_button.setObjectName("dialogPrimary")
        cancel_button.clicked.connect(self.reject)
        save_button.clicked.connect(self._validate_and_accept)
        footer_layout.addWidget(cancel_button)
        footer_layout.addWidget(save_button)
        root.addWidget(footer)

        self.order_type.currentIndexChanged.connect(self._type_changed)
        self.vat_rate.valueChanged.connect(self._update_total_preview)
        self.discount_rate.valueChanged.connect(self._update_total_preview)

        self._fill_order()
        self._build_initial_segments()
        self._filling = False
        self._update_segment_buttons()
        self._update_total_preview()

    def get_data(self) -> dict[str, object]:
        segment_kind = "extension" if self.prolong_only else "initial"
        segments = [
            editor.get_data(
                str(editor.data.get("segment_kind") or segment_kind)
                if not self.prolong_only
                else "extension"
            )
            for editor in self.segment_editors
        ]
        if self.prolong_only:
            return {"segments": segments}

        payload: dict[str, object] = {
            "client_id": self.client_combo.currentData(),
            "order_type": self.order_type.currentData(),
            "status": self.status.currentData(),
            "vat_rate": f"{self.vat_rate.value():.2f}",
            "discount_rate": f"{self.discount_rate.value():.2f}",
            "comment": self.comment.toPlainText().strip() or None,
            "segments": segments,
        }
        if self.user_role == "admin":
            payload["manager_id"] = self.manager_combo.currentData()
        return payload

    def add_segment(
        self,
        data: dict[str, object] | None = None,
    ) -> None:
        editor = SegmentEditor(
            str(self.order_type.currentData()),
            self.catalog,
            self._update_total_preview,
            self.segment_container,
            data,
        )
        self.segment_editors.append(editor)
        self.segment_layout.insertWidget(self.segment_layout.count() - 1, editor)

        if self.prolong_only and not data:
            start, end, space_id = self._extension_defaults()
            editor.set_default_period(start, end, space_id)
        self._update_segment_buttons()
        self._update_total_preview()

    def remove_last_segment(self) -> None:
        if len(self.segment_editors) <= 1:
            return
        editor = self.segment_editors.pop()
        editor.deleteLater()
        self._update_segment_buttons()
        self._update_total_preview()

    def _fill_order(self) -> None:
        if not self.order:
            return
        _set_combo_data(self.client_combo, self.order.get("client_id"))
        _set_combo_data(self.manager_combo, self.order.get("manager_id"))
        _set_combo_data(self.order_type, self.order.get("order_type"))
        _set_combo_data(self.status, self.order.get("status"))
        self.vat_rate.setValue(float(self.order.get("vat_rate") or 20))
        self.discount_rate.setValue(float(self.order.get("discount_rate") or 0))
        self.comment.setPlainText(str(self.order.get("comment") or ""))
        if self.prolong_only:
            self.client_combo.setEnabled(False)
            self.manager_combo.setEnabled(False)
            self.order_type.setEnabled(False)
            self.vat_rate.setEnabled(False)
            self.discount_rate.setEnabled(False)

    def _build_initial_segments(self) -> None:
        segments = self.order.get("segments")
        if self.prolong_only:
            self.add_segment()
        elif isinstance(segments, list) and segments:
            for segment in segments:
                if isinstance(segment, dict):
                    self.add_segment(segment)
        else:
            self.add_segment(self._legacy_segment())

    def _legacy_segment(self) -> dict[str, object] | None:
        if not self.order:
            return None
        return {
            "period_start": self.order.get("rental_start"),
            "period_end": self.order.get("rental_end"),
            "video_seconds": self.order.get("led_seconds"),
            "product_name": self.order.get("product_name"),
            "material_code": self.order.get("material_type"),
            "size_code": self.order.get("product_size"),
            "quantity": self.order.get("quantity"),
        }

    def _type_changed(self) -> None:
        if self._filling:
            return
        for editor in self.segment_editors:
            editor.deleteLater()
        self.segment_editors.clear()
        self.add_segment()
        self._update_segment_buttons()

    def _update_segment_buttons(self) -> None:
        multiple_allowed = self.order_type.currentData() in ("billboard", "led")
        self.add_segment_button.setVisible(multiple_allowed)
        self.remove_segment_button.setVisible(
            multiple_allowed and len(self.segment_editors) > 1
        )

    def _update_total_preview(self) -> None:
        subtotal = sum(
            (editor.estimate() for editor in self.segment_editors),
            Decimal("0"),
        )
        discount = subtotal * Decimal(str(self.discount_rate.value())) / 100
        after_discount = subtotal - discount
        vat = after_discount * Decimal(str(self.vat_rate.value())) / 100
        total = after_discount + vat
        self.subtotal_value.setText(_money_text(subtotal))
        self.discount_value.setText(_money_text(discount))
        self.vat_value.setText(_money_text(vat))
        self.total_value.setText(_money_text(total))

    def _validate_and_accept(self) -> None:
        errors: list[str] = []
        self.validation_label.hide()
        _mark_error(self.client_combo, False)
        _mark_error(self.manager_combo, False)
        for editor in self.segment_editors:
            editor.clear_field_errors()

        if self.client_combo.currentData() is None:
            errors.append("Оберіть клієнта.")
            _mark_error(self.client_combo, True)
        if self.user_role == "admin" and self.manager_combo.currentData() is None:
            errors.append("Оберіть менеджера.")
            _mark_error(self.manager_combo, True)
        if not self.segment_editors:
            errors.append("Додайте хоча б один сегмент.")

        for index, editor in enumerate(self.segment_editors, start=1):
            data = editor.get_data()
            segment_errors: list[str] = []
            if editor.order_type in ("billboard", "led"):
                if data.get("advertising_space_id") is None:
                    segment_errors.append("оберіть адресу")
                    _mark_error(editor.space_combo, True)
                if editor.period_end.date() < editor.period_start.date():
                    segment_errors.append("перевірте період")
                    _mark_error(editor.period_start, True)
                    _mark_error(editor.period_end, True)
            elif data.get("product_type") == "other" and not data.get("product_name"):
                segment_errors.append("вкажіть назву продукції")
                _mark_error(editor.custom_product_name, True)
            if segment_errors:
                message = f"Сегмент {index}: " + ", ".join(segment_errors) + "."
                errors.append(message)
                editor.set_error(message)

        if errors:
            self.validation_label.setText("\n".join(errors))
            self.validation_label.show()
            return
        self.accept()

    def _extension_defaults(self) -> tuple[date, date, int | None]:
        dated = [
            segment
            for segment in self.order.get("segments", [])
            if isinstance(segment, dict) and segment.get("period_end")
        ]
        if dated:
            last = max(dated, key=lambda item: str(item.get("period_end")))
            last_end = date.fromisoformat(str(last["period_end"])[:10])
            return (
                last_end + timedelta(days=1),
                last_end + timedelta(days=7),
                last.get("advertising_space_id"),
            )
        rental_end = self.order.get("rental_end")
        last_end = (
            date.fromisoformat(str(rental_end)[:10])
            if rental_end
            else date.today()
        )
        return last_end + timedelta(days=1), last_end + timedelta(days=7), None


def _form_section(title: str, hint: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("formSection")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(20, 18, 20, 20)
    layout.setSpacing(12)
    title_label = QLabel(title)
    title_label.setObjectName("sectionTitle")
    hint_label = QLabel(hint)
    hint_label.setObjectName("sectionHint")
    hint_label.setWordWrap(True)
    layout.addWidget(title_label)
    layout.addWidget(hint_label)
    return frame, layout


def _add_wide_row(
    layout: QGridLayout,
    row: int,
    label: str,
    widget: QWidget,
) -> None:
    _allow_widget_shrink(widget)
    layout.addWidget(QLabel(label), row, 0)
    layout.addWidget(widget, row, 1, 1, 3)


def _add_grid_field(
    layout: QGridLayout,
    row: int,
    column: int,
    label: str,
    widget: QWidget,
) -> None:
    _allow_widget_shrink(widget)
    layout.addWidget(QLabel(label), row, column)
    layout.addWidget(widget, row, column + 1)


def _summary_value() -> QLabel:
    label = QLabel("0.00 грн")
    label.setObjectName("summaryValue")
    return label


def _add_summary_item(
    layout: QGridLayout,
    column: int,
    title: str,
    value: QLabel,
) -> None:
    title_label = QLabel(title)
    title_label.setObjectName("summaryLabel")
    grid_column = column * 2
    layout.addWidget(title_label, 0, grid_column)
    layout.addWidget(value, 1, grid_column)


def _date_edit() -> QDateEdit:
    field = QDateEdit(QDate.currentDate())
    field.setCalendarPopup(True)
    field.setDisplayFormat("dd.MM.yyyy")
    return field


def _percent_spin(value: float) -> QDoubleSpinBox:
    field = QDoubleSpinBox()
    field.setRange(0, 100)
    field.setDecimals(2)
    field.setValue(value)
    field.setSuffix(" %")
    field.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
    return field


def _set_combo_data(combo: QComboBox, value: object) -> None:
    index = combo.findData(value)
    if index >= 0:
        combo.setCurrentIndex(index)


def _set_date(field: QDateEdit, value: object) -> None:
    if not value:
        return
    parsed = QDate.fromString(str(value)[:10], "yyyy-MM-dd")
    if parsed.isValid():
        field.setDate(parsed)


def _qdate(value: date) -> QDate:
    return QDate(value.year, value.month, value.day)


def _money_text(value: Decimal) -> str:
    return f"{Decimal(value):,.2f} грн".replace(",", " ")


def _mark_error(widget: QWidget, enabled: bool) -> None:
    widget.setProperty("error", enabled)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def _allow_widget_shrink(widget: QWidget) -> None:
    widget.setSizePolicy(
        QSizePolicy.Policy.Ignored,
        QSizePolicy.Policy.Preferred,
    )
    if isinstance(widget, QComboBox):
        widget.setMinimumContentsLength(10)
        widget.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
