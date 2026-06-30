import json
import logging

import httpx

from app.core.config import settings
from app.llm.base import ChatMessage, LLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider:
    """Chat-completions compatible provider for OpenAI and OpenRouter."""

    def __init__(self) -> None:
        self.provider = settings.llm_provider
        self.base_url = settings.llm_base_url.rstrip("/")
        self.model = settings.openai_model
        self.api_key = settings.openai_api_key

        if self.provider == "openrouter":
            self.base_url = "https://openrouter.ai/api/v1"
            self.model = settings.openrouter_model or settings.openai_model
            self.api_key = settings.openrouter_api_key

    async def complete(self, prompt: str) -> str:
        response = await self._create_chat_completion(
            [{"role": "user", "content": prompt}],
            json_response=False,
        )
        return response["choices"][0]["message"]["content"]

    async def chat_json(self, messages: list[ChatMessage], max_retries: int = 3) -> dict:
        import asyncio
        last_exc = None
        
        for attempt in range(max_retries):
            try:
                response = await self._create_chat_completion(messages, json_response=True)
                if "error" in response:
                    raise ValueError(f"Provider error: {response.get('error')}")
                if "choices" not in response or not response["choices"]:
                    raise ValueError(f"No choices in response: {response}")
                    
                content = response["choices"][0]["message"].get("content")
                if content is None:
                    raise ValueError("Response content was null.")
        
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                elif content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

                return json.loads(content)
            except (ValueError, httpx.HTTPStatusError) as exc:
                last_exc = exc
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                continue
                
        raise ValueError(f"LLM failed after {max_retries} attempts. Last error: {last_exc}") from last_exc

    async def _create_chat_completion(
        self,
        messages: list[ChatMessage],
        json_response: bool,
    ) -> dict:
        if not self.api_key:
            raise ValueError(f"Missing API key for LLM provider: {self.provider}")

        configs_to_try = [
            {
                "provider": self.provider,
                "base_url": self.base_url,
                "api_key": self.api_key,
                "model": self.model,
            }
        ]

        # Add fallbacks
        if self.provider == "openrouter":
            configs_to_try.append({
                "provider": "openrouter",
                "base_url": self.base_url,
                "api_key": self.api_key,
                "model": "openrouter/free",
            })
        elif self.provider == "openai" and getattr(settings, "openrouter_api_key", None):
            configs_to_try.append({
                "provider": "openrouter",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": settings.openrouter_api_key,
                "model": getattr(settings, "openrouter_model", None) or "openrouter/free",
            })

        last_exc = None
        async with httpx.AsyncClient(timeout=30) as client:
            for config in configs_to_try:
                logger.info(f"[LLM Provider] Trying model: {config['model']} via {config['provider']}")
                
                payload: dict = {
                    "messages": messages,
                    "temperature": 0.1,
                    "model": config["model"],
                }

                if json_response and config["provider"] != "openrouter":
                    payload["response_format"] = {"type": "json_object"}

                headers = {
                    "Authorization": f"Bearer {config['api_key']}",
                    "Content-Type": "application/json",
                }

                try:
                    response = await client.post(
                        f"{config['base_url']}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    logger.info(f"[LLM Provider] Success with {config['model']}!")
                    return response.json()
                except httpx.HTTPStatusError as exc:
                    last_exc = exc
                    if exc.response.status_code in (429, 502, 503, 400, 404, 402):
                        logger.warning(f"[LLM Provider] {config['model']} failed with {exc.response.status_code}. Falling back to next configuration...")
                        continue
                    raise

            if last_exc:
                raise last_exc


def get_llm_provider() -> LLMProvider:
    if settings.llm_provider == "gemini":
        from app.llm.gemini_provider import GeminiProvider
        return GeminiProvider()
    return OpenAIProvider()
