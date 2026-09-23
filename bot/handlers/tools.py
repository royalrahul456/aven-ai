"""AI Tools handlers: /think, /explain, /summarize, /rewrite, /translate."""
from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from database.repository import repo, UserSettings
from providers.registry import registry
from providers.base import ProviderMessage, AIProviderError
from utils.themes import Theme
from utils.formatting import markdown_to_telegram_html, format_aven_response_card
from utils.splitter import prepare_response_delivery
from bot.keyboards.main import get_back_keyboard, get_response_action_keyboard
from bot.keyboards.tools import get_language_selector_keyboard
from bot.states.form_states import TranslateForm, InteractivePromptForm

router = Router(name="tools_router")


async def run_ai_task(
    message: Message,
    user_settings: UserSettings,
    theme: Theme,
    prompt: str,
    system_prompt: str,
    override_model: str | None = None,
    task_name: str = "tool"
) -> None:
    """Helper to run a specialized AI tool task with typing indicators and safe message delivery."""
    title = theme.format_title("AVEN")
    thinking_msg = await message.reply(
        f"<blockquote><b>{theme.header_prefix} {title} is reasoning...</b></blockquote>",
        parse_mode="HTML"
    )

    model_to_use = override_model or user_settings.model
    if user_settings.custom_instructions:
        system_prompt = f"{system_prompt}\n\nUser Custom Instructions:\n{user_settings.custom_instructions}"

    try:
        response = await registry.execute_query(
            model_id=model_to_use,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=user_settings.temperature
        )

        full_html = format_aven_response_card(response.text, response.model_name, user_settings.theme)

        chunks, is_file, file_buffer = prepare_response_delivery(full_html)

        if is_file and file_buffer:
            file_attachment = BufferedInputFile(file_buffer.getvalue(), filename=f"aven_{task_name}_response.txt")
            await message.reply_document(file_attachment, caption=f"📄 {task_name.capitalize()} response by {response.model_name}")

        for i, chunk in enumerate(chunks):
            if i == 0:
                try:
                    await thinking_msg.edit_text(chunk, parse_mode="HTML", disable_web_page_preview=True)
                except Exception:
                    # Fallback if markdown error
                    await thinking_msg.edit_text(response.text[:3500], disable_web_page_preview=True)
            else:
                try:
                    await message.reply(chunk, parse_mode="HTML", disable_web_page_preview=True)
                except Exception:
                    await message.reply(chunk, disable_web_page_preview=True)

        # Record usage
        await repo.record_usage(
            user_id=user_settings.user_id,
            model_used=model_to_use,
            request_type=task_name,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens
        )

    except AIProviderError as e:
        await thinking_msg.edit_text(str(e), parse_mode="HTML")
    except Exception as e:
        await thinking_msg.edit_text(
            "⚠️ <b>Something went wrong</b>\n\nAVEN couldn't process your request right now. Please try again.",
            parse_mode="HTML"
        )


