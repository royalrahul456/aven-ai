"""Rate limiting middleware to prevent spam and abuse."""
from __future__ import annotations

import time
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from config import settings
from utils.logger import logger


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit_per_minute: int = settings.RATE_LIMIT_PER_MINUTE):
        super().__init__()
        self.limit = limit_per_minute
        self.user_timestamps: Dict[int, list[float]] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        if isinstance(event, Message) and event.from_user:
            # If in group, only throttle if it's a command or mention/reply
            if event.chat.type in ("group", "supergroup"):
                is_command = (event.text or "").startswith("/")
                is_reply = event.reply_to_message and event.reply_to_message.from_user and event.reply_to_message.from_user.is_bot
                is_tag = "@" in (event.text or "")
                if not (is_command or is_reply or is_tag):
                    # Passive message, do not rate-limit
                    return await handler(event, data)
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        if not user_id:
            return await handler(event, data)

        now = time.time()
        # Clean older timestamps (> 60 seconds)
        timestamps = self.user_timestamps.get(user_id, [])
        timestamps = [ts for ts in timestamps if now - ts < 60]

        if len(timestamps) >= self.limit:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            if isinstance(event, Message):
                await event.answer("⚠️ <b>Rate limit exceeded.</b>\nPlease slow down and try again in a few moments.", parse_mode="HTML")
            elif isinstance(event, CallbackQuery):
                await event.answer("⚠️ Please slow down! Too many requests.", show_alert=True)
            return

        timestamps.append(now)
        self.user_timestamps[user_id] = timestamps

        return await handler(event, data)
