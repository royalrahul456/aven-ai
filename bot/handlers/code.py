"""Code assistance handlers: /code, /debug, /explaincode, /optimize, /review, /convert."""
from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from database.repository import repo, UserSettings
from providers.registry import registry
from utils.formatting import markdown_to_telegram_html, format_aven_response_card
from utils.splitter import prepare_response_delivery
from bot.keyboards.main import get_back_keyboard, get_response_action_keyboard
from bot.keyboards.tools import get_code_lang_keyboard
from bot.states.form_states import CodeConvertForm, InteractivePromptForm

router = Router(name="code_router")


async def run_code_task(
    message: Message,
    user_settings: UserSettings,
    theme: Theme,
    prompt: str,
    system_prompt: str,
    task_name: str = "code"
) -> None:
    """Helper to run code tasks with code-specific system prompting and formatting."""
    title = theme.format_title("AVEN")
    thinking_msg = await message.reply(
        f"<blockquote><b>{theme.code_emoji} {title} is synthesizing code...</b></blockquote>",
        parse_mode="HTML"
    )

    if user_settings.custom_instructions:
        system_prompt = f"{system_prompt}\n\nUser Custom Instructions:\n{user_settings.custom_instructions}"

    # Auto or user's selected model
    model_to_use = user_settings.model

    try:
        response = await registry.execute_query(
            model_id=model_to_use,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=min(user_settings.temperature, 0.3)  # Lower temperature for coding accuracy
        )

        full_html = format_aven_response_card(response.text, f"{response.model_name} • Code", user_settings.theme)

        chunks, is_file, file_buffer = prepare_response_delivery(full_html)

        if is_file and file_buffer:
            file_attachment = BufferedInputFile(file_buffer.getvalue(), filename=f"aven_{task_name}.txt")
            await message.reply_document(file_attachment, caption=f"💻 {task_name.capitalize()} output")

        for i, chunk in enumerate(chunks):
            if i == 0:
                try:
                    await thinking_msg.edit_text(chunk, parse_mode="HTML", disable_web_page_preview=True)
                except Exception:
                    await thinking_msg.edit_text(response.text[:3500], disable_web_page_preview=True)
            else:
                try:
                    await message.reply(chunk, parse_mode="HTML", disable_web_page_preview=True)
                except Exception:
                    await message.reply(chunk, disable_web_page_preview=True)

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
            "⚠️ <b>Something went wrong</b>\n\nAVEN couldn't process your code request right now. Please try again.",
            parse_mode="HTML"
        )


