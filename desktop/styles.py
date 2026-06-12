class Theme:
    COLOR_BG = "#F4F7FB"
    COLOR_SURFACE = "#FFFFFF"
    COLOR_NAVY = "#06284A"
    COLOR_TEXT = "#071B3A"
    COLOR_TEXT_MUTED = "#6F7D95"
    COLOR_BORDER = "#DDE5F0"
    COLOR_PRIMARY = "#FF6A00"
    COLOR_PRIMARY_HOVER = "#E85F00"
    COLOR_DANGER = "#C9362B"
    COLOR_DANGER_BG = "#FFF5F4"

    RADIUS_CARD = 16
    RADIUS_BUTTON = 8

    SPACE_8 = 8
    SPACE_12 = 12
    SPACE_16 = 16
    SPACE_24 = 24
    SPACE_32 = 32


AUTH_STYLE = """
    QWidget {
        background-color: #F4F7FB;
        color: #071B3A;
        font-family: "Segoe UI";
    }

    QLabel {
        background: transparent;
    }

    QFrame#loginCard {
        background-color: #FFFFFF;
        border-radius: 20px;
        border: 1px solid #DDE5F0;
    }

    QLabel#brandLabel {
        color: #FF6A00;
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 1px;
    }

    QLabel#authTitle {
        font-size: 30px;
        font-weight: 800;
        color: #071B3A;
    }

    QLabel#authSubtitle {
        font-size: 15px;
        color: #6F7D95;
    }

    QLabel#fieldLabel {
        font-size: 14px;
        font-weight: 700;
        color: #243453;
    }

    QLabel#errorLabel {
        color: #B42318;
        background-color: #FFF5F4;
        border: 1px solid #F4C7C3;
        border-radius: 8px;
        padding: 10px 12px;
        font-size: 13px;
    }

    QLineEdit {
        min-height: 50px;
        border-radius: 8px;
        border: 1px solid #D6DFEC;
        background-color: #FFFFFF;
        padding-left: 14px;
        padding-right: 14px;
        font-size: 15px;
        selection-background-color: #FFDEC7;
    }

    QLineEdit:focus {
        border: 1px solid #FF7A1A;
        background-color: #FFF9F4;
    }

    QLineEdit[error="true"] {
        border: 1px solid #D92D20;
        background-color: #FFF5F4;
    }

    QPushButton#loginButton {
        min-height: 50px;
        border: none;
        border-radius: 8px;
        background-color: #FF6A00;
        color: #FFFFFF;
        font-size: 16px;
        font-weight: 700;
    }

    QPushButton#loginButton:hover {
        background-color: #E85F00;
    }

    QPushButton#loginButton:disabled {
        background-color: #F3F6FA;
        color: #A7B1C2;
        border: 1px solid #E1E7F0;
    }
"""


