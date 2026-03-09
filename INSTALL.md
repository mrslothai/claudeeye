# ClaudeEye Installation Guide

## Prerequisites
- Python 3.9+
- An Anthropic API key (get one at console.anthropic.com)

## Install (all platforms)

```bash
pip install git+https://github.com/mrslothai/claudeeye.git
```

Or clone and install locally:
```bash
git clone https://github.com/mrslothai/claudeeye.git
cd claudeeye
pip install -e .
```

## Setup
Create a `.env` file in the claudeeye folder:
```
ANTHROPIC_API_KEY=your_key_here
```

Or set as environment variable:
```bash
export ANTHROPIC_API_KEY=your_key_here  # Mac/Linux
set ANTHROPIC_API_KEY=your_key_here     # Windows
```

## Run
```bash
claudeeye
```

## Platform Notes

### Mac
- First run: System will ask for **Screen Recording** permission
- Go to: System Preferences → Privacy & Security → Screen Recording → Enable for Terminal/Python
- Hotkey `Ctrl+Shift+Space` works system-wide

### Windows
- Run as normal user (no admin needed)
- Windows Defender may flag pynput — click "Allow"
- Hotkey `Ctrl+Shift+Space` works system-wide

### Linux (GNOME Wayland)
- Install scrot: `sudo apt install scrot`
- Screenshots are silent via scrot
- Hotkey `Ctrl+Shift+Space` works system-wide
