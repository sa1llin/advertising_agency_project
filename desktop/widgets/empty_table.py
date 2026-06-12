from __future__ import annotations

from typing import Any

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
)

STATUS_COLORS = {
    "Нова": ("#EAF3FF", "#1B5FA7"),
    "Нове": ("#EAF3FF", "#1B5FA7"),
    "Оброблена": ("#EAF8EF", "#1F7A3F"),
    "Відхилена": ("#FFF0EF", "#B42318"),
    "У роботі": ("#FFF4E5", "#A65300"),
    "Призупинено": ("#FFF8DC", "#866500"),
    "Завершено": ("#EAF8EF", "#1F7A3F"),
    "Скасовано": ("#F1F3F6", "#5D6878"),
    "Активний": ("#EAF8EF", "#1F7A3F"),
    "Неактивний": ("#F1F3F6", "#5D6878"),
    "Деактивований": ("#F1F3F6", "#5D6878"),
}


class TableModel(QAbstractTableModel):
    def __init__(
        self,
        headers: list[str],
        money_columns: set[int] | None = None,
        center_columns: set[int] | None = None,
    ):
        super().__init__()
        self.headers = headers
        self.rows: list[list[str]] = []
        self.roles: dict[tuple[int, int, int], object] = {}
        self.money_columns = money_columns or set()
        self.center_columns = center_columns or set()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.headers)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        column = index.column()
        if row >= len(self.rows) or column >= len(self.headers):
            return None

        custom = self.roles.get((row, column, int(role)))
        if custom is not None:
            return custom

        value = self.rows[row][column]
        if role == Qt.ItemDataRole.DisplayRole:
            return value
        if role == Qt.ItemDataRole.ToolTipRole and value not in ("", "—"):
            return value
        if role == Qt.ItemDataRole.TextAlignmentRole:
            if column in self.money_columns:
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            if column in self.center_columns:
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        if role == Qt.ItemDataRole.FontRole and column in self.money_columns:
            font = QFont()
            font.setWeight(QFont.Weight.DemiBold)
            return font
        return None

    def setData(
        self,
        index: QModelIndex,
        value: Any,
        role: int = Qt.ItemDataRole.EditRole,
    ) -> bool:
        if not index.isValid():
            return False
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            self.rows[index.row()][index.column()] = str(value)
        else:
            self.roles[(index.row(), index.column(), int(role))] = value
        self.dataChanged.emit(index, index, [role])
        return True

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
            and 0 <= section < len(self.headers)
        ):
            return self.headers[section]
        return None

    def set_rows(self, rows: list[list[object]]) -> None:
        self.beginResetModel()
        self.rows = [
            [str(value) for value in row[: len(self.headers)]]
            + [""] * max(0, len(self.headers) - len(row))
            for row in rows
        ]
        self.roles.clear()
        self.endResetModel()

    def set_columns(
        self,
        headers: list[str],
        money_columns: set[int] | None = None,
        center_columns: set[int] | None = None,
    ) -> None:
        self.beginResetModel()
        self.headers = headers
        self.money_columns = money_columns or set()
        self.center_columns = center_columns or set()
        self.rows = []
        self.roles.clear()
        self.endResetModel()


class StatusBadgeDelegate(QStyledItemDelegate):
    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        text = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        colors = STATUS_COLORS.get(text)
        if colors is None:
            super().paint(painter, option, index)
            return

        background_option = QStyleOptionViewItem(option)
        self.initStyleOption(background_option, index)
        background_option.text = ""
        if option.widget is not None:
            option.widget.style().drawControl(
                QStyle.ControlElement.CE_ItemViewItem,
                background_option,
                painter,
                option.widget,
            )

        font = option.font
        font.setWeight(QFont.Weight.DemiBold)
        metrics = painter.fontMetrics()
        chip_width = min(
            option.rect.width() - 20,
            max(76, metrics.horizontalAdvance(text) + 24),
        )
        chip_rect = option.rect.adjusted(12, 0, 0, 0)
        chip_rect.setWidth(chip_width)
        chip_rect.setHeight(28)
        chip_rect.moveCenter(
            option.rect.center() + (chip_rect.center() - chip_rect.center())
        )
        chip_rect.moveLeft(option.rect.left() + 12)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(colors[0]))
        painter.drawRoundedRect(chip_rect, 10, 10)
        painter.setFont(font)
        painter.setPen(QColor(colors[1]))
        painter.drawText(
            chip_rect,
            Qt.AlignmentFlag.AlignCenter,
            text,
        )
        painter.restore()


