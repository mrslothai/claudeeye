# ClaudeEye 👁

AI assistant that sees your screen. No more screenshots.

## Install
```bash
pip install -e .
claudeeye
```

## First run
Copy `.env.example` to `.env` and add your Anthropic API key.

## Platform support
- **Linux** — GNOME Wayland + X11 ✅
- **Mac** — requires Screen Recording permission (prompted on first run) ✅
- **Windows** — works out of the box ✅

## How it works
Click the tray icon → chat window opens → every message auto-captures your screen → Claude sees what you see.

## Usage
- Drag the window by its header to move it anywhere on screen
- Close button (✕) hides to system tray — app keeps running
- Clear button (⟳) resets conversation history
- Press Enter or click ↑ to send a message
