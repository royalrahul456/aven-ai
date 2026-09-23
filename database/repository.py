"""Database repository supporting Supabase PostgreSQL and SQLite."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from database.db import db_manager
from config import settings
from utils.logger import logger


@dataclass
class UserSettings:
    user_id: int
    model: str
    temperature: float
    theme: str
    custom_instructions: str
    auto_mode_enabled: bool
    updated_at: str


@dataclass
class ChatMessage:
    id: int
    user_id: int
    conversation_id: Optional[int]
    role: str
    content: str
    model_used: Optional[str]
    created_at: str


class Repository:
    def __init__(self, database=db_manager):
        self.db = database

    async def get_or_create_user(self, user_id: int, username: Optional[str] = None, first_name: Optional[str] = None) -> UserSettings:
        """Retrieves user settings, creating the user and default settings if non-existent."""
        # 1. Upsert user record
        await self.db.execute(
            """
            INSERT INTO users (user_id, username, first_name, last_active_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                username = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                last_active_at = CURRENT_TIMESTAMP
            """,
            user_id, username, first_name
        )

        # 2. Ensure settings record exists (using standard ON CONFLICT DO NOTHING)
        await self.db.execute(
            """
            INSERT INTO settings (user_id, model, temperature, theme, custom_instructions, auto_mode_enabled)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO NOTHING
            """,
            user_id, settings.DEFAULT_MODEL, settings.DEFAULT_TEMPERATURE, settings.DEFAULT_THEME, "", True if self.db.is_postgres else 1
        )

        # 3. Fetch settings
        row = await self.db.fetchrow("SELECT * FROM settings WHERE user_id = ?", user_id)
        if row:
            return UserSettings(
                user_id=int(row["user_id"]),
                model=str(row["model"]),
                temperature=float(row["temperature"]),
                theme=str(row["theme"]),
                custom_instructions=str(row.get("custom_instructions") or ""),
                auto_mode_enabled=bool(row["auto_mode_enabled"]),
                updated_at=str(row["updated_at"])
            )

        # Fallback
        return UserSettings(
            user_id=user_id,
            model=settings.DEFAULT_MODEL,
            temperature=settings.DEFAULT_TEMPERATURE,
            theme=settings.DEFAULT_THEME,
            custom_instructions="",
            auto_mode_enabled=True,
            updated_at=datetime.utcnow().isoformat()
        )

    async def update_user_model(self, user_id: int, model: str) -> None:
        """Updates user's selected active model."""
        await self.db.execute(
            "UPDATE settings SET model = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            model, user_id
        )

    async def update_user_temperature(self, user_id: int, temperature: float) -> None:
        """Updates user's preferred temperature."""
        await self.db.execute(
            "UPDATE settings SET temperature = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            temperature, user_id
        )

    async def update_user_theme(self, user_id: int, theme: str) -> None:
        """Updates user's interface theme."""
        await self.db.execute(
            "UPDATE settings SET theme = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            theme, user_id
        )

    async def update_user_instructions(self, user_id: int, instructions: str) -> None:
        """Updates user's custom AI instructions."""
        await self.db.execute(
            "UPDATE settings SET custom_instructions = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            instructions, user_id
        )

    async def reset_user_settings(self, user_id: int) -> UserSettings:
        """Resets user settings to default values."""
        await self.db.execute(
            """
            UPDATE settings SET
                model = ?,
                temperature = ?,
                theme = ?,
                custom_instructions = '',
                auto_mode_enabled = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            settings.DEFAULT_MODEL, settings.DEFAULT_TEMPERATURE, settings.DEFAULT_THEME, True if self.db.is_postgres else 1, user_id
        )
        return await self.get_or_create_user(user_id)

    async def add_message(self, user_id: int, role: str, content: str, model_used: Optional[str] = None) -> None:
        """Appends a message to conversation history."""
        await self.db.execute(
            """
            INSERT INTO messages (user_id, role, content, model_used)
            VALUES (?, ?, ?, ?)
            """,
            user_id, role, content, model_used
        )

    async def get_recent_messages(self, user_id: int, limit: int = settings.MAX_HISTORY_MESSAGES) -> List[ChatMessage]:
        """Fetches the most recent conversation messages in chronological order."""
        rows = await self.db.fetch(
            """
            SELECT * FROM (
                SELECT * FROM messages
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
            ) sub ORDER BY id ASC
            """,
            user_id, limit
        )
        return [
            ChatMessage(
                id=int(row["id"]),
                user_id=int(row["user_id"]),
                conversation_id=row.get("conversation_id"),
                role=str(row["role"]),
                content=str(row["content"]),
                model_used=row.get("model_used"),
                created_at=str(row["created_at"])
            )
            for row in rows
        ]

    async def clear_history(self, user_id: int) -> None:
        """Clears user conversation history."""
        await self.db.execute("DELETE FROM messages WHERE user_id = ?", user_id)

    async def record_usage(self, user_id: int, model_used: str, request_type: str = "chat", prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
        """Records API usage metric."""
        await self.db.execute(
            """
            INSERT INTO usage_stats (user_id, model_used, request_type, prompt_tokens, completion_tokens)
            VALUES (?, ?, ?, ?, ?)
            """,
            user_id, model_used, request_type, prompt_tokens, completion_tokens
        )

    async def get_system_stats(self, user_id: int) -> Dict[str, Any]:
        """Fetches aggregate statistics for /status command."""
        total_users = await self.db.fetchval("SELECT COUNT(*) FROM users") or 0
        total_messages = await self.db.fetchval("SELECT COUNT(*) FROM messages") or 0
        user_msg_count = await self.db.fetchval("SELECT COUNT(*) FROM messages WHERE user_id = ?", user_id) or 0

        return {
            "total_users": int(total_users),
            "total_messages": int(total_messages),
            "user_messages": int(user_msg_count)
        }


repo = Repository()
