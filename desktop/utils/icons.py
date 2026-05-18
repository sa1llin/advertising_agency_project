from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer


MATERIAL_ICONS = {
    "assignment": (
        "M19 3h-4.18C14.4 1.84 13.3 1 12 1S9.6 1.84 9.18 3H5c-1.1 "
        "0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z"
        "M12 3c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1z"
        "M14 17H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"
    ),
    "list_alt": (
        "M19 5v14H5V5h14m0-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 "
        "2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z"
        "M14 17H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"
    ),
    "groups": (
        "M12 12.75c1.63 0 3.07.39 4.24.9 1.08.48 1.76 1.56 1.76 2.73V18H6v-1.61"
        "c0-1.18.68-2.26 1.76-2.73 1.17-.52 2.61-.91 4.24-.91z"
        "M4 13c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2z"
        "M20 13c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2z"
        "M12 6c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3z"
    ),
    "bar_chart": "M5 9.2h3V19H5V9.2zM10.6 5h3v14h-3V5zm5.6 8h3v6h-3v-6z",
    "description": (
        "M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6z"
        "M16 18H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"
    ),
    "manage_accounts": (
        "M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5s-3 1.34-3 3 1.34 3 3 3z"
        "M8 11c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5 5 6.34 5 8s1.34 3 3 3z"
        "M8 13c-2.33 0-7 1.17-7 3.5V19h14v-2.5C15 14.17 10.33 13 8 13z"
        "M16 13c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"
    ),
    "history": (
        "M13 3c-4.97 0-9 4.03-9 9H1l4 4.01L9 12H6c0-3.86 3.14-7 7-7s7 "
        "3.14 7 7-3.14 7-7 7c-1.93 0-3.68-.78-4.95-2.05l-1.42 1.42C8.27 "
        "20 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9z"
        "M12 8v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"
    ),
    "logout": (
        "M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5z"
        "M4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"
    ),
    "account_circle": (
        "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"
        "M12 5c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3z"
        "M12 19.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08s5.97 1.09 6 3.08c-1.29 1.94-3.5 3.22-6 3.22z"
    ),
    "desktop_windows": (
        "M20 18c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2H4c-1.1 0-2 .9-2 "
        "2v10c0 1.1.9 2 2 2H0v2h24v-2h-4zM4 6h16v10H4V6z"
    ),
    "grid_view": (
        "M3 5v6h8V5H3zm6 4H5V7h4v2zm-6 10h8v-6H3v6zm2-4h4v2H5v-2z"
        "M13 5v6h8V5h-8zm6 4h-4V7h4v2zm-6 10h8v-6h-8v6zm2-4h4v2h-4v-2z"
    ),
    "print": (
        "M19 8H5c-1.66 0-3 1.34-3 3v6h4v4h12v-4h4v-6c0-1.66-1.34-3-3-3z"
        "M16 19H8v-5h8v5zm3-7c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1z"
        "M18 3H6v4h12V3z"
    ),
}


def material_icon(icon_name: str, color: str = "#ffffff", size: int = 24) -> QIcon:
    path = MATERIAL_ICONS.get(icon_name, MATERIAL_ICONS["assignment"])
    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24">
        <path fill="{color}" d="{path}"/>
    </svg>
    """

    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)


def material_pixmap(icon_name: str, color: str = "#0b1635", size: int = 28) -> QPixmap:
    return material_icon(icon_name, color, size).pixmap(QSize(size, size))