MAIN_STYLE = """
    QMainWindow {
        background-color: #F4F7FB;
    }

    QWidget {
        font-family: "Segoe UI";
        color: #071B3A;
    }

    QLabel {
        background: transparent;
    }

    QFrame#sidebar {
        background-color: #06284A;
        border: none;
    }

    QLabel#brandMark {
        color: #FFFFFF;
        background-color: #FF6A00;
        border-radius: 10px;
        font-size: 15px;
        font-weight: 900;
        qproperty-alignment: AlignCenter;
    }

    QLabel#appTitle {
        color: #FFFFFF;
        font-size: 16px;
        font-weight: 800;
    }

    QLabel#appSubtitle {
        color: #91A8C4;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
    }

    QLabel#userName {
        color: #FFFFFF;
        font-size: 16px;
        font-weight: 700;
    }

    QLabel#userPosition {
        color: #C6D2E1;
        font-size: 13px;
    }

    QPushButton#navButton {
        min-height: 48px;
        border: none;
        border-radius: 10px;
        padding-left: 16px;
        text-align: left;
        color: #FFFFFF;
        background-color: transparent;
        font-size: 14px;
        font-weight: 600;
    }

    QPushButton#navButton:hover {
        background-color: rgba(255, 255, 255, 0.09);
    }

    QPushButton#navButton[active="true"] {
        background-color: rgba(255, 106, 0, 0.18);
        color: #FF8A38;
        border-left: 4px solid #FF6A00;
    }

    QWidget#content {
        background-color: #F4F7FB;
    }

    QFrame#pageHeader {
        background: transparent;
        border: none;
    }

    QLabel#pageTitle {
        font-size: 30px;
        font-weight: 800;
        color: #071B3A;
    }

    QLabel#pageSubtitle {
        font-size: 15px;
        color: #6F7D95;
    }

    QFrame#filterBar,
    QFrame#actionBar {
        background-color: #FFFFFF;
        border: 1px solid #E1E7F0;
        border-radius: 12px;
    }

    QFrame#actionBar {
        background-color: #F9FBFE;
    }

    QFrame#statCard,
    QFrame#placeholderCard {
        background-color: #FFFFFF;
        border-radius: 16px;
        border: 1px solid #E1E7F0;
    }

    QFrame#statCard:hover {
        border: 1px solid #FFC49B;
        background-color: #FFFDFC;
    }

    QLabel#statIcon {
        background-color: #F3F6FA;
        border-radius: 12px;
        qproperty-alignment: AlignCenter;
    }

    QLabel#statTitle {
        font-size: 14px;
        font-weight: 700;
        color: #52627A;
    }

    QLabel#statValue {
        font-size: 28px;
        font-weight: 800;
        color: #071B3A;
    }

    QLabel#emptyTableHint {
        color: #6F7D95;
        font-size: 13px;
        padding-left: 4px;
    }

    QTableView#dataTable {
        background-color: #FFFFFF;
        alternate-background-color: #FFFFFF;
        border-radius: 14px;
        border: 1px solid #E1E7F0;
        gridline-color: transparent;
        font-size: 14px;
        selection-background-color: #FFF1E8;
        selection-color: #071B3A;
        outline: none;
    }

    QHeaderView::section {
        background-color: #FFFFFF;
        color: #071B3A;
        font-size: 13px;
        font-weight: 700;
        border: none;
        border-bottom: 1px solid #E4EAF3;
        padding: 0 14px;
        height: 52px;
    }

    QTableView#dataTable::item {
        padding: 0 14px;
        border: none;
        border-bottom: 1px solid #EEF2F7;
    }

    QTableView#dataTable::item:hover {
        background-color: #F7FAFD;
    }

    QTableView#dataTable::item:selected {
        background-color: #FFF1E8;
        color: #071B3A;
    }

    QLineEdit#searchInput,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QSpinBox,
    QDoubleSpinBox,
    QTextEdit {
        min-height: 48px;
        border-radius: 8px;
        border: 1px solid #D6DFEC;
        background-color: #FFFFFF;
        padding-left: 12px;
        padding-right: 12px;
        color: #071B3A;
        font-size: 14px;
        selection-background-color: #FFDEC7;
    }

    QTextEdit {
        padding-top: 8px;
        padding-bottom: 8px;
    }

    QLineEdit:focus,
    QComboBox:focus,
    QDateEdit:focus,
    QSpinBox:focus,
    QDoubleSpinBox:focus,
    QTextEdit:focus {
        border: 1px solid #FF7A1A;
        background-color: #FFF9F4;
    }

    QLineEdit[error="true"],
    QComboBox[error="true"],
    QDateEdit[error="true"] {
        border: 1px solid #D92D20;
        background-color: #FFF5F4;
    }

    QLineEdit::placeholder {
        color: #8794A8;
    }

    QComboBox::drop-down,
    QDateEdit::drop-down {
        width: 34px;
        border: none;
    }

    QComboBox QAbstractItemView {
        background-color: #FFFFFF;
        border: 1px solid #DDE5F0;
        selection-background-color: #FFF1E8;
        selection-color: #071B3A;
        padding: 6px;
    }

    QPushButton#filterButton,
    QPushButton#secondaryButton,
    QPushButton#outlineButton {
        min-height: 48px;
        border-radius: 8px;
        border: 1px solid #D6DFEC;
        background-color: #FFFFFF;
        color: #18315C;
        font-size: 14px;
        font-weight: 700;
        padding-left: 16px;
        padding-right: 16px;
        text-align: center;
    }

    QPushButton#filterButton:hover,
    QPushButton#secondaryButton:hover {
        border: 1px solid #FFB27A;
        background-color: #FFF8F3;
    }

    QPushButton#outlineButton {
        color: #E85F00;
        border: 1px solid #FF8A38;
        background-color: #FFFFFF;
    }

    QPushButton#outlineButton:hover {
        background-color: #FFF4EB;
    }

    QPushButton#primaryButton {
        min-height: 50px;
        border: none;
        border-radius: 8px;
        background-color: #FF6A00;
        color: #FFFFFF;
        font-size: 14px;
        font-weight: 800;
        padding-left: 18px;
        padding-right: 18px;
    }

    QPushButton#primaryButton:hover {
        background-color: #E85F00;
    }

    QPushButton#dangerButton {
        min-height: 48px;
        border-radius: 8px;
        border: 1px solid #F2B8B3;
        background-color: #FFF5F4;
        color: #B42318;
        font-size: 14px;
        font-weight: 700;
        padding-left: 16px;
        padding-right: 16px;
    }

    QPushButton#dangerButton:hover {
        background-color: #FEE9E7;
        border-color: #E58B84;
    }

    QPushButton#filterChip {
        min-height: 34px;
        border: 1px solid #DDE5F0;
        border-radius: 17px;
        padding: 0 14px;
        background-color: #FFFFFF;
        color: #52627A;
        font-size: 13px;
        font-weight: 700;
    }

    QPushButton#filterChip:hover {
        border-color: #FFB27A;
        color: #E85F00;
    }

    QPushButton#filterChip:checked {
        border-color: #FF6A00;
        background-color: #FFF1E8;
        color: #C85000;
    }

    QPushButton:disabled,
    QComboBox:disabled,
    QDateEdit:disabled {
        color: #A7B1C2;
        background-color: #F3F6FA;
        border: 1px solid #E1E7F0;
    }

    QCheckBox {
        spacing: 8px;
        color: #34445F;
        font-size: 13px;
    }

    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 1px solid #C7D1DF;
        background-color: #FFFFFF;
    }

    QCheckBox::indicator:checked {
        background-color: #FF6A00;
        border-color: #FF6A00;
    }

    QScrollBar:vertical {
        width: 10px;
        background: transparent;
        margin: 4px 2px;
    }

    QScrollBar::handle:vertical {
        min-height: 32px;
        border-radius: 4px;
        background: #C8D2E0;
    }

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0;
    }

    QScrollBar:horizontal {
        height: 14px;
        background: #EEF2F7;
        margin: 2px 4px;
        border-radius: 6px;
    }

    QScrollBar::handle:horizontal {
        min-width: 64px;
        border-radius: 6px;
        background: #AEBBCD;
    }

    QScrollBar::handle:horizontal:hover {
        background: #8797AD;
    }

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {
        width: 0;
    }
"""


