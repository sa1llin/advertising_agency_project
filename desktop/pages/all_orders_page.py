from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from widgets.empty_table import EmptyTable
from widgets.page_controls import SearchInput, Toolbar, ToolbarButton


class AllOrdersPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setSpacing(22)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Усі замовлення")
        title.setObjectName("pageTitle")

        subtitle = QLabel("База замовлень рекламного агентства")
        subtitle.setObjectName("pageSubtitle")

        toolbar = Toolbar()
        toolbar.add_item(SearchInput("Пошук", 300))
        toolbar.add_item(ToolbarButton("Статус", "keyboard_arrow_down", "filter", 100))
        toolbar.add_item(ToolbarButton("Період", "calendar_month", "filter", 135))
        toolbar.add_stretch()
        toolbar.add_item(ToolbarButton("Редагувати", "edit", "secondary", 135))
        toolbar.add_item(ToolbarButton("Видалити", "delete", "secondary", 125))
        toolbar.add_item(ToolbarButton("Друк", "print", "secondary", 105))
        toolbar.add_item(ToolbarButton("Створити нове замовлення", "add", "primary", 230))

        table = EmptyTable(
            headers=[
                "Номер замовлення",
                "Тип продукції",
                "Дата",
                "Клієнт",
                "Статус замовлення",
                "Сума замовлення",
                "Менеджер",
            ],
            column_widths=[165, 165, 175, 210, 175, 165, 210],
        )

        empty_hint = QLabel("Дані замовлень будуть завантажуватися з бази даних після підключення API.")
        empty_hint.setObjectName("emptyTableHint")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(toolbar)
        layout.addWidget(table, 1)
        layout.addWidget(empty_hint)
