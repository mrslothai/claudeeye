#!/usr/bin/env python3
"""ClaudeEye v1 — AI assistant with screen vision."""
import sys
import os
from dotenv import load_dotenv

load_dotenv()


def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set in .env file")
        print("Copy .env.example to .env and add your key")
        sys.exit(1)

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from claude_client import ClaudeEyeClient
    from gui import ClaudeEyeWindow
    from tray import create_tray_icon
    from hotkey import start_hotkey_listener

    app = QApplication(sys.argv)
    app.setApplicationName("ClaudeEye")
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray when window closed

    client = ClaudeEyeClient(api_key)
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
