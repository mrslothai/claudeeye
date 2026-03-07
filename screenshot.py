"""Screen capture using mss with fallbacks."""
import mss
import base64
import io
import os
import subprocess
import tempfile
from PIL import Image


def _try_mss(monitor_idx: int = 1, max_width: int = 1920) -> str:
    """Try capturing via mss."""
    with mss.mss() as sct:
        monitor = sct.monitors[monitor_idx] if monitor_idx < len(sct.monitors) else sct.monitors[1]
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        if img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return base64.standard_b64encode(buffer.getvalue()).decode("utf-8")


def _try_gnome_screenshot() -> str:
    """Try capturing via gnome-screenshot CLI."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name
    try:
        env = {**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":0")}
        subprocess.run(
            ["gnome-screenshot", "-f", path],
            capture_output=True, env=env, timeout=5, check=True
        )
        img = Image.open(path).convert("RGB")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return base64.standard_b64encode(buffer.getvalue()).decode("utf-8")
    finally:
        if os.path.exists(path):
            os.unlink(path)


def _try_scrot() -> str:
    """Try capturing via scrot."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name
    try:
        env = {**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":0")}
        subprocess.run(
            ["scrot", path],
            capture_output=True, env=env, timeout=5, check=True
        )
        img = Image.open(path).convert("RGB")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return base64.standard_b64encode(buffer.getvalue()).decode("utf-8")
    finally:
        if os.path.exists(path):
            os.unlink(path)


def capture_screen(monitor_idx: int = 1, max_width: int = 1920) -> str:
    """Capture screen and return base64 encoded JPEG.
    
    Tries multiple backends: mss → gnome-screenshot → scrot.
    Raises RuntimeError if all fail.
    """
    errors = []
    for backend_name, backend_fn in [
        ("mss", lambda: _try_mss(monitor_idx, max_width)),
        ("gnome-screenshot", _try_gnome_screenshot),
        ("scrot", _try_scrot),
    ]:
        try:
            return backend_fn()
        except Exception as e:
            errors.append(f"{backend_name}: {e}")
    raise RuntimeError("All screenshot backends failed:\n" + "\n".join(errors))


def capture_region(x: int, y: int, width: int, height: int) -> str:
    """Capture a specific region of the screen."""
    with mss.mss() as sct:
        region = {"top": y, "left": x, "width": width, "height": height}
        screenshot = sct.grab(region)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return base64.standard_b64encode(buffer.getvalue()).decode("utf-8")
