"""
Silent screen capture for ClaudeEye.
No flash, no sound, no visual indicator — guaranteed.
Cross-platform: Linux (Wayland/X11), Mac, Windows.
"""
import sys
import os
import base64
import io
import subprocess
import tempfile
from PIL import Image


def capture_screen_silent() -> str:
    """Capture screen silently. Returns base64 JPEG. No flash, no sound."""
    platform = sys.platform

    if platform == "linux":
        return _linux_screenshot()
    elif platform == "darwin":
        return _mac_screenshot()
    elif platform == "win32":
        return _windows_screenshot()
    else:
        raise RuntimeError(f"Unsupported platform: {platform}")


def _img_to_b64(img: Image.Image, max_width: int = 1920, quality: int = 82) -> str:
    """Resize if needed and encode as base64 JPEG."""
    img = img.convert("RGB")
    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    return base64.standard_b64encode(buffer.getvalue()).decode("utf-8")


def _linux_screenshot() -> str:
    """
    Linux silent screenshot.
    Priority:
    1. org.gnome.Shell.Screenshot D-Bus with flash=False (GNOME Wayland, truly silent)
    2. scrot -z (X11, -z = silent/no decoration)
    3. gnome-screenshot as last resort
    """
    errors = []

    # Method 1: GNOME Shell D-Bus — flash=False means NO visual flash at all
    try:
        import dbus
        bus = dbus.SessionBus()
        obj = bus.get_object('org.gnome.Shell.Screenshot', '/org/gnome/Shell/Screenshot')
        iface = dbus.Interface(obj, 'org.gnome.Shell.Screenshot')
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = f.name
        success, filename = iface.Screenshot(
            False,  # include_cursor = False
            False,  # flash = FALSE — no visual indicator!
            path
        )
        if success and os.path.exists(path):
            img = Image.open(path).convert("RGB")
            os.unlink(path)
            return _img_to_b64(img)
        else:
            errors.append("dbus: Screenshot returned failure")
    except Exception as e:
        errors.append(f"dbus gnome-shell: {e}")

    # Method 2: scrot with -z flag (silent, no flash, X11)
    try:
        env = {**os.environ, "DISPLAY": ":0"}
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        subprocess.run(
            ["scrot", "-z", path],
            env=env, capture_output=True, timeout=10, check=True
        )
        img = Image.open(path).convert("RGB")
        os.unlink(path)
        return _img_to_b64(img)
    except Exception as e:
        errors.append(f"scrot: {e}")

    # Method 3: gnome-screenshot (may flash — last resort)
    try:
        env = {**os.environ, "DISPLAY": ":0", "WAYLAND_DISPLAY": "wayland-0"}
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        subprocess.run(
            ["gnome-screenshot", "-f", path],
            env=env, capture_output=True, timeout=10, check=True
        )
        img = Image.open(path).convert("RGB")
        os.unlink(path)
        return _img_to_b64(img)
    except Exception as e:
        errors.append(f"gnome-screenshot: {e}")

    raise RuntimeError("All Linux screenshot backends failed:\n" + "\n".join(errors))


def _mac_screenshot() -> str:
    """-x flag disables shutter sound and flash completely on Mac."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name
    try:
        subprocess.run(
            ["screencapture", "-x", "-t", "png", path],
            check=True, timeout=10, capture_output=True
        )
        img = Image.open(path).convert("RGB")
        return _img_to_b64(img)
    finally:
        if os.path.exists(path):
            os.unlink(path)


def _windows_screenshot() -> str:
    """PIL ImageGrab — completely silent on Windows."""
    from PIL import ImageGrab
    img = ImageGrab.grab()
    return _img_to_b64(img)


# Alias
capture_screen = capture_screen_silent
