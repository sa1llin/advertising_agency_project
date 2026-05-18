AUTH_STYLE = """
    QWidget {
        background-color: #f4f7fb;
        color: #0b1635;
        font-family: Segoe UI;
    }

    QFrame#loginCard {
        background-color: #ffffff;
        border-radius: 28px;
        border: 1px solid #e6ebf2;
    }

    QLabel#authTitle {
        font-size: 30px;
        font-weight: 800;
        color: #0b1635;
    }

    QLabel#authSubtitle {
        font-size: 16px;
        color: #6b7890;
    }

    QLabel#fieldLabel {
        font-size: 14px;
        font-weight: 600;
        color: #243453;
    }

    QLineEdit {
        min-height: 46px;
        border-radius: 14px;
        border: 1px solid #dbe3ee;
        background-color: #f8fafc;
        padding-left: 16px;
        padding-right: 16px;
        font-size: 15px;
    }

    QLineEdit:focus {
        border: 1px solid #ff6a00;
        background-color: #ffffff;
    }

    QPushButton#loginButton {
        min-height: 48px;
        border-radius: 16px;
        background-color: #ff6a00;
        color: white;
        font-size: 16px;
        font-weight: 700;
    }

    QPushButton#loginButton:hover {
        background-color: #e85f00;
    }

    QLabel#hint {
        color: #7a8699;
        font-size: 13px;
    }
"""

MAIN_STYLE = """
    QMainWindow {
        background-color: #f4f7fb;
    }

    QWidget {
        font-family: Segoe UI;
        color: #0b1635;
    }

    QFrame#sidebar {
        background-color: #001b3a;
        border: none;
    }

    QLabel#appTitle {
        color: white;
        font-size: 19px;
        font-weight: 800;
    }

    QLabel#appSubtitle {
        color: #8ea4c5;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 2px;
    }

    QLabel#userName {
        color: white;
        font-size: 17px;
        font-weight: 700;
    }

    QLabel#userPosition {
        color: #c6d0e0;
        font-size: 14px;
    }

    QPushButton#navButton {
        min-height: 48px;
        border: none;
        border-radius: 12px;
        padding-left: 16px;
        text-align: left;
        color: white;
        background-color: transparent;
        font-size: 15px;
        font-weight: 600;
    }

    QPushButton#navButton:hover {
        background-color: rgba(255, 255, 255, 0.10);
    }

    QPushButton#navButton[active="true"] {
        background-color: rgba(255, 106, 0, 0.18);
        color: #ff7a1a;
        border-left: 4px solid #ff6a00;
    }

    QWidget#content {
        background-color: #f4f7fb;
    }

    QLabel#pageTitle {
        font-size: 30px;
        font-weight: 800;
        color: #0b1635;
    }

    QLabel#pageSubtitle {
        font-size: 16px;
        color: #6b7890;
    }

    QFrame#statCard,
    QFrame#placeholderCard {
        background-color: #ffffff;
        border-radius: 18px;
        border: 1px solid #e7edf5;
    }

    QLabel#statIcon {
        background-color: #f3f5f8;
        border-radius: 14px;
        qproperty-alignment: AlignCenter;
    }

    QLabel#statTitle {
        font-size: 15px;
        font-weight: 700;
        color: #0b1635;
    }

    QLabel#statValue {
        font-size: 30px;
        font-weight: 900;
        color: #0b1635;
    }

    QLabel#emptyTableHint {
        color: #7a8699;
        font-size: 14px;
        padding-left: 6px;
    }

    QTableWidget {
        background-color: #ffffff;
        border-radius: 18px;
        border: 1px solid #e7edf5;
        gridline-color: #e9eef5;
        font-size: 14px;
        selection-background-color: #fff1e8;
        selection-color: #0b1635;
    }

    QHeaderView::section {
        background-color: #ffffff;
        color: #18315c;
        font-size: 14px;
        font-weight: 700;
        border: none;
        border-bottom: 1px solid #e7edf5;
        padding: 12px;
    }

    QTableWidget::item {
        padding: 8px;
        border-bottom: 1px solid #eef2f7;
    }

    QPushButton#actionButton {
        border: none;
        color: #0b2a66;
        background-color: transparent;
        font-size: 14px;
        font-weight: 700;
    }

    QLineEdit#searchInput {
        min-height: 48px;
        border-radius: 8px;
        border: 1px solid #d9e1ec;
        background-color: #ffffff;
        padding-left: 8px;
        padding-right: 12px;
        color: #0b1635;
        font-size: 14px;
    }

    QLineEdit#searchInput:focus {
        border: 1px solid #ff6a00;
    }

    QLineEdit#searchInput::placeholder {
        color: #7a8699;
    }

    QPushButton#filterButton,
    QPushButton#secondaryButton {
        min-height: 48px;
        border-radius: 8px;
        border: 1px solid #d9e1ec;
        background-color: #ffffff;
        color: #102a5e;
        font-size: 14px;
        font-weight: 700;
        padding-left: 14px;
        padding-right: 14px;
        text-align: center;
    }

    QPushButton#filterButton:hover,
    QPushButton#secondaryButton:hover {
        border: 1px solid #ffb27a;
        background-color: #fff8f3;
    }

    QPushButton#primaryButton {
        min-height: 50px;
        border: none;
        border-radius: 8px;
        background-color: #ff5c00;
        color: #ffffff;
        font-size: 14px;
        font-weight: 800;
        padding-left: 16px;
        padding-right: 16px;
    }

    QPushButton#primaryButton:hover {
        background-color: #e85300;
    }

    QPushButton#actionButton:hover {
        color: #ff6a00;
    }
"""
