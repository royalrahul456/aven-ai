"""Help command and interactive documentation handlers with stylized typography."""
from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from utils.themes import Theme
from utils.fonts import to_sans_bold
from bot.keyboards.main import get_help_keyboard, get_back_keyboard

router = Router(name="help_router")


def get_help_sections(theme: Theme) -> dict[str, str]:
    b = theme.bullet
    return {
        "basic": (
            f"<blockquote><b>🚀 {to_sans_bold('CORE COMMANDS')}</b>\n\n"
            f"{b} <code>/start</code> — Open dashboard\n"
            f"{b} <code>/help</code> — Command encyclopedia\n"
            f"{b} <code>/chat &lt;msg&gt;</code> — Chat with AVEN\n"
            f"{b} <code>/ask &lt;prompt&gt;</code> — Ask question\n"
            f"{b} <code>/image &lt;prompt&gt;</code> — Generate AI image (FLUX.1)\n"
            f"{b} <code>/models</code> — Switch AI engines</blockquote>"
        ),
        "tools": (
            f"<blockquote><b>🧠 {to_sans_bold('AI REASONING & ART')}</b>\n\n"
            f"{b} <code>/image &lt;prompt&gt;</code> — FLUX.1 image generator\n"
            f"{b} <code>/imagine &lt;prompt&gt;</code> — AI artwork studio\n"
            f"{b} <code>/think &lt;query&gt;</code> — Step-by-step logic\n"
            f"{b} <code>/explain &lt;topic&gt;</code> — Simple explanations\n"
            f"{b} <code>/summarize &lt;text&gt;</code> — Bulleted key points\n"
            f"{b} <code>/rewrite &lt;text&gt;</code> — Clarity & tone boost\n"
            f"{b} <code>/translate &lt;text&gt;</code> — Multi-language engine</blockquote>"
        ),
        "code": (
            f"<blockquote><b>💻 {to_sans_bold('DEVELOPER SUITE')}</b>\n\n"
            f"{b} <code>/code &lt;task&gt;</code> — Clean code generation\n"
            f"{b} <code>/debug &lt;snippet&gt;</code> — Root cause bug fixes\n"
            f"{b} <code>/explaincode &lt;snippet&gt;</code> — Code breakdown\n"
            f"{b} <code>/optimize &lt;snippet&gt;</code> — Performance boost\n"
            f"{b} <code>/review &lt;snippet&gt;</code> — Architecture & security\n"
            f"{b} <code>/convert &lt;code&gt;</code> — Language converter</blockquote>"
        ),
        "settings": (
            f"<blockquote><b>⚙️ {to_sans_bold('SETTINGS & PERSONALIZATION')}</b>\n\n"
            f"{b} <code>/settings</code> — Active configuration\n"
            f"{b} <code>/theme</code> — Visual & typography theme\n"
            f"{b} <code>/temperature</code> — Creativity gauge\n"
            f"{b} <code>/instructions</code> — Persistent steering\n"
            f"{b} <code>/reset</code> — Restore defaults</blockquote>"
        ),
        "special": (
            f"<blockquote><b>🌐 {to_sans_bold('SPECIAL CAPABILITIES')}</b>\n\n"
            f"{b} <code>/image &lt;prompt&gt;</code> — FLUX.1 image synthesis\n"
            f"{b} <code>/web &lt;query&gt;</code> — Live web grounded search\n"
            f"{b} <code>/auto</code> — Smart intent router\n"
            f"{b} <code>/status</code> — System health & metrics\n"
            f"{b} <code>/ping</code> — Gateway latency diagnostic\n"
            f"{b} <code>/about</code> — Platform architecture</blockquote>"
        ),
    }


def build_full_help(theme: Theme) -> str:
    brand = theme.format_title("AVEN AI — COMMAND DIRECTORY")
    b = theme.bullet
    return (
        f"<blockquote><b>{theme.header_prefix} {brand}</b>\n\n"
        f"<b>🚀 {to_sans_bold('CORE')}</b>\n"
        f"{b} <code>/start</code> • <code>/chat</code> • <code>/ask</code> • <code>/image</code> • <code>/models</code>\n\n"
        f"<b>🧠 {to_sans_bold('REASONING & ART')}</b>\n"
        f"{b} <code>/image</code> • <code>/think</code> • <code>/explain</code>\n"
        f"{b} <code>/summarize</code> • <code>/rewrite</code> • <code>/translate</code>\n\n"
        f"<b>💻 {to_sans_bold('DEVELOPER')}</b>\n"
        f"{b} <code>/code</code> • <code>/debug</code> • <code>/explaincode</code>\n"
        f"{b} <code>/optimize</code> • <code>/review</code> • <code>/convert</code>\n\n"
        f"<b>⚙️ {to_sans_bold('PREFERENCES')}</b>\n"
        f"{b} <code>/settings</code> • <code>/theme</code> • <code>/temperature</code>\n"
        f"{b} <code>/instructions</code> • <code>/reset</code>\n\n"
        f"<b>🌐 {to_sans_bold('SPECIAL')}</b>\n"
        f"{b} <code>/web</code> • <code>/auto</code> • <code>/status</code> • <code>/ping</code></blockquote>"
    )


@router.message(Command("help"))
async def cmd_help(message: Message, theme: Theme) -> None:
    text = build_full_help(theme)
    await message.reply(text, parse_mode="HTML", reply_markup=get_help_keyboard())


@router.callback_query(F.data == "nav:help")
async def cb_help(callback: CallbackQuery, theme: Theme) -> None:
    text = build_full_help(theme)
    if callback.message:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_help_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("help_cat:"))
async def cb_help_category(callback: CallbackQuery, theme: Theme) -> None:
    category = callback.data.split(":")[1]
    if category == "all":
        text = build_full_help(theme)
    else:
        sections = get_help_sections(theme)
        text = sections.get(category, build_full_help(theme))

    if callback.message:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_help_keyboard())
    await callback.answer()
