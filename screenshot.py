"""
Silent screen capture for ClaudeEye.
No flash, no sound, no visual indicator.
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
    img = img.convert("RGB")  # ensure no RGBA issues
    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    return base64.standard_b64encode(buffer.getvalue()).decode("utf-8")


def _linux_screenshot() -> str:
    """
    Linux silent screenshot — tries multiple backends in order:
    1. pyscreenshot (Wayland-compatible, truly silent)
    2. gnome-screenshot (works but may flash — last resort)
    """
    errors = []

    # Method 1: pyscreenshot — silent, works on Wayland via gnome-screenshot internally
    # but with DISPLAY set it uses X11 route which is silent
    try:
        import pyscreenshot as ps
        env_display = os.environ.get("DISPLAY", ":0")
        os.environ["DISPLAY"] = env_display
        img = ps.grab()
        return _img_to_b64(img)
    except Exception as e:
        errors.append(f"pyscreenshot: {e}")

    # Method 2: mss (X11 only, fast and silent)
    try:
        import mss
        with mss.mss() as sct:
            shot = sct.grab(sct.monitors[1])
            img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
            return _img_to_b64(img)
    except Exception as e:
        errors.append(f"mss: {e}")

    # Method 3: gnome-screenshot (last resort — may flash on some setups)
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
    """Mac: screencapture -x (the -x flag disables shutter sound completely)."""
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
    """Windows: PIL ImageGrab — completely silent, no visual indicator."""
    from PIL import ImageGrab
    img = ImageGrab.grab()
    return _img_to_b64(img)


# Backward compat alias
capture_screen = capture_screen_silent
