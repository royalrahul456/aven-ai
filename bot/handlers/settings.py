"""Settings, theme switcher, temperature, custom instructions, and reset handlers with stylized typography."""
from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config import MODELS_METADATA
from database.repository import repo, UserSettings
from utils.themes import Theme, THEMES, get_theme
from utils.fonts import to_sans_bold, to_serif_bold, to_mono
from bot.keyboards.settings import (
    get_settings_keyboard,
    get_theme_keyboard,
    get_temperature_keyboard,
    get_instructions_keyboard,
    get_reset_confirm_keyboard
)
from bot.keyboards.main import get_back_keyboard
from bot.states.form_states import InstructionsForm

router = Router(name="settings_router")


def build_settings_text(user_settings: UserSettings, theme: Theme) -> str:
    meta = MODELS_METADATA.get(user_settings.model)
    model_name = meta.name if meta else "Aven Auto"

    curr_theme = THEMES.get(user_settings.theme, theme)
    theme_name = curr_theme.name

    instr = user_settings.custom_instructions
    instructions_display = (instr[:40] + "..." if len(instr) > 40 else instr) if instr else "Default"
    
    b = theme.bullet
    title = theme.format_title("PREFERENCES DASHBOARD")

    return (
        f"<blockquote><b>{theme.header_prefix} {title}</b>\n\n"
        f"<b>✦ Engine:</b> <code>{model_name}</code>\n"
        f"<b>✦ Creativity:</b> <code>{user_settings.temperature}</code>\n"
        f"<b>✦ Visual Theme:</b> <code>{theme_name}</code>\n"
        f"<b>✦ System Steering:</b> <code>{instructions_display}</code>\n\n"
        f"<i>Configure your AI experience using the controls below:</i></blockquote>"
    )


# --- /settings ---
@router.message(Command("settings"))
async def cmd_settings(message: Message, user_settings: UserSettings, theme: Theme) -> None:
    text = build_settings_text(user_settings, theme)
    await message.reply(text, parse_mode="HTML", reply_markup=get_settings_keyboard())


@router.callback_query(F.data == "nav:settings")
async def cb_settings(callback: CallbackQuery, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    await state.clear()
    text = build_settings_text(user_settings, theme)
    if callback.message:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_settings_keyboard())
    await callback.answer()


# --- /theme ---
@router.message(Command("theme"))
async def cmd_theme(message: Message, user_settings: UserSettings, theme: Theme) -> None:
    kb = get_theme_keyboard(user_settings.theme)
    title = theme.format_title("INTERFACE THEMES")
    await message.reply(f"<blockquote><b>{theme.header_prefix} {title}</b>\n\nSelect a theme style:</blockquote>", parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "nav:theme")
async def cb_theme(callback: CallbackQuery, user_settings: UserSettings, theme: Theme) -> None:
    kb = get_theme_keyboard(user_settings.theme)
    title = theme.format_title("INTERFACE THEMES")
    if callback.message:
        await callback.message.edit_text(f"<blockquote><b>{theme.header_prefix} {title}</b>\n\nSelect a theme style:</blockquote>", parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("theme_set:"))
async def cb_theme_set(callback: CallbackQuery, user_settings: UserSettings) -> None:
    theme_id = callback.data.split(":")[1]
    if theme_id in THEMES:
        await repo.update_user_theme(user_settings.user_id, theme_id)
        user_settings.theme = theme_id
        th = THEMES[theme_id]
        kb = get_theme_keyboard(theme_id)
        title = th.format_title(f"THEME ACTIVATED: {th.name}")
        if callback.message:
            await callback.message.edit_text(
                f"<blockquote><b>{th.header_prefix} {title}</b>\n\nChoose an interface theme:</blockquote>",
                parse_mode="HTML",
                reply_markup=kb
            )
        await callback.answer(f"Theme set to {th.name}!")


# --- /temperature ---
@router.message(Command("temperature"))
async def cmd_temperature(message: Message, user_settings: UserSettings, theme: Theme) -> None:
    kb = get_temperature_keyboard(user_settings.temperature)
    title = theme.format_title("CREATIVITY & PRECISION")
    await message.reply(
        f"<blockquote><b>{theme.header_prefix} {title}</b>\n\n"
        f"<b>✦ Current Level:</b> <code>{user_settings.temperature}</code>\n"
        f"<i>0.2 = Exact & Deterministic | 1.2 = Highly Creative</i>\n\n"
        f"Select a temperature value:</blockquote>",
        parse_mode="HTML",
        reply_markup=kb
    )


@router.callback_query(F.data == "nav:temperature")
async def cb_temperature(callback: CallbackQuery, user_settings: UserSettings, theme: Theme) -> None:
    kb = get_temperature_keyboard(user_settings.temperature)
    title = theme.format_title("CREATIVITY & PRECISION")
    if callback.message:
        await callback.message.edit_text(
            f"<blockquote><b>{theme.header_prefix} {title}</b>\n\n"
            f"<b>✦ Current Level:</b> <code>{user_settings.temperature}</code>\n"
            f"<i>0.2 = Exact & Deterministic | 1.2 = Highly Creative</i>\n\n"
            f"Select a temperature value:</blockquote>",
            parse_mode="HTML",
            reply_markup=kb
        )
    await callback.answer()


