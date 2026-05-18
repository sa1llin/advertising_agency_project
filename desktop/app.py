import sys

from PySide6.QtWidgets import QApplication

from windows.auth_window import AuthWindow


def run_app() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Creative Spark Agency CRM")

    window = AuthWindow()
    window.showMaximized()

    sys.exit(app.exec())
