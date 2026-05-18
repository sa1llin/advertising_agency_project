from PySide6.QtWidgets import QAbstractItemView, QTableWidget


class EmptyTable(QTableWidget):
    def __init__(self, headers: list[str], column_widths: list[int] | None = None, min_height: int = 430):
        super().__init__()

        self.setColumnCount(len(headers))
        self.setRowCount(0)
        self.setHorizontalHeaderLabels(headers)

        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setAlternatingRowColors(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.horizontalHeader().setStretchLastSection(True)

        if column_widths is not None:
            for index, width in enumerate(column_widths):
                self.setColumnWidth(index, width)

        self.setMinimumHeight(min_height)
