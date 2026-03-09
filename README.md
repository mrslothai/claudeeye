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

## Install

```bash
pip install git+https://github.com/mrslothai/claudeeye.git
```

## Setup

```bash
# Create .env file with your Anthropic API key
echo "ANTHROPIC_API_KEY=your_key_here" > .env
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

## Platform Support

| Platform | Screenshot | Status |
|----------|-----------|--------|
| Linux (GNOME/Wayland) | scrot (silent) | ✅ Tested |
| Mac | screencapture -x | ✅ Should work |
| Windows | PIL ImageGrab | ✅ Should work |

## Use cases

- Debug code errors without copy-pasting
- Get help on AWS console, Vercel, any web UI
- Explain what's on your screen to Claude
- Fix terminal errors instantly

---
Built by [@rajeshchityal](https://instagram.com/therajeshchityal)
