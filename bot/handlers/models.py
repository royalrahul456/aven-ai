"""Model selector, info cards, and switcher handlers with typography enhancements."""
from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from config import MODELS_METADATA, ModelMetadata
from database.repository import repo, UserSettings
from providers.registry import registry
from utils.themes import Theme
from utils.fonts import to_sans_bold, to_serif_bold, to_mono
from bot.keyboards.models import get_models_keyboard, get_model_detail_keyboard
from bot.keyboards.main import get_back_keyboard

router = Router(name="models_router")


def build_model_selector_text(current_model_id: str, theme: Theme) -> str:
    meta = MODELS_METADATA.get(current_model_id)
    name = meta.name if meta else "Aven Auto"
    emoji = meta.emoji if meta else "✨"
    title = theme.format_title("AI MODEL REGISTRY")

    return (
        f"<blockquote><b>{theme.header_prefix} {title}</b>\n\n"
        f"<b>✦ Current Engine:</b> {emoji} <code>{name}</code>\n"
        f"<b>✦ Status:</b> 🟢 Operational\n\n"
        f"Select a specialized AI model from the options below:</blockquote>"
    )


def build_model_detail_text(model_id: str, is_active: bool, theme: Theme) -> str:
    meta = MODELS_METADATA.get(model_id)
    if not meta:
        return "⚠️ Unknown model."

    is_available = registry.is_model_available(model_id)
    status_str = "🟢 Online" if is_available else "🔴 Unavailable (No API Key)"
    active_badge = "\n<b>✦ Active:</b> ⚡ <i>(Currently Selected)</i>" if is_active else ""
    title = theme.format_title(meta.name.upper())

    return (
        f"<blockquote><b>{meta.emoji} {title}</b>\n\n"
        f"<b>✦ Provider:</b> <code>{meta.provider}</code>\n"
        f"<b>✦ Base Architecture:</b> <code>{meta.underlying_model}</code>\n"
        f"<b>✦ Specialization:</b> {meta.badge}\n"
        f"<b>✦ Engine Status:</b> {status_str}{active_badge}\n\n"
        f"<i>{meta.description}</i></blockquote>"
    )


@router.message(Command("models"))
async def cmd_models(message: Message, user_settings: UserSettings, theme: Theme) -> None:
    text = build_model_selector_text(user_settings.model, theme)
    kb = get_models_keyboard(user_settings.model)
    await message.reply(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "nav:models")
async def cb_models(callback: CallbackQuery, user_settings: UserSettings, theme: Theme) -> None:
    text = build_model_selector_text(user_settings.model, theme)
    kb = get_models_keyboard(user_settings.model)
    if callback.message:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("model_view:"))
async def cb_model_view(callback: CallbackQuery, user_settings: UserSettings, theme: Theme) -> None:
    model_id = callback.data.split(":")[1]
    is_active = (user_settings.model == model_id)
    text = build_model_detail_text(model_id, is_active, theme)
    kb = get_model_detail_keyboard(model_id, is_active)
    if callback.message:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("model_select:"))
async def cb_model_select(callback: CallbackQuery, user_settings: UserSettings, theme: Theme) -> None:
    model_id = callback.data.split(":")[1]
    meta = MODELS_METADATA.get(model_id)
    if not meta:
        await callback.answer("Model not recognized.", show_alert=True)
        return

    is_available = registry.is_model_available(model_id)
    if not is_available and model_id not in ("aven_auto", "aven_web"):
        await callback.answer(
            f"⚠️ {meta.name} is currently unavailable because its API key is not configured.",
            show_alert=True
        )
        return

    await repo.update_user_model(user_settings.user_id, model_id)
    user_settings.model = model_id

    title = theme.format_title("MODEL ACTIVATED")
    confirm_text = (
        f"<blockquote><b>{theme.header_prefix} {title}</b>\n\n"
        f"Switched engine to <b>{meta.emoji} {meta.name}</b>.\n\n"
        f"<i>Future prompts will now route to this engine.</i></blockquote>"
    )

    if callback.message:
        await callback.message.edit_text(confirm_text, parse_mode="HTML", reply_markup=get_back_keyboard("nav:models"))
    await callback.answer(f"Switched to {meta.name}!")


@router.callback_query(F.data.startswith("model_info:"))
async def cb_model_info(callback: CallbackQuery, theme: Theme) -> None:
    model_id = callback.data.split(":")[1]
    meta = MODELS_METADATA.get(model_id)
    if not meta:
        await callback.answer("Unknown model", show_alert=True)
        return

    b = theme.bullet
    title = theme.format_title(f"SPECIFICATION: {meta.name.upper()}")
    info_text = (
        f"<blockquote><b>{theme.header_prefix} {title}</b>\n\n"
        f"{b} <b>Model ID:</b> <code>{meta.id}</code>\n"
        f"{b} <b>Base Engine:</b> <code>{meta.underlying_model}</code>\n"
        f"{b} <b>Provider:</b> <code>{meta.provider}</code>\n"
        f"{b} <b>Specialty:</b> {meta.badge}\n"
        f"{b} <b>Release:</b> <code>{meta.version}</code>\n\n"
        f"<b>✦ Capabilities:</b>\n"
        f"{b} Context: 128k - 1M tokens\n"
        f"{b} High-Performance Reasoning\n"
        f"{b} Production-grade Code Synthesis\n"
        f"{b} Sliding-Window Memory</blockquote>"
    )

    if callback.message:
        await callback.message.edit_text(info_text, parse_mode="HTML", reply_markup=get_back_keyboard(f"model_view:{model_id}"))
    await callback.answer()
