import json
import logging

import httpx

from app.core.config import settings
from app.llm.base import ChatMessage, LLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider:
    """Native provider for Google Gemini API."""

    def __init__(self) -> None:
        self.provider = settings.llm_provider
        self.model = settings.openai_model
        # Use openai_api_key for the Gemini API key, since the user already has it there
        self.api_key = settings.openai_api_key
        # Default native endpoint
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def complete(self, prompt: str) -> str:
        response = await self._create_chat_completion(
            [{"role": "user", "content": prompt}],
            json_response=False,
        )
        return response

    async def chat_json(self, messages: list[ChatMessage], max_retries: int = 3) -> dict:
        import asyncio
        last_exc = None
        
        for attempt in range(max_retries):
            try:
                content = await self._create_chat_completion(messages, json_response=True)
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
    ) -> str:
        if not self.api_key:
            raise ValueError(f"Missing API key for LLM provider: {self.provider}")

        configs_to_try = [
            {
                "provider": "gemini_native",
                "base_url": self.base_url,
                "api_key": self.api_key,
                "model": self.model,
            }
        ]

        # OpenRouter Fallback
        if getattr(settings, "openrouter_api_key", None):
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
                
                if config["provider"] == "gemini_native":
                    # Native Gemini Format
                    system_instruction = None
                    contents = []
                    for msg in messages:
                        if msg["role"] == "system":
                            system_instruction = {"parts": [{"text": msg["content"]}]}
                        elif msg["role"] == "user":
                            contents.append({"role": "user", "parts": [{"text": msg["content"]}]})
                        elif msg["role"] == "assistant":
                            contents.append({"role": "model", "parts": [{"text": msg["content"]}]})

                    payload = {
                        "contents": contents,
                        "generationConfig": {
                            "temperature": 0.1,
                        }
                    }
                    if system_instruction:
                        payload["systemInstruction"] = system_instruction
                        
                    if json_response:
                        payload["generationConfig"]["responseMimeType"] = "application/json"

                    headers = {
                        "Content-Type": "application/json",
                    }
                    url = f"{config['base_url']}/models/{config['model']}:generateContent?key={config['api_key']}"

                    try:
                        response = await client.post(url, headers=headers, json=payload)
                        response.raise_for_status()
                        logger.info(f"[LLM Provider] Success with {config['model']} (Native)!")
                        
                        data = response.json()
                        if "candidates" not in data or not data["candidates"]:
                            raise ValueError(f"No candidates in Gemini response: {data}")
                            
                        return data["candidates"][0]["content"]["parts"][0]["text"]
                        
                    except httpx.HTTPStatusError as exc:
                        last_exc = exc
                        if exc.response.status_code in (429, 502, 503, 400, 404, 402):
                            logger.warning(f"[LLM Provider] {config['model']} failed with {exc.response.status_code}. Falling back to next configuration...")
                            continue
                        raise

                else:
                    # OpenAI / OpenRouter Format
                    payload = {
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
                        logger.info(f"[LLM Provider] Success with {config['model']} (OpenRouter)!")
                        
                        data = response.json()
                        if "choices" not in data or not data["choices"]:
                            raise ValueError(f"No choices in response: {data}")
                            
                        return data["choices"][0]["message"]["content"]
                        
                    except httpx.HTTPStatusError as exc:
                        last_exc = exc
                        if exc.response.status_code in (429, 502, 503, 400, 404, 402):
                            logger.warning(f"[LLM Provider] {config['model']} failed with {exc.response.status_code}. Falling back to next configuration...")
                            continue
                        raise

            if last_exc:
                raise last_exc
