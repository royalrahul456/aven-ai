"""AVEN AI Configuration and settings management."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass
class ModelMetadata:
    id: str
    name: str
    display_name: str
    provider: str
    underlying_model: str
    type_name: str
    version: str
    description: str
    emoji: str
    badge: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Bot Identity
    BOT_NAME: str = "AVEN AI"
    BOT_USERNAME: str = "@AvenAi_Bot"
    BOT_VERSION: str = "1.0.0"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""

    # Provider Keys
    GEMINI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    MISTRAL_API_KEY: Optional[str] = None
    MISTRAL_MODEL: str = "codestral-latest"
    MISTRAL_CODE_MODEL: str = "codestral-latest"
    WEB_SEARCH_API_KEY: Optional[str] = None
    TAVILY_API_KEY: Optional[str] = None

    # Model ID Defaults (Configurable for flexible API endpoint mapping)
    GEMINI_MODEL: str = "gemini-flash-latest"
    ANTHROPIC_HAIKU_MODEL: str = "claude-3-5-haiku-20241022"
    ANTHROPIC_SONNET_MODEL: str = "claude-3-5-sonnet-20241022"
    ANTHROPIC_OPUS_MODEL: str = "claude-3-opus-20240229"
    OPENAI_PRO_MODEL: str = "openai/gpt-oss-120b"
    OPENAI_ULTRA_MODEL: str = "openai/gpt-oss-120b"

    # Defaults
    DEFAULT_MODEL: str = "aven_auto"
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_THEME: str = "aven"

    # Database
    DATABASE_PATH: str = "data/aven_ai.db"

    # Performance & Security
    RATE_LIMIT_PER_MINUTE: int = 25
    MAX_HISTORY_MESSAGES: int = 10
    REQUEST_TIMEOUT_SECONDS: int = 60
    MAX_MESSAGE_LENGTH: int = 4096


# Global instance
settings = Settings()

# Ensure data directory exists
Path(settings.DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)

# Central Model Registry Metadata
MODELS_METADATA: Dict[str, ModelMetadata] = {
    "aven_flash": ModelMetadata(
        id="aven_flash",
        name="Aven Flash",
        display_name="⚡ Aven Flash",
        provider="Google",
        underlying_model="Gemini 3.7 Flash",
        type_name="Fast AI",
        version="3.7",
        description="Optimized for fast everyday conversations, instant answers, and quick code.",
        emoji="⚡",
        badge="Fast AI"
    ),
    "aven_swift": ModelMetadata(
        id="aven_swift",
        name="Aven Swift",
        display_name="⚡ Aven Swift",
        provider="Anthropic",
        underlying_model="Claude Haiku 4.5",
        type_name="Fast AI",
        version="4.5",
        description="Ultra-responsive AI designed for speed, precision, and quick problem solving.",
        emoji="⚡",
        badge="Fast AI"
    ),
    "aven_pro": ModelMetadata(
        id="aven_pro",
        name="Aven Pro",
        display_name="🧠 Aven Pro",
        provider="OpenAI",
        underlying_model="GPT-5.6 Terra",
        type_name="Advanced AI",
        version="5.6",
        description="High-capacity intelligence for complex problem solving, coding, and in-depth discussions.",
        emoji="🧠",
        badge="Advanced AI"
    ),
    "aven_claude": ModelMetadata(
        id="aven_claude",
        name="Aven Claude",
        display_name="🧠 Aven Claude",
        provider="Anthropic",
        underlying_model="Claude Sonnet 5",
        type_name="Advanced AI",
        version="5.0",
        description="Superior coding abilities, detailed explanations, and thoughtful conversational flow.",
        emoji="🧠",
        badge="Advanced AI"
    ),
    "aven_ultra": ModelMetadata(
        id="aven_ultra",
        name="Aven Ultra",
        display_name="🔥 Aven Ultra",
        provider="OpenAI",
        underlying_model="GPT-5.6 Sol",
        type_name="Advanced AI",
        version="5.6",
        description="Top-tier computational depth for intricate architectural design and challenging tasks.",
        emoji="🔥",
        badge="Advanced AI"
    ),
    "aven_opus": ModelMetadata(
        id="aven_opus",
        name="Aven Opus",
        display_name="🔬 Aven Opus",
        provider="Anthropic",
        underlying_model="Claude Opus 5",
        type_name="Deep Reasoning",
        version="5.0",
        description="Deep reasoning engine tailored for comprehensive research, step-by-step logic, and analysis.",
        emoji="🔬",
        badge="Deep Reasoning"
    ),
    "aven_mistral": ModelMetadata(
        id="aven_mistral",
        name="Aven Mistral",
        display_name="💻 Aven Mistral",
        provider="Mistral AI",
        underlying_model="Codestral Latest",
        type_name="Code Specialist",
        version="25.08",
        description="Mistral AI flagship code model specialized for programming, syntax correction, and refactoring.",
        emoji="💻",
        badge="Code AI"
    ),
    "aven_web": ModelMetadata(
        id="aven_web",
        name="Aven Web",
        display_name="🌐 Aven Web",
        provider="Web Engine",
        underlying_model="Live Web Search + LLM",
        type_name="Web-enabled AI",
        version="1.0",
        description="Searches real-time web information before answering, citing trustworthy sources.",
        emoji="🌐",
        badge="Web-enabled AI"
    ),
    "aven_auto": ModelMetadata(
        id="aven_auto",
        name="Aven Auto",
        display_name="✨ Aven Auto",
        provider="Auto Router",
        underlying_model="Adaptive Multi-Provider Router",
        type_name="Smart Router",
        version="2.0",
        description="Intelligently evaluates your query and routes to the best available active model.",
        emoji="✨",
        badge="Smart Auto"
    ),
}
