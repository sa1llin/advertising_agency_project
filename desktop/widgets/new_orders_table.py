from PySide6.QtWidgets import QAbstractItemView, QTableWidget


class NewOrdersTable(QTableWidget):
    def __init__(self):
        super().__init__()

        self.setColumnCount(5)
        self.setRowCount(0)
        self.setHorizontalHeaderLabels([
            "Замовник",
            "Дата та час замовлення",
            "Послуга",
            "Статус",
            "Дія",
        ])

        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setAlternatingRowColors(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.horizontalHeader().setStretchLastSection(True)
        self.setColumnWidth(0, 260)
        self.setColumnWidth(1, 250)
        self.setColumnWidth(2, 230)
        self.setColumnWidth(3, 160)
        self.setColumnWidth(4, 230)

        self.setMinimumHeight(430)
