from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from widgets.empty_table import EmptyTable
from widgets.page_controls import SearchInput, Toolbar, ToolbarButton


class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setSpacing(22)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Звіти")
        title.setObjectName("pageTitle")

        subtitle = QLabel("Формування та перегляд звітів по замовленнях рекламного агентства")
        subtitle.setObjectName("pageSubtitle")

        toolbar = Toolbar()
        toolbar.add_item(SearchInput("Пошук за номером замовлення або клієнтом", 410))
        toolbar.add_item(ToolbarButton("Тип продукції", "keyboard_arrow_down", "filter", 170))
        toolbar.add_item(ToolbarButton("Період", "keyboard_arrow_down", "filter", 145))
        toolbar.add_stretch()
        toolbar.add_item(ToolbarButton("Друк", "print", "secondary", 105))
        toolbar.add_item(ToolbarButton("Експорт", "download", "secondary", 130))
        toolbar.add_item(ToolbarButton("Створити звіт", "add_circle", "primary", 180))

        table = EmptyTable(
            headers=[
                "Номер замовлення",
                "Клієнт",
                "Період",
                "Тип продукції",
                "Менеджер",
                "Сума продажу",
                "ПДВ",
                "Знижка",
            ],
            column_widths=[155, 220, 180, 170, 210, 140, 110, 110],
        )

        empty_hint = QLabel("Дані звітів будуть завантажуватися з бази даних після підключення API.")
        empty_hint.setObjectName("emptyTableHint")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(toolbar)
        layout.addWidget(table, 1)
        layout.addWidget(empty_hint)
