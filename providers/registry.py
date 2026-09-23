"""Central Provider Registry for AVEN AI."""
from __future__ import annotations

from typing import Dict, List, Optional
from config import settings, MODELS_METADATA, ModelMetadata
from providers.base import (
    AIProvider,
    ProviderMessage,
    ProviderResponse,
    ProviderUnavailableError,
    AIProviderError
)
from providers.gemini import GeminiProvider
from providers.anthropic import AnthropicProvider
from providers.openai_compatible import OpenAICompatibleProvider
from providers.mistral import MistralProvider
from providers.web import WebProvider
from providers.auto import AutoProvider
from utils.logger import logger


class ProviderRegistry:
    def __init__(self):
        # 1. Underlying providers
        self.gemini_provider = GeminiProvider()
        
        self.anthropic_haiku = AnthropicProvider(
            model=settings.ANTHROPIC_HAIKU_MODEL,
            display_name="Aven Swift"
        )
        self.anthropic_sonnet = AnthropicProvider(
            model=settings.ANTHROPIC_SONNET_MODEL,
            display_name="Aven Claude"
        )
        self.anthropic_opus = AnthropicProvider(
            model=settings.ANTHROPIC_OPUS_MODEL,
            display_name="Aven Opus"
        )

        self.openai_pro = OpenAICompatibleProvider(
            model=settings.OPENAI_PRO_MODEL,
            display_name="Aven Pro"
        )
        self.openai_ultra = OpenAICompatibleProvider(
            model=settings.OPENAI_ULTRA_MODEL,
            display_name="Aven Ultra"
        )

        self.mistral_provider = MistralProvider(
            model=settings.MISTRAL_MODEL,
            display_name="Aven Mistral"
        )

        # Primary LLM provider for web synthesis
        primary_synth_provider = self._resolve_primary_llm()
        self.web_provider = WebProvider(fallback_llm_provider=primary_synth_provider)

        # Smart Auto Router
        self.auto_provider = AutoProvider(registry=self)

        # Map model IDs to concrete providers
        self._providers_map: Dict[str, AIProvider] = {
            "aven_flash": self.gemini_provider,
            "aven_swift": self.anthropic_haiku,
            "aven_pro": self.openai_pro,
            "aven_claude": self.anthropic_sonnet,
            "aven_ultra": self.openai_ultra,
            "aven_opus": self.anthropic_opus,
            "aven_mistral": self.mistral_provider,
            "aven_web": self.web_provider,
            "aven_auto": self.auto_provider,
        }

    def _resolve_primary_llm(self) -> AIProvider:
        """Finds the first available LLM provider for internal operations."""
        candidates = [self.openai_pro, self.gemini_provider, self.mistral_provider, self.anthropic_sonnet, self.anthropic_haiku]
        for candidate in candidates:
            if candidate.is_available():
                return candidate
        # Default to gemini provider even if unconfigured (will report cleanly on invoke)
        return self.gemini_provider

    def get_provider_by_model_id(self, model_id: str) -> Optional[AIProvider]:
        """Retrieves provider instance for a model key."""
        return self._providers_map.get(model_id)

    def is_model_available(self, model_id: str) -> bool:
        """Checks if a model key's provider has valid configured credentials."""
        if model_id == "aven_auto":
            return any(
                p.is_available() for k, p in self._providers_map.items() if k != "aven_auto"
            )
        if model_id == "aven_web":
            return any(
                p.is_available() for k, p in self._providers_map.items() if k not in ("aven_auto", "aven_web")
            )
        provider = self.get_provider_by_model_id(model_id)
        return bool(provider and provider.is_available())

    def get_available_models(self) -> List[str]:
        """Returns all model IDs that currently have available credentials."""
        return [m_id for m_id in MODELS_METADATA.keys() if self.is_model_available(m_id)]

    async def execute_query(
        self,
        model_id: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[ProviderMessage]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> ProviderResponse:
        """Executes a prompt against the requested model with fallback protection."""
        provider = self.get_provider_by_model_id(model_id)
        if not provider:
            raise ProviderUnavailableError(f"Model ID '{model_id}'")

        if not provider.is_available():
            meta = MODELS_METADATA.get(model_id)
            name = meta.name if meta else model_id
            raise ProviderUnavailableError(name)

        # Refresh web provider's synth provider if needed
        if model_id == "aven_web" and (not self.web_provider.fallback_llm_provider or not self.web_provider.fallback_llm_provider.is_available()):
            self.web_provider.fallback_llm_provider = self._resolve_primary_llm()

        return await provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            history=history,
            temperature=temperature,
            max_tokens=max_tokens
        )


registry = ProviderRegistry()
