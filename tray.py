"""System tray icon for ClaudeEye."""
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter
from PyQt6.QtCore import Qt


def create_tray_icon(window, app):
    """Create system tray icon that shows/hides ClaudeEye window."""
    # Create simple purple eye icon programmatically
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    # Eye white
    painter.setBrush(QColor("#7c3aed"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(2, 8, 28, 16)
    # Iris
    painter.setBrush(QColor("white"))
    painter.drawEllipse(10, 11, 12, 10)
    # Pupil
    painter.setBrush(QColor("#7c3aed"))
    painter.drawEllipse(13, 13, 6, 6)
    painter.end()

    tray = QSystemTrayIcon(QIcon(pixmap), app)
    tray.setToolTip("ClaudeEye — Ctrl+Shift+Space to toggle")

    menu = QMenu()
    show_action = menu.addAction("👁 Open ClaudeEye")
    show_action.triggered.connect(window.show)
    show_action.triggered.connect(window.raise_)
    menu.addSeparator()
    quit_action = menu.addAction("Quit")

    def quit_app():
        tray.hide()
        app.quit()

    quit_action.triggered.connect(quit_app)

    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: window.show() if reason == QSystemTrayIcon.ActivationReason.Trigger else None
    )
    tray.show()
    return tray
