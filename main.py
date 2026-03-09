#!/usr/bin/env python3
"""ClaudeEye v1 — AI assistant with screen vision."""
import sys
import os


def main():
    # No API key needed — ClaudeEye uses your claude CLI (Claude Max plan)
    # Make sure claude CLI is installed and logged in: claude /login

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from claude_client import ClaudeEyeClient
    from gui import ClaudeEyeWindow
    from tray import create_tray_icon
    from hotkey import start_hotkey_listener

    app = QApplication(sys.argv)
    app.setApplicationName("ClaudeEye")
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray when window closed

    client = ClaudeEyeClient()
    window = ClaudeEyeWindow(client)
    window.show()

    tray = create_tray_icon(window, app)

    def toggle_window():
        if window.isVisible():
            window.hide()
        else:
            window.show()
            window.raise_()
            window.activateWindow()

    # Start global hotkey listener
    start_hotkey_listener(toggle_window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
