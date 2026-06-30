from typing import Protocol


ChatMessage = dict[str, str]


class LLMProvider(Protocol):
    async def complete(self, prompt: str) -> str:
        """Return a text completion for a prompt."""

    async def chat_json(self, messages: list[ChatMessage]) -> dict:
        """Return a JSON object from a chat-completions compatible API."""
