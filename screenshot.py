"""Cross-platform silent screenshot capture."""
import sys
import os
import base64
import io
import subprocess
import tempfile
from PIL import Image


def capture_screen_silent() -> str:
    """Capture screen silently. Returns base64 JPEG. Works on Linux/Mac/Windows."""
    platform = sys.platform

    if platform == "linux":
        return _linux_screenshot()
    elif platform == "darwin":
        return _mac_screenshot()
    elif platform == "win32":
        return _windows_screenshot()
    else:
        raise RuntimeError(f"Unsupported platform: {platform}")


def _linux_screenshot() -> str:
    """Linux: try D-Bus XDG portal first, fallback to gnome-screenshot."""
    errors = []

    # Method 1: D-Bus org.gnome.Shell.Screenshot (works on GNOME Wayland, silent)
    try:
        import dbus
        bus = dbus.SessionBus()
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = f.name
        shell = bus.get_object('org.gnome.Shell', '/org/gnome/Shell')
        shell_screenshot = dbus.Interface(shell, 'org.gnome.Shell.Screenshot')
        shell_screenshot.Screenshot(False, False, path)  # include_cursor=False, flash=False
        img = Image.open(path).convert('RGB')
        os.unlink(path)
        return _img_to_b64(img)
    except Exception as e:
        errors.append(f"dbus: {e}")

    # Method 2: gnome-screenshot (no sound by default on GNOME)
    try:
        env = {**os.environ, "DISPLAY": ":0", "WAYLAND_DISPLAY": "wayland-0"}
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = f.name
        subprocess.run(["gnome-screenshot", "-f", path], env=env, capture_output=True, timeout=10, check=True)
        img = Image.open(path).convert('RGB')
        os.unlink(path)
        return _img_to_b64(img)
    except Exception as e:
        errors.append(f"gnome-screenshot: {e}")

    # Method 3: scrot (X11, -z = silent)
    try:
        env = {**os.environ, "DISPLAY": ":0"}
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = f.name
        subprocess.run(["scrot", "-z", path], env=env, capture_output=True, timeout=10, check=True)
        img = Image.open(path).convert('RGB')
        os.unlink(path)
        return _img_to_b64(img)
    except Exception as e:
        errors.append(f"scrot: {e}")

    # Method 4: mss fallback
    try:
        import mss
        with mss.mss() as sct:
            screenshot = sct.grab(sct.monitors[1])
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            return _img_to_b64(img)
    except Exception as e:
        errors.append(f"mss: {e}")

    raise RuntimeError("All Linux screenshot backends failed:\n" + "\n".join(errors))


def _mac_screenshot() -> str:
    """Mac: screencapture -x (silent, no shutter sound)."""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        path = f.name
    try:
        subprocess.run(["screencapture", "-x", "-t", "png", path], check=True, timeout=10)
        img = Image.open(path).convert('RGB')
        return _img_to_b64(img)
    finally:
        if os.path.exists(path):
            os.unlink(path)


def _windows_screenshot() -> str:
    """Windows: PIL ImageGrab (silent, no flash)."""
    from PIL import ImageGrab
    img = ImageGrab.grab()
    return _img_to_b64(img)


def _img_to_b64(img: Image.Image, max_width: int = 1920, quality: int = 82) -> str:
    """Resize if needed and encode as base64 JPEG."""
    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    return base64.standard_b64encode(buffer.getvalue()).decode("utf-8")
