from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class PlaceholderPage(QWidget):
    def __init__(self, title_text: str, subtitle_text: str):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel(title_text)
        title.setObjectName("pageTitle")

        subtitle = QLabel(subtitle_text)
        subtitle.setObjectName("pageSubtitle")

        card = QFrame()
        card.setObjectName("placeholderCard")
        card.setMinimumHeight(220)

        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        message = QLabel("Розділ буде реалізовано на наступному етапі")
        message.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(message)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        layout.addWidget(card)
        layout.addStretch()
