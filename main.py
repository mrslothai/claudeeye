#!/usr/bin/env python3
"""ClaudeEye v1 — AI assistant with screen vision."""
import sys
import os
from dotenv import load_dotenv

# Load .env from multiple locations — current dir, home dir, ~/.config/claudeeye/
from pathlib import Path
load_dotenv()  # current directory
load_dotenv(Path.home() / ".env")
load_dotenv(Path.home() / ".config" / "claudeeye" / ".env")
load_dotenv(Path.home() / ".claudeeye.env")


def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        config_dir = Path.home() / ".config" / "claudeeye"
        config_dir.mkdir(parents=True, exist_ok=True)
        env_path = config_dir / ".env"
        print("ClaudeEye — First time setup")
        print("=" * 40)
        print("Get your API key at: https://console.anthropic.com")
        print()
        key = input("Enter your Anthropic API key: ").strip()
        if key:
            with open(env_path, "w") as f:
                f.write(f"ANTHROPIC_API_KEY={key}\n")
            os.environ["ANTHROPIC_API_KEY"] = key
            api_key = key
            print(f"✅ Key saved to {env_path}")
            print()
        else:
            print("Error: API key required. Get one at https://console.anthropic.com")
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