# --- /think ---
@router.message(Command("think"))
async def cmd_think(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    args = (message.text or "").partition(" ")[2].strip()
    if not args:
        await state.set_state(InteractivePromptForm.waiting_for_think_input)
        text = (
            f"<blockquote><b>🧠 Deep Reasoning Mode</b>\n\n"
            f"Send your question and AVEN will reason step-by-step.</blockquote>"
        )
        await message.reply(text, parse_mode="HTML", reply_markup=get_back_keyboard("nav:start"))
        return

    sys_prompt = (
        "You are AVEN AI in Reasoning Mode. Provide a concise, clear, step-by-step logical breakdown of the problem and a direct conclusion."
    )
    # Prefer aven_opus or current model if available
    reasoning_model = "aven_opus" if registry.is_model_available("aven_opus") else user_settings.model
    await run_ai_task(message, user_settings, theme, args, sys_prompt, override_model=reasoning_model, task_name="think")


@router.message(InteractivePromptForm.waiting_for_think_input)
async def process_think_input(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    await state.clear()
    args = message.text or ""
    sys_prompt = (
        "You are AVEN AI in Reasoning Mode. Provide a concise, clear, step-by-step logical breakdown of the problem and a direct conclusion."
    )
    reasoning_model = "aven_opus" if registry.is_model_available("aven_opus") else user_settings.model
    await run_ai_task(message, user_settings, theme, args, sys_prompt, override_model=reasoning_model, task_name="think")


# --- /explain ---
@router.message(Command("explain"))
async def cmd_explain(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    args = (message.text or "").partition(" ")[2].strip()
    if not args:
        await state.set_state(InteractivePromptForm.waiting_for_explain_input)
        await message.reply("<blockquote><b>💡 Explain Mode</b>\n\nPlease enter the topic or concept you want explained.</blockquote>", parse_mode="HTML")
        return

    sys_prompt = "You are AVEN AI. Explain the topic simply, clearly, and concisely with a brief example. Keep it focused and brief."
    await run_ai_task(message, user_settings, theme, args, sys_prompt, task_name="explain")


@router.message(InteractivePromptForm.waiting_for_explain_input)
async def process_explain_input(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    await state.clear()
    sys_prompt = "You are AVEN AI. Explain the topic simply, clearly, and concisely with a brief example. Keep it focused and brief."
    await run_ai_task(message, user_settings, theme, message.text or "", sys_prompt, task_name="explain")


# --- /summarize ---
@router.message(Command("summarize"))
async def cmd_summarize(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    args = (message.text or "").partition(" ")[2].strip()
    if not args:
        await state.set_state(InteractivePromptForm.waiting_for_summarize_input)
        await message.reply("<blockquote><b>📑 Summarize Mode</b>\n\nPaste or send the text you want summarized.</blockquote>", parse_mode="HTML")
        return

    sys_prompt = "You are AVEN AI. Summarize the text into 3-5 concise, impactful bullet points."
    await run_ai_task(message, user_settings, theme, args, sys_prompt, task_name="summarize")


@router.message(InteractivePromptForm.waiting_for_summarize_input)
async def process_summarize_input(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    await state.clear()
    sys_prompt = "You are AVEN AI. Summarize the text into 3-5 concise, impactful bullet points."
    await run_ai_task(message, user_settings, theme, message.text or "", sys_prompt, task_name="summarize")


# --- /rewrite ---
@router.message(Command("rewrite"))
async def cmd_rewrite(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    args = (message.text or "").partition(" ")[2].strip()
    if not args:
        await state.set_state(InteractivePromptForm.waiting_for_rewrite_input)
        await message.reply("<blockquote><b>✍️ Rewrite & Improve</b>\n\nPaste the text you want improved for clarity and tone.</blockquote>", parse_mode="HTML")
        return

    sys_prompt = "You are AVEN AI. Rewrite the provided text directly to improve clarity, precision, and tone. Provide the rewritten text followed by a 1-line note of changes."
    await run_ai_task(message, user_settings, theme, args, sys_prompt, task_name="rewrite")


@router.message(InteractivePromptForm.waiting_for_rewrite_input)
async def process_rewrite_input(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    await state.clear()
    sys_prompt = "You are AVEN AI. Rewrite the provided text directly to improve clarity, precision, and tone. Provide the rewritten text followed by a 1-line note of changes."
    await run_ai_task(message, user_settings, theme, message.text or "", sys_prompt, task_name="rewrite")


# --- /translate ---
@router.message(Command("translate"))
async def cmd_translate(message: Message, state: FSMContext) -> None:
    args = (message.text or "").partition(" ")[2].strip()
    if args:
        await state.update_data(translate_text=args)
        await message.reply(
            "<blockquote><b>🌐 Select Target Language:</b></blockquote>",
            parse_mode="HTML",
            reply_markup=get_language_selector_keyboard("trans_to")
        )
    else:
        await state.set_state(TranslateForm.waiting_for_text)
        await message.reply("<blockquote><b>🌐 Translation Tool</b>\n\nSend the text you wish to translate.</blockquote>", parse_mode="HTML")


@router.message(TranslateForm.waiting_for_text)
async def process_translate_text(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.reply("Please send valid text.")
        return
    await state.update_data(translate_text=text)
    await message.reply(
        "<blockquote><b>🌐 Select Target Language:</b></blockquote>",
        parse_mode="HTML",
        reply_markup=get_language_selector_keyboard("trans_to")
    )


@router.callback_query(F.data.startswith("trans_to:"))
async def cb_trans_to(callback: CallbackQuery, state: FSMContext, user_settings: UserSettings, theme: Theme) -> None:
    target_lang = callback.data.split(":")[1]
    data = await state.get_data()
    text_to_trans = data.get("translate_text")
    await state.clear()

    if not text_to_trans:
        await callback.answer("No text found to translate. Please try again.", show_alert=True)
        return

    if callback.message:
        await callback.message.delete()

    sys_prompt = f"You are AVEN AI translation engine. Accurately translate the input text into {target_lang}. Preserve tone and formatting."
    prompt = f"Translate the following text into {target_lang}:\n\n{text_to_trans}"
    if callback.message:
        await run_ai_task(callback.message, user_settings, theme, prompt, sys_prompt, task_name="translate")
    await callback.answer()
