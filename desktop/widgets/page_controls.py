from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget

from utils.icons import material_icon


class SearchInput(QLineEdit):
    def __init__(self, placeholder: str, min_width: int = 360):
        super().__init__()

        self.setObjectName("searchInput")
        self.setPlaceholderText(placeholder)
        self.setMinimumWidth(min_width)
        self.setClearButtonEnabled(True)
        self.addAction(
            material_icon("search", "#102a5e", 22),
            QLineEdit.ActionPosition.LeadingPosition,
        )


class ToolbarButton(QPushButton):
    def __init__(
        self,
        text: str,
        icon_name: str | None = None,
        button_type: str = "secondary",
        min_width: int | None = None,
    ):
        super().__init__(text)

        if button_type == "primary":
            self.setObjectName("primaryButton")
            icon_color = "#ffffff"
        elif button_type == "filter":
            self.setObjectName("filterButton")
            icon_color = "#102a5e"
        else:
            self.setObjectName("secondaryButton")
            icon_color = "#102a5e"

        if icon_name is not None:
            self.setIcon(material_icon(icon_name, icon_color, 22))
            self.setIconSize(QSize(22, 22))

        if min_width is not None:
            self.setMinimumWidth(min_width)

        self.setCursor(Qt.CursorShape.PointingHandCursor)


class Toolbar(QWidget):
    def __init__(self):
        super().__init__()

        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(12)
        self.setLayout(self._layout)

    def add_item(self, widget: QWidget) -> None:
        self._layout.addWidget(widget)

    def add_stretch(self) -> None:
        self._layout.addStretch()
