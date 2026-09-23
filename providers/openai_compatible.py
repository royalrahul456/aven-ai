"""OpenAI and OpenAI-compatible API Provider implementation."""
from __future__ import annotations

import asyncio
import json
from typing import List, Optional
import aiohttp
from config import settings
from providers.base import (
    AIProvider,
    ProviderMessage,
    ProviderResponse,
    ProviderUnavailableError,
    RateLimitError,
    InvalidAPIKeyError,
    TimeoutError,
    AIProviderError
)
from utils.logger import logger


class OpenAICompatibleProvider(AIProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        display_name: str = "Aven Pro"
    ):
        super().__init__(name="OpenAI")
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = (base_url or settings.OPENAI_API_BASE).rstrip("/")
        self.model = model or settings.OPENAI_PRO_MODEL
        self.display_name = display_name

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[ProviderMessage]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> ProviderResponse:
        if not self.is_available():
            raise ProviderUnavailableError(f"OpenAI ({self.display_name})")

        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if history:
            for msg in history:
                messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": prompt})

        candidate_models = [self.model, "openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b", "gpt-4o", "gpt-4o-mini"]
        candidate_models = list(dict.fromkeys(candidate_models))

        timeout = aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT_SECONDS)
        last_error_text = ""

        for model_candidate in candidate_models:
            payload = {
                "model": model_candidate,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(endpoint, json=payload, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            try:
                                choice = data["choices"][0]
                                text = choice["message"]["content"]
                                usage = data.get("usage", {})
                                prompt_tokens = usage.get("prompt_tokens", 0)
                                completion_tokens = usage.get("completion_tokens", 0)

                                return ProviderResponse(
                                    text=text,
                                    model_name=self.display_name,
                                    provider="OpenAI / Groq",
                                    prompt_tokens=prompt_tokens,
                                    completion_tokens=completion_tokens
                                )
                            except (KeyError, IndexError) as e:
                                logger.error(f"Malformed response from {self.display_name}: {data}, error: {e}")
                                raise AIProviderError(f"Received an invalid response format from {self.display_name}.")

                        elif response.status in (404, 400):
                            last_error_text = await response.text()
                            logger.warning(f"Model '{model_candidate}' failed on {self.base_url} (HTTP {response.status}). Trying next candidate...")
                            continue

                        elif response.status == 429:
                            last_error_text = f"Rate limit on model '{model_candidate}'"
                            logger.warning(f"{last_error_text}. Trying next candidate...")
                            await asyncio.sleep(0.5)
                            continue

                        elif response.status in (401, 403):
                            raise InvalidAPIKeyError(self.display_name)
                        else:
                            error_body = await response.text()
                            logger.error(f"API Error {response.status}: {error_body}")
                            raise AIProviderError(f"API returned error code {response.status}.")

            except aiohttp.ClientConnectorError as e:
                logger.error(f"Connection error to {self.base_url}: {e}")
                raise AIProviderError(f"Could not connect to service at {self.base_url}.")
            except TimeoutError:
                raise TimeoutError()

        raise AIProviderError(f"All candidate models failed: {last_error_text}")
