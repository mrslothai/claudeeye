"""Global hotkey listener for ClaudeEye — Ctrl+Shift+Space to toggle window."""
from pynput import keyboard

def start_hotkey_listener(toggle_callback):
    """
    Start a background thread listening for Ctrl+Shift+Space.
    Calls toggle_callback() when hotkey is pressed.
    Returns the listener object so caller can stop it during shutdown.
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
    listener.daemon = True  # dies with main thread
    listener.start()
    return listener  # IMPORTANT: return so caller can stop it