@router.callback_query(F.data.startswith("temp_set:"))
async def cb_temp_set(callback: CallbackQuery, user_settings: UserSettings, theme: Theme) -> None:
    temp_val = float(callback.data.split(":")[1])
    await repo.update_user_temperature(user_settings.user_id, temp_val)
    user_settings.temperature = temp_val
    kb = get_temperature_keyboard(temp_val)
    title = theme.format_title("TEMPERATURE UPDATED")
    if callback.message:
        await callback.message.edit_text(
            f"<blockquote><b>{theme.header_prefix} {title}</b>\n\n"
            f"<b>✦ New Level:</b> <code>{temp_val}</code>\n\n"
            f"Select a temperature value:</blockquote>",
            parse_mode="HTML",
            reply_markup=kb
        )
    await callback.answer(f"Temperature set to {temp_val}!")


# --- /instructions ---
@router.message(Command("instructions"))
async def cmd_instructions(message: Message, user_settings: UserSettings, theme: Theme) -> None:
    has_custom = bool(user_settings.custom_instructions)
    instr_text = user_settings.custom_instructions if has_custom else "<i>No custom instructions active.</i>"
    title = theme.format_title("CUSTOM AI STEERING")
    text = (
        f"<blockquote><b>{theme.header_prefix} {title}</b>\n\n"
        f"<i>Custom instructions guide how AVEN responds to every request.</i>\n\n"
        f"<b>✦ Active Instructions:</b>\n{instr_text}</blockquote>"
    )
    kb = get_instructions_keyboard(has_custom)
    await message.reply(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "nav:instructions")
async def cb_instructions(callback: CallbackQuery, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    await state.clear()
    has_custom = bool(user_settings.custom_instructions)
    instr_text = user_settings.custom_instructions if has_custom else "<i>No custom instructions active.</i>"
    title = theme.format_title("CUSTOM AI STEERING")
    text = (
        f"<blockquote><b>{theme.header_prefix} {title}</b>\n\n"
        f"<i>Custom instructions guide how AVEN responds to every request.</i>\n\n"
        f"<b>✦ Active Instructions:</b>\n{instr_text}</blockquote>"
    )
    kb = get_instructions_keyboard(has_custom)
    if callback.message:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "instructions:edit")
async def cb_instructions_edit(callback: CallbackQuery, theme: Theme, state: FSMContext) -> None:
    await state.set_state(InstructionsForm.waiting_for_instructions)
    title = theme.format_title("EDIT INSTRUCTIONS")
    text = (
        f"<blockquote><b>{theme.header_prefix} {title}</b>\n\n"
        f"Send the instructions you would like AVEN to follow.\n\n"
        f"<i>Example: 'Respond in bullet points and include Python code examples.'</i></blockquote>"
    )
    if callback.message:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_back_keyboard("nav:instructions"))
    await callback.answer()


@router.message(InstructionsForm.waiting_for_instructions)
async def process_custom_instructions(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    new_instructions = (message.text or "").strip()
    if not new_instructions:
        await message.reply("Please send valid text instructions.")
        return

    await repo.update_user_instructions(user_settings.user_id, new_instructions)
    user_settings.custom_instructions = new_instructions
    await state.clear()

    title = theme.format_title("INSTRUCTIONS SAVED")
    await message.reply(
        f"<blockquote><b>{theme.header_prefix} {title}</b>\n\n"
        f"<code>{new_instructions}</code>\n\n"
        f"<i>AVEN will use these instructions for all future prompts.</i></blockquote>",
        parse_mode="HTML",
        reply_markup=get_back_keyboard("nav:settings")
    )


@router.callback_query(F.data == "instructions:clear")
async def cb_instructions_clear(callback: CallbackQuery, user_settings: UserSettings, theme: Theme) -> None:
    await repo.update_user_instructions(user_settings.user_id, "")
    user_settings.custom_instructions = ""
    title = theme.format_title("INSTRUCTIONS CLEARED")
    if callback.message:
        await callback.message.edit_text(
            f"<blockquote><b>{theme.header_prefix} {title}</b>\n\n"
            f"<i>Your custom AI instructions have been removed.</i></blockquote>",
            parse_mode="HTML",
            reply_markup=get_back_keyboard("nav:settings")
        )
    await callback.answer("Instructions cleared!")


# --- /reset ---
@router.message(Command("reset"))
async def cmd_reset(message: Message, theme: Theme) -> None:
    title = theme.format_title("RESET PREFERENCES?")
    text = (
        f"<blockquote><b>{theme.header_prefix} {title}</b>\n\n"
        f"This will restore your model, temperature, theme, and instructions back to system defaults.</blockquote>"
    )
    await message.reply(text, parse_mode="HTML", reply_markup=get_reset_confirm_keyboard())


@router.callback_query(F.data == "settings:reset_confirm")
async def cb_reset_confirm(callback: CallbackQuery, theme: Theme) -> None:
    title = theme.format_title("RESET PREFERENCES?")
    text = (
        f"<blockquote><b>{theme.header_prefix} {title}</b>\n\n"
        f"This will restore your model, temperature, theme, and instructions back to system defaults.</blockquote>"
    )
    if callback.message:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_reset_confirm_keyboard())
    await callback.answer()


@router.callback_query(F.data == "settings:do_reset")
async def cb_do_reset(callback: CallbackQuery, user_settings: UserSettings, theme: Theme) -> None:
    updated = await repo.reset_user_settings(user_settings.user_id)
    user_settings.model = updated.model
    user_settings.temperature = updated.temperature
    user_settings.theme = updated.theme
    user_settings.custom_instructions = updated.custom_instructions

    title = theme.format_title("SETTINGS RESTORED")
    confirm_text = (
        f"<blockquote><b>{theme.header_prefix} {title}</b>\n\n"
        f"<i>All settings restored to defaults.</i></blockquote>"
    )
    if callback.message:
        await callback.message.edit_text(confirm_text, parse_mode="HTML", reply_markup=get_back_keyboard("nav:settings"))
    await callback.answer("Settings reset!")
