from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from widgets.new_orders_table import NewOrdersTable
from widgets.stat_card import StatCard


class NewOrdersPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setSpacing(22)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Нові замовлення")
        title.setObjectName("pageTitle")

        subtitle = QLabel("Заявки на зворотний зв’язок, що надійшли з сайту")
        subtitle.setObjectName("pageSubtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        stats_grid = QGridLayout()
        stats_grid.setSpacing(20)
        stats_grid.addWidget(StatCard("assignment", "Нові заявки", "0", True), 0, 0)
        stats_grid.addWidget(StatCard("desktop_windows", "Білборд", "0"), 0, 1)
        stats_grid.addWidget(StatCard("grid_view", "LED", "0"), 0, 2)
        stats_grid.addWidget(StatCard("print", "Друк", "0"), 0, 3)

        layout.addLayout(stats_grid)
        layout.addWidget(NewOrdersTable(), 1)

