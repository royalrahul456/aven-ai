"""Main chat and conversational interaction handlers."""
from __future__ import annotations

import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from config import settings, MODELS_METADATA
from database.repository import repo, UserSettings, ChatMessage
from providers.registry import registry
from providers.base import ProviderMessage, AIProviderError
from utils.themes import Theme
from utils.formatting import markdown_to_telegram_html, format_aven_response_card
from utils.splitter import prepare_response_delivery
from bot.keyboards.main import get_back_keyboard, get_response_action_keyboard
from bot.states.form_states import InteractivePromptForm
from utils.logger import logger

router = Router(name="chat_router")


async def handle_user_chat_query(
    message: Message,
    user_settings: UserSettings,
    theme: Theme,
    query_text: str
) -> None:
    """Core pipeline for multi-turn conversation and query processing."""
    if not query_text or not query_text.strip():
        return

    query_text = query_text.strip()

    # Step 1: Send thinking message as a direct reply to user's question
    title = theme.format_title("AVEN")
    thinking_msg = await message.reply(
        f"<blockquote><b>{theme.header_prefix} {title} is processing...</b></blockquote>",
        parse_mode="HTML"
    )

    # Step 2: Retrieve recent conversation history
    recent_history = await repo.get_recent_messages(user_settings.user_id, limit=settings.MAX_HISTORY_MESSAGES)
    provider_history = [
        ProviderMessage(role=m.role, content=m.content)
        for m in recent_history
    ]

    # Step 3: Build concise system prompt with identity and custom instructions
    system_prompt = (
        "You are AVEN AI — an intelligent, ultra-fast, and precise AI assistant for Telegram.\n\n"
        "Core Response Guidelines:\n"
        "1. Be concise, direct, and focused. Get straight to the answer without fluff, excessive preamble, or repetitive concluding remarks.\n"
        "2. Keep response length proportional to the question: for simple questions, greetings, or quick queries, reply in 1–3 crisp sentences. Only give longer structured answers when explicitly requested or when complex multi-step tasks require it.\n"
        "3. Format cleanly: use bold for key terms, neat bullet points (•) when listing items, and inline `code` for commands, variables, and technical terms.\n"
        "4. When writing code, provide minimal, clean, working code blocks with a brief 1-2 sentence explanation."
    )

    if user_settings.custom_instructions:
        system_prompt += f"\n\nUser Custom Instructions:\n{user_settings.custom_instructions}"

    try:
        # Step 4: Execute query
        response = await registry.execute_query(
            model_id=user_settings.model,
            prompt=query_text,
            system_prompt=system_prompt,
            history=provider_history,
            temperature=user_settings.temperature
        )

        # Step 5: Format response with styled card
        full_html = format_aven_response_card(response.text, response.model_name, user_settings.theme)

        # Step 6: Prepare chunks / file delivery
        chunks, is_file, file_buffer = prepare_response_delivery(full_html)

        if is_file and file_buffer:
            file_attachment = BufferedInputFile(file_buffer.getvalue(), filename="aven_response.txt")
            await message.reply_document(file_attachment, caption=f"📄 Full response from {response.model_name}")

        for i, chunk in enumerate(chunks):
            if i == 0:
                try:
                    await thinking_msg.edit_text(chunk, parse_mode="HTML", disable_web_page_preview=True)
                except Exception as parse_err:
                    logger.warning(f"HTML parse error in Telegram edit_text: {parse_err}. Falling back to safe text...")
                    await thinking_msg.edit_text(response.text[:3500], disable_web_page_preview=True)
            else:
                try:
                    await message.reply(chunk, parse_mode="HTML", disable_web_page_preview=True)
                except Exception:
                    await message.reply(chunk, disable_web_page_preview=True)

        # Step 7: Persist user and assistant messages in database history
        await repo.add_message(user_settings.user_id, "user", query_text, user_settings.model)
        await repo.add_message(user_settings.user_id, "assistant", response.text, user_settings.model)

        # Record usage
        await repo.record_usage(
            user_id=user_settings.user_id,
            model_used=user_settings.model,
            request_type="chat",
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens
        )

    except AIProviderError as e:
        logger.warning(f"AI Provider error: {e}")
        await thinking_msg.edit_text(str(e), parse_mode="HTML")
    except Exception as e:
        logger.exception(f"Unexpected error in handle_user_chat_query: {e}")
        await thinking_msg.edit_text(
            "⚠️ <b>Something went wrong</b>\n\nAVEN couldn't process your request right now.\nPlease try again in a moment.",
            parse_mode="HTML"
        )


# --- Interactive Action Bar Callbacks ---
@router.callback_query(F.data == "ai_act:del")
async def cb_act_delete(callback: CallbackQuery) -> None:
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            pass
    await callback.answer("Message deleted")


