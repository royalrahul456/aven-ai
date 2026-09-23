"""Base abstractions, exceptions, and models for AI providers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


class AIProviderError(Exception):
    """Base exception for AI provider issues."""
    def __init__(self, message: str = "An error occurred with the AI provider."):
        self.message = message
        super().__init__(self.message)


class ProviderUnavailableError(AIProviderError):
    """Raised when an AI provider or model is not configured or offline."""
    def __init__(self, model_name: str = "This model"):
        super().__init__(f"⚠️ <b>Model Unavailable</b>\n\n{model_name} is currently unavailable or unconfigured.\nPlease choose another available model using /models.")


class RateLimitError(AIProviderError):
    """Raised when upstream API rate limits are exceeded."""
    def __init__(self, message: str = "Rate limit reached. Please wait a moment before trying again."):
        super().__init__(f"⚠️ <b>Rate Limit Exceeded</b>\n\n{message}")


class TimeoutError(AIProviderError):
    """Raised when an AI provider call times out."""
    def __init__(self):
        super().__init__("⏳ <b>Request Timed Out</b>\n\nThe AI model took too long to respond. Please try again.")


class InvalidAPIKeyError(AIProviderError):
    """Raised when provider rejects credentials."""
    def __init__(self, provider: str = "AI"):
        super().__init__(f"⚠️ <b>Authentication Error</b>\n\nAPI credentials for {provider} are invalid or missing.")


@dataclass
class ProviderMessage:
    role: str  # 'user', 'assistant', 'system'
    content: str


@dataclass
class SourceCitation:
    title: str
    url: str
    snippet: Optional[str] = None


@dataclass
class ProviderResponse:
    text: str
    model_name: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    sources: List[SourceCitation] = field(default_factory=list)


class AIProvider(ABC):
    """Abstract base class for all AVEN AI providers."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the provider is properly configured with valid credentials."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[ProviderMessage]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> ProviderResponse:
        """Generates an AI response for the given prompt and conversation context."""
        pass
