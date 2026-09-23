"""Smart Auto Router: classifies intent and selects best available model with resilient fallback."""
from __future__ import annotations

import re
from typing import List, Optional, Tuple, TYPE_CHECKING
from providers.base import (
    AIProvider,
    ProviderMessage,
    ProviderResponse,
    ProviderUnavailableError,
    AIProviderError
)
from utils.logger import logger

if TYPE_CHECKING:
    from providers.registry import ProviderRegistry


class AutoProvider(AIProvider):
    def __init__(self, registry: ProviderRegistry):
        super().__init__(name="Aven Auto Router")
        self.registry = registry

    def is_available(self) -> bool:
        # Auto is available if any registered provider is active
        return len(self.registry.get_available_models()) > 0

    def classify_intent(self, prompt: str) -> str:
        """
        Classifies user prompt intent to pick optimal model type:
        - 'web': current events, real-time facts, stock, weather, news
        - 'code': programming, debugging, refactoring, algorithms
        - 'reasoning': mathematical proofs, deep logic, philosophical or multi-step analysis
        - 'fast': everyday conversation, simple QA, translations, summaries
        """
        prompt_lower = prompt.lower()

        # Check for web search indicators
        web_keywords = [
            "latest", "today", "yesterday", "news", "current price", "stock price",
            "weather in", "score of", "who won", "release date of", "who is the current",
            "recent news", "what happened in", "2025", "2026"
        ]
        if any(kw in prompt_lower for kw in web_keywords):
            return "web"

        # Check for code indicators
        code_keywords = [
            "def ", "function ", "class ", "import ", "const ", "var ", "let ",
            "public static void", "sql", "select *", "regex", "traceback", "syntax error",
            "debug", "refactor", "algorithm", "python", "javascript", "typescript",
            "c++", "rust", "golang", "html", "css", "dockerfile", "yaml"
        ]
        if any(kw in prompt_lower for kw in code_keywords) or "```" in prompt:
            return "code"

        # Check for deep reasoning indicators
        reasoning_keywords = [
            "prove that", "step by step proof", "logical deduction", "analyze in depth",
            "compare and contrast", "philosophical analysis", "evaluate trade-offs",
            "comprehensive report", "deep dive"
        ]
        if any(kw in prompt_lower for kw in reasoning_keywords) or len(prompt) > 1200:
            return "reasoning"

        return "fast"

    def get_candidate_chain(self, intent: str) -> List[str]:
        """Returns prioritized list of model IDs for the given intent."""
        if intent == "web":
            return ["aven_web", "aven_pro", "aven_mistral", "aven_flash", "aven_claude"]
        elif intent == "code":
            return ["aven_pro", "aven_mistral", "aven_claude", "aven_flash", "aven_ultra"]
        elif intent == "reasoning":
            return ["aven_pro", "aven_mistral", "aven_opus", "aven_ultra", "aven_claude"]
        else:  # fast / general
            return ["aven_pro", "aven_flash", "aven_mistral", "aven_swift", "aven_ultra"]

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[ProviderMessage]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> ProviderResponse:
        intent = self.classify_intent(prompt)
        candidates = self.get_candidate_chain(intent)
        logger.info(f"Auto mode classified intent as '{intent}'. Candidate priority: {candidates}")

        last_error = None
        for model_id in candidates:
            provider = self.registry.get_provider_by_model_id(model_id)
            if provider and provider.is_available():
                try:
                    logger.info(f"Auto router dispatching to '{model_id}'...")
                    response = await provider.generate(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        history=history,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    # Decorate response to indicate Auto routing
                    response.model_name = f"Aven Auto ({response.model_name})"
                    return response
                except Exception as e:
                    logger.warning(f"Model '{model_id}' failed in Auto chain: {e}. Falling back to next candidate...")
                    last_error = e
                    continue

        # If all candidates failed
        if last_error:
            raise last_error
        raise ProviderUnavailableError("No active AI models are currently configured in AVEN AI.")