DIALOG_STYLE = """
    QDialog {
        background-color: #F4F7FB;
        color: #071B3A;
        font-family: "Segoe UI";
    }

    QLabel {
        background: transparent;
    }

    QLabel#dialogTitle,
    QLabel#cardTitle {
        color: #071B3A;
        font-size: 24px;
        font-weight: 800;
    }

    QLabel#dialogHint {
        color: #6F7D95;
        font-size: 13px;
    }

    QLabel#sectionTitle {
        color: #071B3A;
        font-size: 16px;
        font-weight: 800;
    }

    QLabel#sectionHint {
        color: #6F7D95;
        font-size: 12px;
    }

    QLabel#validationError {
        color: #B42318;
        background-color: #FFF5F4;
        border: 1px solid #F4C7C3;
        border-radius: 8px;
        padding: 9px 11px;
        font-size: 13px;
    }

    QFrame#formSection,
    QFrame#segmentCard,
    QFrame#summaryCard {
        background-color: #FFFFFF;
        border: 1px solid #DDE5F0;
        border-radius: 14px;
    }

    QFrame#segmentCard {
        background-color: #F9FBFE;
    }

    QFrame#summaryCard {
        background-color: #FFF8F3;
        border-color: #FFD5B8;
    }

    QFrame#dialogFooter {
        background-color: #FFFFFF;
        border-top: 1px solid #DDE5F0;
    }

    QLabel#summaryLabel {
        color: #6F7D95;
        font-size: 13px;
    }

    QLabel#summaryValue {
        color: #071B3A;
        font-size: 14px;
        font-weight: 700;
    }

    QLabel#totalLabel {
        color: #B84900;
        font-size: 14px;
        font-weight: 800;
    }

    QLabel#totalValue {
        color: #C85000;
        font-size: 24px;
        font-weight: 900;
    }

    QLabel#cardValue {
        background-color: #FFFFFF;
        border: 1px solid #E1E7F0;
        border-radius: 8px;
        padding: 9px 11px;
        font-size: 14px;
    }

    QLineEdit,
    QComboBox,
    QDateEdit,
    QSpinBox,
    QDoubleSpinBox,
    QTextEdit {
        min-height: 46px;
        border: 1px solid #D6DFEC;
        border-radius: 8px;
        background-color: #FFFFFF;
        padding-left: 12px;
        padding-right: 12px;
        color: #071B3A;
        font-size: 14px;
        selection-background-color: #FFDEC7;
    }

    QTextEdit {
        padding-top: 8px;
        padding-bottom: 8px;
    }

    QLineEdit:focus,
    QComboBox:focus,
    QDateEdit:focus,
    QSpinBox:focus,
    QDoubleSpinBox:focus,
    QTextEdit:focus {
        border: 1px solid #FF7A1A;
        background-color: #FFF9F4;
    }

    QLineEdit[error="true"],
    QComboBox[error="true"],
    QDateEdit[error="true"] {
        border: 1px solid #D92D20;
        background-color: #FFF5F4;
    }

    QComboBox::drop-down,
    QDateEdit::drop-down {
        width: 34px;
        border: none;
    }

    QCheckBox {
        spacing: 8px;
    }

    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 1px solid #C7D1DF;
        background-color: #FFFFFF;
    }

    QCheckBox::indicator:checked {
        background-color: #FF6A00;
        border-color: #FF6A00;
    }

    QPushButton {
        min-height: 44px;
        min-width: 110px;
        border-radius: 8px;
        border: 1px solid #D6DFEC;
        background-color: #FFFFFF;
        color: #18315C;
        padding: 0 16px;
        font-size: 14px;
        font-weight: 700;
    }

    QPushButton:hover {
        border-color: #FFB27A;
        background-color: #FFF8F3;
    }

    QPushButton#dialogPrimary {
        border: none;
        background-color: #FF6A00;
        color: #FFFFFF;
    }

    QPushButton#dialogPrimary:hover {
        background-color: #E85F00;
    }

    QPushButton#outlineButton {
        color: #E85F00;
        border: 1px solid #FF8A38;
        background-color: #FFFFFF;
    }

    QPushButton#dangerButton {
        color: #B42318;
        border: 1px solid #F2B8B3;
        background-color: #FFF5F4;
    }

    QPushButton:disabled {
        color: #A7B1C2;
        background-color: #F3F6FA;
        border: 1px solid #E1E7F0;
    }

    QScrollArea {
        border: none;
        background: transparent;
    }

    QScrollArea > QWidget > QWidget {
        background: transparent;
    }
"""
