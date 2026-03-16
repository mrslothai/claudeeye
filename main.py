#!/usr/bin/env python3
"""ClaudeEye v1 — AI assistant with screen vision."""
import sys
import os
import signal


def main():
    # No API key needed — ClaudeEye uses your claude CLI (Claude Max plan)
    # Make sure claude CLI is installed and logged in: claude /login

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt, QTimer
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

    # Start global hotkey listener (returns listener for cleanup)
    hotkey_listener = start_hotkey_listener(toggle_window)

    # Proper shutdown function
    def shutdown():
        """Clean shutdown — stop hotkey listener, hide tray, quit app."""
        try:
            if hotkey_listener:
                hotkey_listener.stop()
        except Exception:
            pass
        try:
            tray.hide()
        except Exception:
            pass
        app.quit()

    # Handle Ctrl+C (SIGINT) and SIGTERM properly
    def handle_signal(signum, frame):
        shutdown()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Allow Python signal handlers to run (Qt blocks them otherwise)
    # Use a QTimer to periodically let Python handle signals
    timer = QTimer()
    timer.timeout.connect(lambda: None)  # No-op, just lets Python event loop run
    timer.start(200)  # every 200ms

    # Connect app aboutToQuit signal for cleanup
    app.aboutToQuit.connect(shutdown)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
