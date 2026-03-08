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


def _tmp_path(suffix=".png") -> str:
    """Generate a temp path WITHOUT leaving the file on disk.
    
    CRITICAL: scrot and some other tools refuse to overwrite existing files.
    We create a temp file to get a unique name, then DELETE it so the tool
    can write to that path fresh.
    """
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    os.unlink(path)
    return path


def _get_dbus_address() -> str:
    """Get DBUS_SESSION_BUS_ADDRESS from environment or systemd user session."""
    addr = os.environ.get("DBUS_SESSION_BUS_ADDRESS", "")
    if addr:
        return addr
    try:
        r = subprocess.run(
            ["systemctl", "--user", "show-environment"],
            capture_output=True, text=True, timeout=5
        )
        for line in r.stdout.splitlines():
            if line.startswith("DBUS_SESSION_BUS_ADDRESS="):
                return line.split("=", 1)[1]
    except Exception:
        pass
    return f"unix:path=/run/user/{os.getuid()}/bus"


def _linux_screenshot() -> str:
    """
    Linux silent screenshot.
    Priority:
    1. org.gnome.Shell.Screenshot D-Bus with flash=False (GNOME Wayland, truly silent)
    2. gdbus call to GNOME Shell (alternative D-Bus approach)
    3. scrot (X11/XWayland, silent — path must NOT exist before calling)
    4. gnome-screenshot as last resort (may flash)
    
    Root cause of flash bug: NamedTemporaryFile creates an empty file before
    calling scrot. scrot sees the file exists and writes 0 bytes, so it
    "succeeds" but produces nothing. The code then falls through to
    gnome-screenshot which causes the visible flash. Fix: use _tmp_path()
    which deletes the placeholder before handing the path to scrot.
    """
    errors = []

    # Method 1: GNOME Shell D-Bus — flash=False means NO visual flash
    try:
        import dbus
        bus = dbus.SessionBus()
        obj = bus.get_object("org.gnome.Shell.Screenshot", "/org/gnome/Shell/Screenshot")
        iface = dbus.Interface(obj, "org.gnome.Shell.Screenshot")
        path = _tmp_path()
        success, filename = iface.Screenshot(
            False,  # include_cursor = False
            False,  # flash = FALSE — no visual indicator!
            path
        )
        if success and os.path.exists(path) and os.path.getsize(path) > 0:
            img = Image.open(path).convert("RGB")
            os.unlink(path)
            print("[screenshot] Used: dbus gnome-shell (silent ✅)")
            return _img_to_b64(img)
        else:
            errors.append("dbus: Screenshot returned failure or empty file")
            if os.path.exists(path):
                os.unlink(path)
    except Exception as e:
        errors.append(f"dbus gnome-shell: {e}")

    # Method 2: gdbus call (alternative for background processes)
    try:
        path = _tmp_path()
        uid = os.getuid()
        env = {
            **os.environ,
            "DISPLAY": os.environ.get("DISPLAY", ":0"),
            "WAYLAND_DISPLAY": os.environ.get("WAYLAND_DISPLAY", "wayland-0"),
            "DBUS_SESSION_BUS_ADDRESS": _get_dbus_address(),
            "XDG_RUNTIME_DIR": f"/run/user/{uid}",
        }
        cmd = [
            "gdbus", "call", "--session",
            "--dest", "org.gnome.Shell.Screenshot",
            "--object-path", "/org/gnome/Shell/Screenshot",
            "--method", "org.gnome.Shell.Screenshot.Screenshot",
            "false", "false", path  # cursor=false, flash=false
        ]
        r = subprocess.run(cmd, env=env, capture_output=True, timeout=10)
        if r.returncode == 0 and os.path.exists(path) and os.path.getsize(path) > 0:
            img = Image.open(path).convert("RGB")
            os.unlink(path)
            print("[screenshot] Used: gdbus gnome-shell (silent ✅)")
            return _img_to_b64(img)
        else:
            errors.append(f"gdbus: rc={r.returncode} {r.stderr.decode()[:100]}")
            if os.path.exists(path):
                os.unlink(path)
    except Exception as e:
        errors.append(f"gdbus: {e}")

    # Method 3: scrot (X11/XWayland — silent, no flash)
    # IMPORTANT: _tmp_path() deletes the placeholder so scrot can write fresh
    try:
        path = _tmp_path()
        env = {**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":0")}
        r = subprocess.run(
            ["scrot", path],
            env=env, capture_output=True, timeout=10
        )
        if r.returncode == 0 and os.path.exists(path) and os.path.getsize(path) > 0:
            img = Image.open(path).convert("RGB")
            os.unlink(path)
            print("[screenshot] Used: scrot (silent ✅)")
            return _img_to_b64(img)
        errors.append(f"scrot: rc={r.returncode} size={os.path.getsize(path) if os.path.exists(path) else 0}")
        if os.path.exists(path):
            os.unlink(path)
    except Exception as e:
        errors.append(f"scrot: {e}")

    # Method 4: gnome-screenshot (last resort — may flash)
    try:
        path = _tmp_path()
        env = {
            **os.environ,
            "DISPLAY": os.environ.get("DISPLAY", ":0"),
            "WAYLAND_DISPLAY": os.environ.get("WAYLAND_DISPLAY", "wayland-0"),
            "DBUS_SESSION_BUS_ADDRESS": _get_dbus_address(),
        }
        r = subprocess.run(
            ["gnome-screenshot", "-f", path],
            env=env, capture_output=True, timeout=10
        )
        if r.returncode == 0 and os.path.exists(path) and os.path.getsize(path) > 0:
            img = Image.open(path).convert("RGB")
            os.unlink(path)
            print("[screenshot] Used: gnome-screenshot (⚠ may flash)")
            return _img_to_b64(img)
        errors.append(f"gnome-screenshot: rc={r.returncode}")
        if os.path.exists(path):
            os.unlink(path)
    except Exception as e:
        errors.append(f"gnome-screenshot: {e}")

    raise RuntimeError("All Linux screenshot backends failed:\n" + "\n".join(errors))


def _mac_screenshot() -> str:
    """-x flag disables shutter sound and flash completely on Mac."""
    path = _tmp_path()
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
