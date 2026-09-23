"""Database repository for users, settings, chat history, and analytics."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
import aiosqlite
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
        async with self.db.get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            # Upsert user record
            await conn.execute(
                """
                INSERT INTO users (user_id, username, first_name, last_active_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    last_active_at = CURRENT_TIMESTAMP
                """,
                (user_id, username, first_name)
            )

            # Ensure settings record exists
            await conn.execute(
                """
                INSERT OR IGNORE INTO settings (user_id, model, temperature, theme, custom_instructions, auto_mode_enabled)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, settings.DEFAULT_MODEL, settings.DEFAULT_TEMPERATURE, settings.DEFAULT_THEME, "", 1)
            )
            await conn.commit()

            # Fetch settings
            cursor = await conn.execute("SELECT * FROM settings WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            if row:
                return UserSettings(
                    user_id=row["user_id"],
                    model=row["model"],
                    temperature=float(row["temperature"]),
                    theme=row["theme"],
                    custom_instructions=row["custom_instructions"] or "",
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
        async with self.db.get_connection() as conn:
            await conn.execute(
                "UPDATE settings SET model = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (model, user_id)
            )
            await conn.commit()

    async def update_user_temperature(self, user_id: int, temperature: float) -> None:
        """Updates user's preferred temperature."""
        async with self.db.get_connection() as conn:
            await conn.execute(
                "UPDATE settings SET temperature = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (temperature, user_id)
            )
            await conn.commit()

    async def update_user_theme(self, user_id: int, theme: str) -> None:
        """Updates user's interface theme."""
        async with self.db.get_connection() as conn:
            await conn.execute(
                "UPDATE settings SET theme = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (theme, user_id)
            )
            await conn.commit()

    async def update_user_instructions(self, user_id: int, instructions: str) -> None:
        """Updates user's custom AI instructions."""
        async with self.db.get_connection() as conn:
            await conn.execute(
                "UPDATE settings SET custom_instructions = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (instructions, user_id)
            )
            await conn.commit()

    async def reset_user_settings(self, user_id: int) -> UserSettings:
        """Resets user settings to default values."""
        async with self.db.get_connection() as conn:
            await conn.execute(
                """
                UPDATE settings SET
                    model = ?,
                    temperature = ?,
                    theme = ?,
                    custom_instructions = '',
                    auto_mode_enabled = 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (settings.DEFAULT_MODEL, settings.DEFAULT_TEMPERATURE, settings.DEFAULT_THEME, user_id)
            )
            await conn.commit()
        return await self.get_or_create_user(user_id)

    async def add_message(self, user_id: int, role: str, content: str, model_used: Optional[str] = None) -> None:
        """Appends a message to conversation history."""
        async with self.db.get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO messages (user_id, role, content, model_used)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, role, content, model_used)
            )
            await conn.commit()

    async def get_recent_messages(self, user_id: int, limit: int = settings.MAX_HISTORY_MESSAGES) -> List[ChatMessage]:
        """Fetches the most recent conversation messages in chronological order."""
        async with self.db.get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                """
                SELECT * FROM (
                    SELECT * FROM messages
                    WHERE user_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                ) ORDER BY id ASC
                """,
                (user_id, limit)
            )
            rows = await cursor.fetchall()
            return [
                ChatMessage(
                    id=row["id"],
                    user_id=row["user_id"],
                    conversation_id=row["conversation_id"],
                    role=row["role"],
                    content=row["content"],
                    model_used=row["model_used"],
                    created_at=str(row["created_at"])
                )
                for row in rows
            ]

    async def clear_history(self, user_id: int) -> None:
        """Clears user conversation history."""
        async with self.db.get_connection() as conn:
            await conn.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
            await conn.commit()

    async def record_usage(self, user_id: int, model_used: str, request_type: str = "chat", prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
        """Records API usage metric."""
        async with self.db.get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO usage_stats (user_id, model_used, request_type, prompt_tokens, completion_tokens)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, model_used, request_type, prompt_tokens, completion_tokens)
            )
            await conn.commit()

    async def get_system_stats(self, user_id: int) -> Dict[str, Any]:
        """Fetches aggregate statistics for /status command."""
        async with self.db.get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            # Total users
            c1 = await conn.execute("SELECT COUNT(*) as total_users FROM users")
            r1 = await c1.fetchone()
            total_users = r1["total_users"] if r1 else 0

            # Total messages
            c2 = await conn.execute("SELECT COUNT(*) as total_messages FROM messages")
            r2 = await c2.fetchone()
            total_messages = r2["total_messages"] if r2 else 0

            # User messages
            c3 = await conn.execute("SELECT COUNT(*) as user_msg_count FROM messages WHERE user_id = ?", (user_id,))
            r3 = await c3.fetchone()
            user_msg_count = r3["user_msg_count"] if r3 else 0

            return {
                "total_users": total_users,
                "total_messages": total_messages,
                "user_messages": user_msg_count
            }


repo = Repository()
