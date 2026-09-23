"""User session middleware to load user settings and record activity."""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from database.repository import repo, UserSettings
from utils.themes import get_theme


class UserSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        telegram_user = None
        if isinstance(event, Message) and event.from_user:
            telegram_user = event.from_user
        elif isinstance(event, CallbackQuery) and event.from_user:
            telegram_user = event.from_user

        if telegram_user and not telegram_user.is_bot:
            user_settings: UserSettings = await repo.get_or_create_user(
                user_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name
            )
            data["user_settings"] = user_settings
            data["theme"] = get_theme(user_settings.theme)

        return await handler(event, data)