class TableItemHandle:
    def __init__(self, table: EmptyTable, row: int, column: int):
        self.table = table
        self.row = row
        self.column = column

    def _index(self) -> QModelIndex:
        return self.table.model().index(self.row, self.column)

    def text(self) -> str:
        return str(self._index().data(Qt.ItemDataRole.DisplayRole) or "")

    def data(self, role: int):
        return self._index().data(role)

    def setData(self, role: int, value: object) -> None:
        self.table.model().setData(self._index(), value, role)

    def setToolTip(self, value: str) -> None:
        self.setData(Qt.ItemDataRole.ToolTipRole, value)


class EmptyTable(QTableView):
    itemSelectionChanged = Signal()
    itemDoubleClicked = Signal(object)

    def __init__(
        self,
        headers: list[str],
        column_widths: list[int] | None = None,
        min_height: int = 430,
        status_columns: list[int] | None = None,
        money_columns: list[int] | None = None,
        center_columns: list[int] | None = None,
        empty_text: str = "Немає даних для відображення",
    ):
        super().__init__()
        self.setObjectName("dataTable")
        self.empty_text = empty_text

        self.source_model = TableModel(
            headers,
            set(money_columns or []),
            set(center_columns or []),
        )
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.source_model)
        self.proxy_model.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setDynamicSortFilter(True)
        self.setModel(self.proxy_model)

        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(56)
        self.horizontalHeader().setMinimumHeight(52)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.setShowGrid(False)
        self.setAlternatingRowColors(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSortingEnabled(True)
        self.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.horizontalScrollBar().setSingleStep(60)
        self.setMouseTracking(True)
        self.setMinimumHeight(min_height)

        if column_widths is not None:
            for index, width in enumerate(column_widths):
                self.setColumnWidth(index, width)

        for column in status_columns or []:
            self.setItemDelegateForColumn(column, StatusBadgeDelegate(self))

        selection_model = self.selectionModel()
        selection_model.selectionChanged.connect(
            lambda selected, deselected: self.itemSelectionChanged.emit()
        )
        self.doubleClicked.connect(
            lambda index: self.itemDoubleClicked.emit(
                TableItemHandle(self, index.row(), index.column())
            )
        )

    def set_rows(self, rows: list[list[object]]) -> None:
        self.clearSelection()
        self.source_model.set_rows(rows)
        self.viewport().update()

    def configure_columns(
        self,
        headers: list[str],
        column_widths: list[int] | None = None,
        money_columns: list[int] | None = None,
        center_columns: list[int] | None = None,
        empty_text: str | None = None,
    ) -> None:
        self.setSortingEnabled(False)
        self.source_model.set_columns(
            headers,
            set(money_columns or []),
            set(center_columns or []),
        )
        if column_widths is not None:
            for index, width in enumerate(column_widths):
                self.setColumnWidth(index, width)
        if empty_text is not None:
            self.empty_text = empty_text
        self.setSortingEnabled(True)
        self.viewport().update()

    def set_row_ids(self, values: list[object], column: int = 0) -> None:
        for row, value in enumerate(values[: self.source_model.rowCount()]):
            index = self.source_model.index(row, column)
            self.source_model.setData(index, value, Qt.ItemDataRole.UserRole)

    def setRowCount(self, count: int) -> None:
        if count <= 0:
            self.set_rows([])
            return
        current = [list(row) for row in self.source_model.rows[:count]]
        while len(current) < count:
            current.append([""] * self.source_model.columnCount())
        self.set_rows(current)

    def rowCount(self) -> int:
        return self.model().rowCount()

    def columnCount(self) -> int:
        return self.model().columnCount()

    def currentRow(self) -> int:
        return self.currentIndex().row()

    def item(self, row: int, column: int) -> TableItemHandle | None:
        if not (0 <= row < self.rowCount() and 0 <= column < self.columnCount()):
            return None
        return TableItemHandle(self, row, column)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self.rowCount() != 0:
            return
        painter = QPainter(self.viewport())
        painter.setPen(QColor("#7B899D"))
        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(
            self.viewport().rect().adjusted(24, 24, -24, -24),
            Qt.AlignmentFlag.AlignCenter,
            self.empty_text,
        )
