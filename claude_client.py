"""Anthropic API client with vision support."""
import anthropic
from typing import Optional

class ClaudeEyeClient:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.conversation_history = []
        self.system_prompt = """You are ClaudeEye, an AI coding assistant that can see the user's screen.
You have access to screenshots of the user's screen which helps you understand:
- Error messages without them having to copy-paste
- Terminal output and stack traces
- Code in their editor
- UI issues they're debugging

Be concise, practical, and focus on solving the actual problem visible in the screenshot.
When you see an error, immediately identify the root cause and suggest the fix.
"""

    def send_message(self, text: str, screenshot_b64: Optional[str] = None) -> str:
        """Send a message with optional screenshot to Claude."""
        content = []

        if screenshot_b64:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": screenshot_b64,
                }
            })

        content.append({
            "type": "text",
            "text": text
        })

        self.conversation_history.append({
            "role": "user",
            "content": content
        })

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=self.system_prompt,
            messages=self.conversation_history,
        )

        assistant_message = response.content[0].text
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

    def clear_history(self):
        self.conversation_history = []
