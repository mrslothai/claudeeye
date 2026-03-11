# ClaudeEye 👁

## No API Key Needed! 🎉
ClaudeEye uses your existing **Claude CLI** installation. If you have Claude Code or Claude Max, you're already good to go.

**Prerequisite:** Claude CLI installed and logged in
```bash
npm install -g @anthropic-ai/claude-code
claude /login
```

> AI assistant that sees your screen. No more screenshots.

Give Claude eyes — every message auto-captures your screen so Claude understands your context without you explaining anything.

## Platform Support

| Platform | Status | Screenshot Method |
|----------|--------|-------------------|
| 🐧 Linux | ✅ Fully supported | scrot / GNOME Shell D-Bus |
| 🍎 Mac | ✅ Fully supported | screencapture (silent) |
| 🪟 Windows | ✅ Supported | PIL ImageGrab |

## Quick Start

### Mac
```bash
# 1. Install Claude CLI first
npm install -g @anthropic-ai/claude-code
claude /login

# 2. Clone and run setup
git clone https://github.com/mrslothai/claudeeye.git
cd claudeeye
chmod +x install_mac.sh && ./install_mac.sh

# 3. Grant permissions when prompted (Screen Recording + Accessibility)

# 4. Run
python3 main.py
```

### Linux
```bash
git clone https://github.com/mrslothai/claudeeye.git
cd claudeeye
pip install -r requirements.txt
python3 main.py
```

### Windows
```bash
git clone https://github.com/mrslothai/claudeeye.git
cd claudeeye
pip install -r requirements.txt
python3 main.py
```

## Install (via pip)

```bash
pip install git+https://github.com/mrslothai/claudeeye.git
```

## Run

```bash
claudeeye
```

## Hotkey

`Ctrl + Shift + Space` — toggle window from anywhere

## How it works

1. Press `Ctrl+Shift+Space` or click tray icon
2. Type your question
3. ClaudeEye silently captures your screen
4. Claude sees what you see and responds

No copy-pasting errors. No manual screenshots. Just ask.

## Use cases

- Debug code errors without copy-pasting
- Get help on AWS console, Vercel, any web UI
- Explain what's on your screen to Claude
- Fix terminal errors instantly

---
Built by [@rajeshchityal](https://instagram.com/therajeshchityal)
