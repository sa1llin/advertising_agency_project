from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from widgets.empty_table import EmptyTable
from widgets.page_controls import SearchInput, Toolbar, ToolbarButton


class ClientsPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setSpacing(22)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("База клієнтів")
        title.setObjectName("pageTitle")

        subtitle = QLabel("Контакти та реквізити клієнтів рекламного агентства")
        subtitle.setObjectName("pageSubtitle")

        toolbar = Toolbar()
        toolbar.add_item(SearchInput("Пошук за компанією, ФОП, телефоном або email", 500))
        toolbar.add_stretch()
        toolbar.add_item(ToolbarButton("Тип клієнта", "keyboard_arrow_down", "filter", 170))
        toolbar.add_item(ToolbarButton("Місто", "keyboard_arrow_down", "filter", 135))
        toolbar.add_item(ToolbarButton("Створити нового клієнта", "add", "primary", 235))

        table = EmptyTable(
            headers=[
                "Найменування компанії / контактна особа",
                "Телефон",
                "Юридична адреса",
                "Email",
            ],
            column_widths=[390, 200, 390, 240],
        )

        empty_hint = QLabel("Дані клієнтів будуть завантажуватися з бази даних після підключення API.")
        empty_hint.setObjectName("emptyTableHint")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(toolbar)
        layout.addWidget(table, 1)
        layout.addWidget(empty_hint)
