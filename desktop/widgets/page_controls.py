from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from utils.icons import material_icon


class PageHeader(QFrame):
    def __init__(self, title: str, subtitle: str):
        super().__init__()
        self.setObjectName("pageHeader")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("pageSubtitle")
        subtitle_label.setWordWrap(True)

        text_layout.addWidget(title_label)
        text_layout.addWidget(subtitle_label)
        layout.addLayout(text_layout, 1)

        self.actions = QHBoxLayout()
        self.actions.setContentsMargins(0, 0, 0, 0)
        self.actions.setSpacing(12)
        layout.addLayout(self.actions)

    def add_action(self, widget: QWidget) -> None:
        self.actions.addWidget(widget)


class SearchInput(QLineEdit):
    def __init__(self, placeholder: str, min_width: int = 360):
        super().__init__()

        self.setObjectName("searchInput")
        self.setPlaceholderText(placeholder)
        self.setMinimumWidth(min_width)
        self.setClearButtonEnabled(True)
        self.addAction(
            material_icon("search", "#52627A", 21),
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

        object_names = {
            "primary": "primaryButton",
            "filter": "filterButton",
            "danger": "dangerButton",
            "outline": "outlineButton",
        }
        self.setObjectName(object_names.get(button_type, "secondaryButton"))

        icon_color = {
            "primary": "#FFFFFF",
            "danger": "#B42318",
            "outline": "#E85F00",
        }.get(button_type, "#18315C")

        if icon_name is not None:
            self.setIcon(material_icon(icon_name, icon_color, 21))
            self.setIconSize(QSize(21, 21))

        if min_width is not None:
            self.setMinimumWidth(min_width)

        self.setCursor(Qt.CursorShape.PointingHandCursor)


class FilterChip(QPushButton):
    def __init__(self, text: str, value: object):
        super().__init__(text)
        self.value = value
        self.setObjectName("filterChip")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class Toolbar(QFrame):
    def __init__(self, kind: str = "plain"):
        super().__init__()
        if kind == "filters":
            self.setObjectName("filterBar")
        elif kind == "actions":
            self.setObjectName("actionBar")

        self._layout = QHBoxLayout()
        margins = (14, 10, 14, 10) if kind != "plain" else (0, 0, 0, 0)
        self._layout.setContentsMargins(*margins)
        self._layout.setSpacing(12)
        self.setLayout(self._layout)

    def add_item(self, widget: QWidget) -> None:
        self._layout.addWidget(widget)

    def add_spacing(self, spacing: int) -> None:
        self._layout.addSpacing(spacing)

    def add_stretch(self) -> None:
        self._layout.addStretch()
