#!/usr/bin/env python3
"""
ClaudeEye Test Suite
Run this to verify your ClaudeEye installation works correctly.
Usage: python3 test_claudeeye.py
"""

import sys
import os
import subprocess
import importlib

PASS = "✅"
FAIL = "❌"
WARN = "⚠️ "

results = []

def check(name, fn):
    try:
        msg = fn()
        print(f"{PASS} {name}: {msg}")
        results.append((True, name))
    except Exception as e:
        print(f"{FAIL} {name}: {e}")
        results.append((False, name))

print("\n🔱 ClaudeEye Test Suite")
print("=" * 40)

# 1. Python version
def test_python():
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 9):
        raise Exception(f"Python 3.9+ required, got {v.major}.{v.minor}")
    return f"Python {v.major}.{v.minor}.{v.micro}"
check("Python version", test_python)

# 2. PyQt6
def test_pyqt6():
    import PyQt6
    return f"PyQt6 {PyQt6.QtCore.PYQT_VERSION_STR}"
check("PyQt6 installed", test_pyqt6)

# 3. Pillow
def test_pillow():
    from PIL import Image
    import PIL
    return f"Pillow {PIL.__version__}"
check("Pillow installed", test_pillow)

# 4. pynput
def test_pynput():
    import pynput
    return "OK"
check("pynput installed", test_pynput)

# 5. requests
def test_requests():
    import requests
    return f"requests {requests.__version__}"
check("requests installed", test_requests)

# 6. Claude CLI
def test_claude_cli():
    r = subprocess.run(["which", "claude"], capture_output=True, text=True)
    if r.returncode != 0:
        raise Exception("claude CLI not found — run: npm install -g @anthropic-ai/claude-code")
    path = r.stdout.strip()
    # Check if logged in
    r2 = subprocess.run(["claude", "-p", "say: OK", "--dangerously-skip-permissions"],
                        capture_output=True, text=True, timeout=15)
    if "not logged in" in r2.stdout.lower() or "not logged in" in r2.stderr.lower():
        raise Exception("Claude CLI not logged in — run: claude /login")
    return f"Found at {path}"
check("Claude CLI", test_claude_cli)

# 7. Screenshot (Mac)
def test_screenshot():
    import tempfile, os
    fd, path = tempfile.mkstemp(suffix='.png')
    os.close(fd)
    os.unlink(path)
    r = subprocess.run(["screencapture", "-x", "-t", "png", path],
                      capture_output=True, timeout=10)
    if r.returncode != 0:
        raise Exception("screencapture failed — grant Screen Recording permission in System Settings")
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        raise Exception("Screenshot empty — grant Screen Recording permission in System Settings → Privacy & Security")
    size = os.path.getsize(path)
    os.unlink(path)
    return f"Screenshot captured ({size:,} bytes)"
check("Screenshot (Screen Recording permission)", test_screenshot)

# 8. ClaudeEye imports
def test_imports():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from screenshot import capture_screen_silent
    from claude_client import ClaudeClient
    return "All core modules importable"
check("ClaudeEye core imports", test_imports)

# 9. End-to-end: screenshot + Claude
def test_e2e():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from screenshot import capture_screen_silent
    from claude_client import ClaudeClient
    
    screenshot = capture_screen_silent()
    if not screenshot or len(screenshot) < 100:
        raise Exception("Screenshot returned empty base64")
    
    client = ClaudeClient()
    response = client.send_message("What color is the background of the screen? Answer in 5 words max.", screenshot)
    if not response or len(response) < 2:
        raise Exception("Claude returned empty response")
    return f"Claude said: '{response[:80]}'"
check("End-to-end (screenshot → Claude)", test_e2e)

# 10. GUI import (don't launch, just import)
def test_gui():
    # Check if display is available
    if sys.platform == "darwin":
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from gui import ClaudeEyeWindow, format_message_html
        # Test format_message_html
        html = format_message_html("Hello **world**\n```python\nprint('hi')\n```", False)
        if "python" not in html:
            raise Exception("Code block rendering broken")
        return "GUI module OK, code blocks rendering OK"
    return "Skipped (non-Mac)"
check("GUI module", test_gui)

# Summary
print("\n" + "=" * 40)
passed = sum(1 for r in results if r[0])
total = len(results)
print(f"\n📊 Results: {passed}/{total} passed")

if passed == total:
    print("\n🎉 All tests passed! ClaudeEye is ready to use.")
    print("   Run: python3 main.py")
    print("   Hotkey: Ctrl+Shift+Space")
else:
    failed = [r[1] for r in results if not r[0]]
    print(f"\n⚠️  Fix these issues:")
    for f in failed:
        print(f"   • {f}")
    print("\nFor help: github.com/mrslothai/claudeeye/issues")
