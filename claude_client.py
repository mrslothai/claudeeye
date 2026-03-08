"""Anthropic API client with vision support and conversation history."""
import anthropic
from typing import Optional

SYSTEM_PROMPT = """You are ClaudeEye, an AI assistant that can see the user's screen.
Every message includes a screenshot of what the user currently sees.
Be concise and direct. When you see errors, identify root cause immediately.
When you see code, suggest fixes without being asked.
Never say "I can see your screen" — just respond to what you see naturally."""


class ClaudeEyeClient:
    def __init__(self, api_key: str, model: str = "claude-opus-4-5"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.conversation_history = []
        self.system_prompt = SYSTEM_PROMPT

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
        """Clear conversation history."""
        self.conversation_history = []
