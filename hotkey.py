"""Global hotkey listener for ClaudeEye — Ctrl+Shift+Space to toggle window."""
import threading
from pynput import keyboard

def start_hotkey_listener(toggle_callback):
    """
    Start a background thread listening for Ctrl+Shift+Space.
    Calls toggle_callback() when hotkey is pressed.
    """
    HOTKEY = {keyboard.Key.ctrl_l, keyboard.Key.shift, keyboard.Key.space}
    # Also support right ctrl
    HOTKEY_ALT = {keyboard.Key.ctrl_r, keyboard.Key.shift, keyboard.Key.space}
    current_keys = set()

    def on_press(key):
        current_keys.add(key)
        if (HOTKEY.issubset(current_keys) or HOTKEY_ALT.issubset(current_keys)):
            toggle_callback()

    def on_release(key):
        current_keys.discard(key)

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    thread = threading.Thread(target=listener.start, daemon=True)
    thread.start()
    return listener
