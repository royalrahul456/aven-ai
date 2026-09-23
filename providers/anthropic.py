"""Anthropic Claude AI Provider implementation."""
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


class AnthropicProvider(AIProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, display_name: str = "Aven Claude"):
        super().__init__(name="Anthropic")
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or settings.ANTHROPIC_SONNET_MODEL
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
            raise ProviderUnavailableError(f"Anthropic ({self.display_name})")

        endpoint = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        # Build messages payload
        messages = []
        if history:
            for msg in history:
                messages.append({
                    "role": "user" if msg.role == "user" else "assistant",
                    "content": msg.content
                })

        messages.append({
            "role": "user",
            "content": prompt
        })

        payload: dict = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": min(max(temperature, 0.0), 1.0)  # Anthropic temperature 0.0 - 1.0
        }

        if system_prompt:
            payload["system"] = system_prompt

        timeout = aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT_SECONDS)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(endpoint, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        try:
                            # Extract text blocks
                            text_blocks = [
                                block["text"] for block in data.get("content", [])
                                if block.get("type") == "text"
                            ]
                            result_text = "\n".join(text_blocks)
                            usage = data.get("usage", {})
                            prompt_tokens = usage.get("input_tokens", 0)
                            completion_tokens = usage.get("output_tokens", 0)

                            return ProviderResponse(
                                text=result_text,
                                model_name=self.display_name,
                                provider="Anthropic",
                                prompt_tokens=prompt_tokens,
                                completion_tokens=completion_tokens
                            )
                        except (KeyError, IndexError) as e:
                            logger.error(f"Malformed Anthropic response: {data}, error: {e}")
                            raise AIProviderError("Received an invalid response structure from Anthropic.")

                    elif response.status == 429:
                        raise RateLimitError("Anthropic API rate limit exceeded.")
                    elif response.status in (401, 403):
                        raise InvalidAPIKeyError("Anthropic")
                    else:
                        error_body = await response.text()
                        logger.error(f"Anthropic API Error {response.status}: {error_body}")
                        raise AIProviderError(f"Anthropic API returned error code {response.status}.")

        except aiohttp.ClientConnectorError as e:
            logger.error(f"Connection error to Anthropic API: {e}")
            raise AIProviderError("Could not connect to Anthropic service.")
        except TimeoutError:
            raise TimeoutError()
