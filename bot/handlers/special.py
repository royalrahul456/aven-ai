"""Special commands handlers: /web, /auto, /status, /ping with stylized typography."""
from __future__ import annotations

import time
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from config import settings, MODELS_METADATA
from database.repository import repo, UserSettings
from providers.registry import registry
from providers.base import AIProviderError
from utils.themes import Theme
from utils.fonts import to_sans_bold, to_serif_bold, to_mono
from utils.formatting import markdown_to_telegram_html, format_aven_response_card
from utils.splitter import prepare_response_delivery
from bot.keyboards.main import get_back_keyboard, get_ping_keyboard
from bot.states.form_states import InteractivePromptForm

router = Router(name="special_router")


# --- /web ---
@router.message(Command("web"))
async def cmd_web(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    args = (message.text or "").partition(" ")[2].strip()
    if not args:
        await state.set_state(InteractivePromptForm.waiting_for_web_input)
        title = theme.format_title("LIVE WEB SEARCH")
        text = (
            f"<blockquote><b>🌐 {title}</b>\n\n"
            f"Ask any question requiring real-time internet data.\n\n"
            f"<i>AVEN will perform live search synthesis and provide verified citations.</i></blockquote>"
        )
        await message.reply(text, parse_mode="HTML", reply_markup=get_back_keyboard("nav:start"))
        return

    await execute_web_search(message, user_settings, theme, args)


@router.callback_query(F.data == "nav:web")
async def cb_web(callback: CallbackQuery, theme: Theme, state: FSMContext) -> None:
    await state.set_state(InteractivePromptForm.waiting_for_web_input)
    title = theme.format_title("LIVE WEB SEARCH")
    text = (
        f"<blockquote><b>🌐 {title}</b>\n\n"
        f"Ask any question requiring real-time internet data.\n\n"
        f"<i>AVEN will perform live search synthesis and provide verified citations.</i></blockquote>"
    )
    if callback.message:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_back_keyboard("nav:start"))
    await callback.answer()