@router.callback_query(F.data == "ai_act:regen")
async def cb_act_regen(callback: CallbackQuery, user_settings: UserSettings, theme: Theme) -> None:
    if not callback.message:
        await callback.answer()
        return

    # Fetch last user message from history
    recent = await repo.get_recent_messages(user_settings.user_id, limit=4)
    last_user_msg = next((m.content for m in reversed(recent) if m.role == "user"), None)
    
    if last_user_msg:
        await callback.answer("🔄 Regenerating response...")
        await handle_user_chat_query(callback.message, user_settings, theme, last_user_msg)
    else:
        await callback.answer("Could not find previous message to regenerate.", show_alert=True)


@router.callback_query(F.data == "ai_act:think")
async def cb_act_think(callback: CallbackQuery, user_settings: UserSettings, theme: Theme) -> None:
    if not callback.message:
        await callback.answer()
        return

    recent = await repo.get_recent_messages(user_settings.user_id, limit=4)
    last_user_msg = next((m.content for m in reversed(recent) if m.role == "user"), None)
    
    if last_user_msg:
        await callback.answer("🧠 Thinking deeper...")
        await handle_user_chat_query(callback.message, user_settings, theme, f"Provide concise, deep logical analysis for: {last_user_msg}")
    else:
        await callback.answer("Send your question first to think deeper.", show_alert=True)


@router.callback_query(F.data == "ai_act:explain")
async def cb_act_explain(callback: CallbackQuery, user_settings: UserSettings, theme: Theme) -> None:
    if not callback.message:
        await callback.answer()
        return

    recent = await repo.get_recent_messages(user_settings.user_id, limit=4)
    last_user_msg = next((m.content for m in reversed(recent) if m.role == "user"), None)
    
    if last_user_msg:
        await callback.answer("💡 Explaining simply with examples...")
        await handle_user_chat_query(callback.message, user_settings, theme, f"Explain this clearly and concisely with a simple example: {last_user_msg}")
    else:
        await callback.answer("Send your question first.", show_alert=True)



@router.message(Command("chat"))
async def cmd_chat(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    args = (message.text or "").partition(" ")[2].strip()
    if not args:
        await state.set_state(InteractivePromptForm.waiting_for_chat_input)
        await message.reply("<blockquote><b>💬 Chat Mode</b>\n\nSend any message to chat with AVEN.</blockquote>", parse_mode="HTML")
        return

    await handle_user_chat_query(message, user_settings, theme, args)


@router.callback_query(F.data == "nav:chat")
async def cb_chat(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(InteractivePromptForm.waiting_for_chat_input)
    text = "<blockquote><b>💬 Chat Mode</b>\n\nType and send your message below:</blockquote>"
    if callback.message:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_back_keyboard("nav:start"))
    await callback.answer()


@router.message(Command("ask"))
async def cmd_ask(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    args = (message.text or "").partition(" ")[2].strip()
    if not args:
        await state.set_state(InteractivePromptForm.waiting_for_chat_input)
        await message.reply("<blockquote><b>❓ Ask Mode</b>\n\nPlease enter your question.</blockquote>", parse_mode="HTML")
        return

    await handle_user_chat_query(message, user_settings, theme, args)


@router.message(InteractivePromptForm.waiting_for_chat_input)
async def process_chat_input(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    await state.clear()
    await handle_user_chat_query(message, user_settings, theme, message.text or "")


# Fallback handler for all normal user messages
@router.message(F.text & ~F.text.startswith("/"))
async def natural_text_handler(message: Message, user_settings: UserSettings, theme: Theme) -> None:
    # If in private chat, respond naturally to all messages
    if message.chat.type == "private":
        await handle_user_chat_query(message, user_settings, theme, message.text or "")
        return

    # In Group / Supergroup chats: ONLY respond if mentioned or replied to
    bot_obj = message.bot
    bot_info = await bot_obj.get_me() if bot_obj else None
    bot_username = bot_info.username.lower() if bot_info and bot_info.username else settings.BOT_USERNAME.lstrip("@").lower()

    text = message.text or ""
    text_lower = text.lower()

    # Check 1: Mentioned directly with @username
    is_mentioned = f"@{bot_username}" in text_lower or (bot_info and bot_info.first_name and bot_info.first_name.lower() in text_lower)
    
    # Check 2: Replying to the bot's message
    is_reply_to_bot = (
        message.reply_to_message is not None
        and message.reply_to_message.from_user is not None
        and (
            (bot_info and message.reply_to_message.from_user.id == bot_info.id)
            or message.reply_to_message.from_user.is_bot
        )
    )

    if is_mentioned or is_reply_to_bot:
        # Strip bot username tag from the prompt for cleaner AI processing
        cleaned_prompt = text
        if f"@{bot_username}" in text_lower:
            # Case-insensitive replacement of @bot_username
            import re
            cleaned_prompt = re.sub(rf"@{bot_username}\b", "", cleaned_prompt, flags=re.IGNORECASE).strip()

        if cleaned_prompt:
            await handle_user_chat_query(message, user_settings, theme, cleaned_prompt)
