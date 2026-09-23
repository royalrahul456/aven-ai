"""Global error handling middleware for safe error sanitization."""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from utils.logger import logger


class ErrorHandlerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as exc:
            logger.exception(f"Unhandled exception caught during update processing: {exc}")
            error_message = (
                "⚠️ <b>Something went wrong</b>\n\n"
                "AVEN couldn't process your request right now.\n"
                "Please try again in a moment."
            )
            try:
                if isinstance(event, Message):
                    await event.answer(error_message, parse_mode="HTML")
                elif isinstance(event, CallbackQuery) and event.message:
                    await event.message.answer(error_message, parse_mode="HTML")
                    await event.answer()
            except Exception as notify_err:
                logger.error(f"Failed to send error message to user: {notify_err}")
