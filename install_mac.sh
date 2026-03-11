#!/bin/bash
# ClaudeEye Mac Installer
echo "🔱 ClaudeEye Mac Setup"
echo "====================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Install from https://python.org"
    exit 1
fi

# Check Claude CLI
if ! command -v claude &> /dev/null; then
    echo "❌ Claude CLI not found."
    echo "   Install: npm install -g @anthropic-ai/claude-code"
    echo "   Then run: claude /login"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install pillow pynput PyQt6 requests --quiet

echo ""
echo "⚠️  IMPORTANT: Grant Screen Recording permission"
echo "   1. Open System Settings → Privacy & Security → Screen Recording"
echo "   2. Enable permission for Terminal (or your terminal app)"
echo "   3. Restart Terminal after granting permission"
echo ""
echo "⚠️  IMPORTANT: Grant Accessibility permission (for hotkey)"
echo "   1. Open System Settings → Privacy & Security → Accessibility"
echo "   2. Enable permission for Terminal (or your terminal app)"
echo ""

# Create LaunchAgent for auto-start (optional)
read -p "Start ClaudeEye automatically on login? (y/n): " autostart
if [ "$autostart" = "y" ]; then
    PLIST_DIR="$HOME/Library/LaunchAgents"
    PLIST_FILE="$PLIST_DIR/ai.claudeeye.app.plist"
    mkdir -p "$PLIST_DIR"
    SCRIPT_PATH="$(pwd)/main.py"
    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.claudeeye.app</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(which python3)</string>
        <string>$SCRIPT_PATH</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
EOF
    launchctl load "$PLIST_FILE" 2>/dev/null || true
    echo "✅ Auto-start configured"
fi

echo ""
echo "✅ Setup complete! Run: python3 main.py"
echo "   Hotkey: Ctrl+Shift+Space"
