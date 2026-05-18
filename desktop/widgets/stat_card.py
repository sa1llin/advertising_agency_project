from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from utils.icons import material_pixmap


class StatCard(QFrame):
    def __init__(self, icon_name: str, title: str, value: str, accent: bool = False):
        super().__init__()

        self.setObjectName("statCard")
        self.setMinimumHeight(104)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(18)

        icon_label = QLabel()
        icon_label.setObjectName("statIcon")
        icon_label.setFixedSize(58, 58)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_color = "#ff6a00" if accent else "#0b1635"
        icon_label.setPixmap(material_pixmap(icon_name, icon_color, 30))

        if accent:
            icon_label.setStyleSheet(
                """
                QLabel {
                    background-color: #fff0df;
                    border-radius: 14px;
                }
                """
            )

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setObjectName("statTitle")

        value_label = QLabel(value)
        value_label.setObjectName("statValue")

        if accent:
            value_label.setStyleSheet("color: #ff6a00;")

        text_layout.addWidget(title_label)
        text_layout.addWidget(value_label)

        layout.addWidget(icon_label)
        layout.addLayout(text_layout)
        layout.addStretch()