# --- /code ---
@router.message(Command("code"))
async def cmd_code(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    args = (message.text or "").partition(" ")[2].strip()
    if not args:
        await state.set_state(InteractivePromptForm.waiting_for_code_input)
        await message.reply("<blockquote><b>💻 Code Generator</b>\n\nDescribe the program, algorithm, or function you need.</blockquote>", parse_mode="HTML")
        return

    sys_prompt = (
        "You are AVEN AI code assistant. Provide clean, correct, concise code inside markdown code blocks (```python). "
        "Keep explanations short and direct (1-2 sentences maximum)."
    )
    await run_code_task(message, user_settings, theme, args, sys_prompt, task_name="code")


@router.message(InteractivePromptForm.waiting_for_code_input)
async def process_code_input(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    await state.clear()
    sys_prompt = (
        "You are AVEN AI code assistant. Provide clean, correct, concise code inside markdown code blocks. "
        "Keep explanations short and direct (1-2 sentences maximum)."
    )
    await run_code_task(message, user_settings, theme, message.text or "", sys_prompt, task_name="code")


# --- /debug ---
@router.message(Command("debug"))
async def cmd_debug(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    args = (message.text or "").partition(" ")[2].strip()
    if not args:
        await state.set_state(InteractivePromptForm.waiting_for_debug_input)
        await message.reply("<blockquote><b>🐞 Code Debugger</b>\n\nPaste your code snippet and error messages to debug.</blockquote>", parse_mode="HTML")
        return

    sys_prompt = (
        "You are AVEN AI code debugger. Identify the bug, show the corrected code, and provide a 1-2 sentence explanation of the fix."
    )
    await run_code_task(message, user_settings, theme, args, sys_prompt, task_name="debug")


@router.message(InteractivePromptForm.waiting_for_debug_input)
async def process_debug_input(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    await state.clear()
    sys_prompt = "You are AVEN AI code debugger. Identify the bug, show the corrected code, and provide a 1-2 sentence explanation of the fix."
    await run_code_task(message, user_settings, theme, message.text or "", sys_prompt, task_name="debug")


# --- /explaincode ---
@router.message(Command("explaincode"))
async def cmd_explaincode(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    args = (message.text or "").partition(" ")[2].strip()
    if not args:
        await state.set_state(InteractivePromptForm.waiting_for_explain_input)
        await message.reply("<blockquote><b>📖 Code Explainer</b>\n\nPaste the code you want explained.</blockquote>", parse_mode="HTML")
        return

    sys_prompt = "You are AVEN AI. Explain what the given code does concisely in clear, simple bullet points."
    await run_code_task(message, user_settings, theme, args, sys_prompt, task_name="explaincode")


# --- /optimize ---
@router.message(Command("optimize"))
async def cmd_optimize(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    args = (message.text or "").partition(" ")[2].strip()
    if not args:
        await state.set_state(InteractivePromptForm.waiting_for_optimize_input)
        await message.reply("<blockquote><b>⚡ Code Optimizer</b>\n\nPaste the code you want optimized.</blockquote>", parse_mode="HTML")
        return

    sys_prompt = (
        "You are AVEN AI code optimizer. Refactor the code for peak efficiency and explain the improvement in 1-2 concise bullet points."
    )
    await run_code_task(message, user_settings, theme, args, sys_prompt, task_name="optimize")


# --- /optimize ---
@router.message(InteractivePromptForm.waiting_for_optimize_input)
async def process_optimize_input(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    await state.clear()
    sys_prompt = "You are AVEN AI code optimizer. Refactor the code for peak efficiency and explain the improvement in 1-2 concise bullet points."
    await run_code_task(message, user_settings, theme, message.text or "", sys_prompt, task_name="optimize")


# --- /review ---
@router.message(Command("review"))
async def cmd_review(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    args = (message.text or "").partition(" ")[2].strip()
    if not args:
        await state.set_state(InteractivePromptForm.waiting_for_review_input)
        await message.reply("<blockquote><b>🔍 Code Reviewer</b>\n\nPaste your code for a concise code review.</blockquote>", parse_mode="HTML")
        return

    sys_prompt = (
        "You are AVEN AI code reviewer. Provide a concise, high-value code review covering Security, Performance, and Quick Recommendations in bullet points."
    )
    await run_code_task(message, user_settings, theme, args, sys_prompt, task_name="review")


# --- /review input ---
@router.message(InteractivePromptForm.waiting_for_review_input)
async def process_review_input(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    await state.clear()
    sys_prompt = "You are AVEN AI code reviewer. Provide a concise, high-value code review in bullet points."
    await run_code_task(message, user_settings, theme, message.text or "", sys_prompt, task_name="review")


# --- /convert ---
@router.message(Command("convert"))
async def cmd_convert(message: Message, state: FSMContext) -> None:
    args = (message.text or "").partition(" ")[2].strip()
    if args:
        await state.update_data(convert_code=args)
        await message.reply(
            "<blockquote><b>🔄 Convert Code</b>\n\nSelect the target programming language:</blockquote>",
            parse_mode="HTML",
            reply_markup=get_code_lang_keyboard("convert_to")
        )
    else:
        await state.set_state(CodeConvertForm.waiting_for_code)
        await message.reply("<blockquote><b>🔄 Convert Code</b>\n\nPaste the code you want converted to another language.</blockquote>", parse_mode="HTML")


@router.message(CodeConvertForm.waiting_for_code)
async def process_convert_code_input(message: Message, state: FSMContext) -> None:
    code = (message.text or "").strip()
    if not code:
        await message.reply("Please send valid code.")
        return
    await state.update_data(convert_code=code)
    await message.reply(
        "<blockquote><b>🔄 Select Target Language:</b></blockquote>",
        parse_mode="HTML",
        reply_markup=get_code_lang_keyboard("convert_to")
    )


@router.callback_query(F.data.startswith("convert_to:"))
async def cb_convert_to(callback: CallbackQuery, state: FSMContext, user_settings: UserSettings, theme: Theme) -> None:
    target_lang = callback.data.split(":")[1]
    data = await state.get_data()
    code_to_convert = data.get("convert_code")
    await state.clear()

    if not code_to_convert:
        await callback.answer("No code found to convert. Please try again.", show_alert=True)
        return

    if callback.message:
        await callback.message.delete()

    sys_prompt = f"You are AVEN AI code converter. Accurately rewrite the input code in {target_lang}, using idiomatic conventions and best practices."
    prompt = f"Convert the following code into {target_lang}:\n\n{code_to_convert}"
    if callback.message:
        await run_code_task(callback.message, user_settings, theme, prompt, sys_prompt, task_name="convert")
    await callback.answer()
