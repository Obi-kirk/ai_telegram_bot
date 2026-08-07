import logging
import os

import httpx
from dotenv import load_dotenv

from src.utils.sanitize import sanitize_prompt

load_dotenv()

logger = logging.getLogger(__name__)

ALLOWED_PROVIDER_URLS = {
    "https://openrouter.ai/api/v1/chat/completions",
    "https://api.groq.com/openai/v1/chat/completions",
}


class LLMService:
    """Единый клиент для LLM-провайдеров: OpenRouter (основной), Groq (fallback)."""

    def __init__(
        self,
        max_tokens: int = 500,
        temperature: float = 0.7,
        cache_limit: int = 200,
    ) -> None:
        self.providers: dict[str, dict[str, str | None]] = {
            "openrouter": {
                "url": "https://openrouter.ai/api/v1/chat/completions",
                "key": os.getenv("OPENROUTER_API_KEY"),
                "model": "deepseek/deepseek-v4-flash",
            },
            "groq": {
                "url": "https://api.groq.com/openai/v1/chat/completions",
                "key": os.getenv("GROQ_API_KEY"),
                "model": "llama3-70b-8192",
            },
        }
        self.default_provider = "openrouter"
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.cache_limit = cache_limit
        self.cache: dict[str, str] = {}

    async def generate(self, prompt: str, provider: str | None = None) -> str:
        prompt = sanitize_prompt(prompt)
        if prompt in self.cache:
            return self.cache[prompt]

        provider = provider or self.default_provider
        result = await self._request(provider, prompt)
        if result is None:
            result = await self._fallback(prompt)
        if result is None:
            return "Все провайдеры недоступны. Попробуйте позже."

        self._save_cache(prompt, result)
        return result

    async def _request(self, provider: str, prompt: str) -> str | None:
        config = self.providers.get(provider)
        if (
            not config
            or not config["key"]
            or config["url"] not in ALLOWED_PROVIDER_URLS
        ):
            return None
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    config["url"],
                    json={
                        "model": config["model"],
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": self.max_tokens,
                        "temperature": self.temperature,
                    },
                    headers={"Authorization": f"Bearer {config['key']}"},
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
        except httpx.HTTPError as exc:
            logger.warning("Ошибка LLM-провайдера %s: %s", provider, exc)
            return None

    async def _fallback(self, prompt: str) -> str | None:
        for name in self.providers:
            if name != self.default_provider:
                result = await self._request(name, prompt)
                if result is not None:
                    return result
        return None

    def _save_cache(self, prompt: str, answer: str) -> None:
        if len(self.cache) >= self.cache_limit:
            self.cache.clear()
        self.cache[prompt] = answer