@router.message(InteractivePromptForm.waiting_for_web_input)
async def process_web_input(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    await state.clear()
    await execute_web_search(message, user_settings, theme, message.text or "")


async def execute_web_search(message: Message, user_settings: UserSettings, theme: Theme, query: str) -> None:
    title = theme.format_title("SEARCHING LIVE WEB")
    thinking_msg = await message.reply(
        f"<blockquote><b>🌐 {title}</b>\n<code>{query[:40]}...</code></blockquote>",
        parse_mode="HTML"
    )

    try:
        response = await registry.execute_query(
            model_id="aven_web",
            prompt=query,
            temperature=0.5
        )

        full_html = format_aven_response_card(response.text, "Aven Web", user_settings.theme)

        chunks, is_file, file_buffer = prepare_response_delivery(full_html)
        if is_file and file_buffer:
            file_attachment = BufferedInputFile(file_buffer.getvalue(), filename="aven_web_research.txt")
            await message.reply_document(file_attachment, caption="🌐 Web Research Report")

        for i, chunk in enumerate(chunks):
            if i == 0:
                try:
                    await thinking_msg.edit_text(chunk, parse_mode="HTML", disable_web_page_preview=False)
                except Exception:
                    await thinking_msg.edit_text(response.text[:3500])
            else:
                try:
                    await message.reply(chunk, parse_mode="HTML", disable_web_page_preview=False)
                except Exception:
                    await message.reply(chunk)

        await repo.record_usage(
            user_id=user_settings.user_id,
            model_used="aven_web",
            request_type="web"
        )

    except AIProviderError as e:
        await thinking_msg.edit_text(str(e), parse_mode="HTML")
    except Exception as e:
        await thinking_msg.edit_text(
            "⚠️ <b>Something went wrong</b>\n\nAVEN couldn't complete the web search right now.",
            parse_mode="HTML"
        )


# --- /auto ---
@router.message(Command("auto"))
async def cmd_auto(message: Message, user_settings: UserSettings, theme: Theme) -> None:
    await repo.update_user_model(user_settings.user_id, "aven_auto")
    user_settings.model = "aven_auto"
    title = theme.format_title("SMART AUTO-ROUTER ACTIVATED")
    confirm_text = (
        f"<blockquote><b>✨ {title}</b>\n\n"
        f"AVEN will dynamically classify your prompts and route to optimal models:\n\n"
        f"✦ <b>Chat / Fast</b> → <code>Groq OSS 120B</code>\n"
        f"✦ <b>Coding</b> → <code>Codestral / Flash</code>\n"
        f"✦ <b>Reasoning</b> → <code>Deep Reasoning</code>\n"
        f"✦ <b>Real-time</b> → <code>Web Engine</code></blockquote>"
    )
    await message.reply(confirm_text, parse_mode="HTML", reply_markup=get_back_keyboard("nav:start"))


# --- /status ---
@router.message(Command("status"))
async def cmd_status(message: Message, user_settings: UserSettings, theme: Theme) -> None:
    meta = MODELS_METADATA.get(user_settings.model)
    model_name = meta.name if meta else "Aven Auto"
    provider_name = meta.provider if meta else "Auto"

    stats = await repo.get_system_stats(user_settings.user_id)
    title = theme.format_title("SYSTEM STATUS & METRICS")
    b = theme.bullet

    status_text = (
        f"<blockquote><b>{theme.header_prefix} {title}</b>\n\n"
        f"{b} <b>Gateway:</b> 🟢 <code>ONLINE</code>\n"
        f"{b} <b>Active Model:</b> <code>{model_name}</code>\n"
        f"{b} <b>Engine Provider:</b> <code>{provider_name}</code>\n"
        f"{b} <b>Web Grounding:</b> 🟢 <code>READY</code>\n"
        f"{b} <b>Architecture:</b> <code>v{settings.BOT_VERSION}</code>\n\n"
        f"<b>✦ USER METRICS:</b>\n"
        f"{b} <b>Your Interactions:</b> <code>{stats.get('user_messages', 0)}</code>\n"
        f"{b} <b>Total System Users:</b> <code>{stats.get('total_users', 0)}</code></blockquote>"
    )
    await message.reply(status_text, parse_mode="HTML", reply_markup=get_back_keyboard("nav:start"))


# --- /ping ---
@router.message(Command("ping"))
async def cmd_ping(message: Message, user_settings: UserSettings, theme: Theme) -> None:
    start_t = time.perf_counter()

    db_start = time.perf_counter()
    await repo.get_system_stats(user_settings.user_id)
    db_latency = (time.perf_counter() - db_start) * 1000

    total_latency = (time.perf_counter() - start_t) * 1000

    meta = MODELS_METADATA.get(user_settings.model)
    model_name = meta.name if meta else "Aven Auto"
    provider_name = meta.provider if meta else "Auto"

    title = theme.format_title("NETWORK DIAGNOSTIC")
    b = theme.bullet
    ping_text = (
        f"<blockquote><b>🏓 {title}</b>\n\n"
        f"{b} <b>Gateway Latency:</b> <code>{total_latency:.1f}ms</code> ⚡\n"
        f"{b} <b>Database Latency:</b> <code>{db_latency:.1f}ms</code> 🗄️\n"
        f"{b} <b>Active Engine:</b> <code>{model_name}</code>\n"
        f"{b} <b>Status:</b> <code>100% HEALTHY</code> 🟢</blockquote>"
    )
    await message.reply(ping_text, parse_mode="HTML", reply_markup=get_ping_keyboard())


@router.callback_query(F.data == "nav:ping")
async def cb_ping(callback: CallbackQuery, user_settings: UserSettings, theme: Theme) -> None:
    start_t = time.perf_counter()

    db_start = time.perf_counter()
    await repo.get_system_stats(user_settings.user_id)
    db_latency = (time.perf_counter() - db_start) * 1000

    total_latency = (time.perf_counter() - start_t) * 1000

    meta = MODELS_METADATA.get(user_settings.model)
    model_name = meta.name if meta else "Aven Auto"

    title = theme.format_title("NETWORK DIAGNOSTIC")
    b = theme.bullet
    ping_text = (
        f"<blockquote><b>🏓 {title}</b>\n\n"
        f"{b} <b>Gateway Latency:</b> <code>{total_latency:.1f}ms</code> ⚡\n"
        f"{b} <b>Database Latency:</b> <code>{db_latency:.1f}ms</code> 🗄️\n"
        f"{b} <b>Active Engine:</b> <code>{model_name}</code>\n"
        f"{b} <b>Status:</b> <code>100% HEALTHY</code> 🟢</blockquote>"
    )
    if callback.message:
        await callback.message.edit_text(ping_text, parse_mode="HTML", reply_markup=get_ping_keyboard())
    await callback.answer(f"🏓 Pong! {total_latency:.1f}ms")
