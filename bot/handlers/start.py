"""Start, About, and top-level navigation handlers with rich typography."""
from __future__ import annotations

import datetime
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from config import settings, MODELS_METADATA
from database.repository import UserSettings
from utils.themes import Theme, get_theme
from utils.fonts import to_sans_bold, to_serif_bold, to_mono, to_double_struck
from bot.keyboards.main import get_start_keyboard, get_back_keyboard

router = Router(name="start_router")


def get_time_greeting() -> str:
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        return "🌅 Good Morning"
    elif 12 <= hour < 17:
        return "☀️ Good Afternoon"
    elif 17 <= hour < 22:
        return "🌆 Good Evening"
    else:
        return "🌙 Good Night"


def build_start_text(user_settings: UserSettings, theme: Theme) -> str:
    current_meta = MODELS_METADATA.get(user_settings.model)
    model_name = current_meta.name if current_meta else "Aven Auto"
    emoji = current_meta.emoji if current_meta else "✨"
    
    greeting = get_time_greeting()
    brand_title = theme.format_title("AVEN AI PLATFORM")
    sub_title = theme.format_title("INTELLIGENT TELEGRAM SUITE")

    return (
        f"<blockquote><b>{theme.header_prefix} {brand_title}</b>\n"
        f"<i>{sub_title}</i>\n\n"
        f"{greeting}! Ready to assist with reasoning, code, and web intelligence.\n\n"
        f"<b>✦ CAPABILITIES</b>\n"
        f"💬 <b>Chat</b> — Instant crisp multi-turn AI\n"
        f"🎨 <b>Image</b> — FLUX.1 AI artwork generator\n"
        f"🧠 <b>Reason</b> — In-depth logical analysis\n"
        f"💻 <b>Code</b> — Multi-language programming\n"
        f"🌐 <b>Web</b> — Live real-time cited search\n"
        f"🤖 <b>Models</b> — Multi-engine failover\n\n"
        f"<b>✦ ACTIVE ENGINE:</b> {emoji} <code>{model_name}</code>\n"
        f"<b>✦ THEME:</b> <code>{theme.name}</code></blockquote>"
    )


@router.message(CommandStart())
async def cmd_start(message: Message, user_settings: UserSettings, theme: Theme) -> None:
    text = build_start_text(user_settings, theme)
    kb = get_start_keyboard(user_settings.theme)
    await message.reply(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "nav:start")
async def cb_start(callback: CallbackQuery, user_settings: UserSettings, theme: Theme) -> None:
    text = build_start_text(user_settings, theme)
    kb = get_start_keyboard(user_settings.theme)
    if callback.message:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.message(Command("about"))
async def cmd_about(message: Message, user_settings: UserSettings, theme: Theme) -> None:
    brand = theme.format_title("AVEN AI")
    about_text = (
        f"<blockquote><b>{theme.header_prefix} ABOUT {brand}</b>\n\n"
        f"<i>Next-generation conversational AI platform built specifically for high-speed Telegram interaction.</i>\n\n"
        f"<b>✦ Architecture:</b> Asynchronous Event Loop\n"
        f"<b>✦ Providers:</b> Groq, Google Gemini, Mistral AI\n"
        f"<b>✦ Web Grounding:</b> Real-time Multi-Engine\n"
        f"<b>✦ Storage:</b> Persistent Async SQLite\n"
        f"<b>✦ Version:</b> <code>v{settings.BOT_VERSION}</code></blockquote>"
    )
    await message.reply(about_text, parse_mode="HTML", reply_markup=get_back_keyboard("nav:start"))


@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery) -> None:
    await callback.answer()
