"""ClaudeEye client using claude CLI with vision support — no API key needed, uses Claude Max plan."""
import subprocess
import os
import base64
import tempfile
import json


class ClaudeEyeClient:
    def __init__(self, api_key: str = None):
        # api_key kept for backward compat but not used
        self.conversation_history = []
        self.system_prompt = """You are ClaudeEye, an AI coding assistant that can see the user's screen.
You have access to screenshots of the user's screen which helps you understand errors, code, and UI without them explaining.
Be concise and direct. When you see errors, identify root cause immediately. When you see code, suggest fixes.
Never say 'I can see your screen' — just respond naturally to what you see."""
        self._verify_claude_cli()

    def _verify_claude_cli(self):
        """Check claude CLI is available."""
        result = subprocess.run(['which', 'claude'], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                "claude CLI not found.\n"
                "Install: npm install -g @anthropic-ai/claude-code\n"
                "Login: claude /login"
            )

    def send_message(self, text: str, screenshot_b64: str = None) -> str:
        """Send message with optional screenshot using claude CLI."""
        img_path = None
        try:
            # Save screenshot to temp file if provided
            if screenshot_b64:
                img_data = base64.b64decode(screenshot_b64)
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                    f.write(img_data)
                    img_path = f.name

            # Build prompt with system context
            parts = [f"[System: {self.system_prompt}]"]

            # Add recent conversation history (last 6 exchanges)
            for msg in self.conversation_history[-6:]:
                role = "User" if msg["role"] == "user" else "Assistant"
                if isinstance(msg["content"], list):
                    for item in msg["content"]:
                        if isinstance(item, dict) and item.get("type") == "text":
                            parts.append(f"{role}: {item['text']}")
                elif isinstance(msg["content"], str):
                    parts.append(f"{role}: {msg['content']}")

            # Add current message, with image path if available
            if img_path:
                parts.append(f"User: {text}\n\n<image>{img_path}</image>")
            else:
                parts.append(f"User: {text}")

            full_prompt = "\n\n".join(parts)

            result = subprocess.run(
                ['claude', '-p', full_prompt, '--dangerously-skip-permissions'],
                capture_output=True, text=True, timeout=60,
                env={**os.environ}
            )

            if result.returncode != 0:
                error = result.stderr.strip()
                raise RuntimeError(f"Claude CLI error: {error[:300]}")

            response = result.stdout.strip() or "(No response from Claude)"

            # Save to history
            self.conversation_history.append({
                "role": "user",
                "content": [{"type": "text", "text": text}]
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })

            return response

        finally:
            if img_path and os.path.exists(img_path):
                os.unlink(img_path)

    def clear_history(self):
        self.conversation_history = []
