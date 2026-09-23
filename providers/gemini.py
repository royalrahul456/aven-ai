"""Google Gemini AI Provider implementation."""
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


class GeminiProvider(AIProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        super().__init__(name="Google Gemini")
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL

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
            raise ProviderUnavailableError("Google Gemini (Aven Flash)")

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        # Prepare payload
        contents = []

        # Multi-turn history
        if history:
            for msg in history:
                role = "user" if msg.role == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.content}]
                })

        # Append current user prompt
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

        payload: dict = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": 0.95
            }
        }

        # System instructions
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        candidate_models = [
            self.model,
            "gemini-flash-latest",
            "gemini-2.5-flash",
            "gemini-flash-lite-latest",
            "gemini-pro-latest",
            "gemini-2.5-pro"
        ]
        # Remove duplicates preserving order
        candidate_models = list(dict.fromkeys(candidate_models))

        timeout = aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT_SECONDS)
        last_error_text = ""

        for model_candidate in candidate_models:
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_candidate}:generateContent?key={self.api_key}"
            
            # Retry up to 2 times for transient 503/network errors
            for attempt in range(2):
                try:
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.post(endpoint, json=payload) as response:
                            if response.status == 200:
                                data = await response.json()
                                try:
                                    candidate = data["candidates"][0]
                                    text = candidate["content"]["parts"][0]["text"]
                                    usage = data.get("usageMetadata", {})
                                    prompt_tokens = usage.get("promptTokenCount", 0)
                                    completion_tokens = usage.get("candidatesTokenCount", 0)
                                    return ProviderResponse(
                                        text=text,
                                        model_name="Aven Flash",
                                        provider="Google",
                                        prompt_tokens=prompt_tokens,
                                        completion_tokens=completion_tokens
                                    )
                                except (KeyError, IndexError) as e:
                                    logger.error(f"Malformed Gemini response: {data}, error: {e}")
                                    raise AIProviderError("Received an invalid response format from Google Gemini.")

                            elif response.status in (503, 500, 502, 504):
                                last_error_text = f"Google model '{model_candidate}' is temporarily overloaded (HTTP {response.status})."
                                logger.warning(f"{last_error_text} Attempt {attempt+1}/2. Retrying with next model...")
                                await asyncio.sleep(1.0)
                                break  # Break to next model candidate

                            elif response.status == 404:
                                last_error_text = await response.text()
                                logger.warning(f"Gemini model '{model_candidate}' returned 404. Trying next model candidate...")
                                break  # Break to next model candidate

                            elif response.status == 429:
                                last_error_text = f"Gemini model '{model_candidate}' reached rate limit (429)."
                                logger.warning(f"{last_error_text} Rotating to alternate model endpoint in cluster...")
                                await asyncio.sleep(0.5)
                                break  # Rotate to next candidate model

                            elif response.status in (401, 403):
                                raise InvalidAPIKeyError("Google Gemini")
                            else:
                                error_body = await response.text()
                                logger.error(f"Gemini API Error {response.status}: {error_body}")
                                raise AIProviderError(f"Gemini API returned error code {response.status}.")

                except aiohttp.ClientConnectorError as e:
                    logger.error(f"Connection error to Gemini API: {e}")
                    await asyncio.sleep(1.0)
                except TimeoutError:
                    raise TimeoutError()

        raise AIProviderError(
            "⏳ <b>Google AI is temporarily overloaded</b>\n\n"
            "Google's servers are experiencing peak traffic (503 Service Unavailable).\n"
            "Please try your request again in a few moments."
        )
