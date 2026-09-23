"""AI Image Generation handlers using FLUX.1 architecture and smart AI enhancement."""
from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database.repository import repo, UserSettings
from providers.image import flux_provider
from utils.themes import Theme
from utils.fonts import to_sans_bold
from utils.logger import logger
from bot.keyboards.main import get_back_keyboard
from bot.states.form_states import InteractivePromptForm

router = Router(name="image_router")


def get_image_action_keyboard(prompt: str) -> InlineKeyboardMarkup:
    """Action bar with quick style buttons and reroll."""
    import base64
    # Truncate prompt safely for callback data if needed
    safe_p = prompt[:30]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Reroll", callback_data=f"img_act:reroll:{safe_p}"),
                InlineKeyboardButton(text="📸 Realism", callback_data=f"img_act:flux-realism:{safe_p}"),
            ],
            [
                InlineKeyboardButton(text="🎌 Anime", callback_data=f"img_act:flux-anime:{safe_p}"),
                InlineKeyboardButton(text="🎨 3D Render", callback_data=f"img_act:flux-3d:{safe_p}"),
            ]
        ]
    )


async def execute_image_generation(
    message: Message,
    user_settings: UserSettings,
    theme: Theme,
    prompt: str,
    aspect_ratio: str = "1:1",
    style: str = "flux-realism"
) -> None:
    """Core pipeline to generate and deliver FLUX.1 images with prompt enrichment."""
    if not prompt or not prompt.strip():
        return

    clean_prompt = prompt.strip()
    title = theme.format_title("FLUX.1 STUDIO")

    thinking_msg = await message.reply(
        f"<blockquote><b>🎨 {theme.header_prefix} {title}</b>\n\n"
        f"<i>Enhancing prompt & rendering in 8K...</i>\n"
        f"<code>{clean_prompt[:45]}...</code></blockquote>",
        parse_mode="HTML"
    )

    try:
        image_bytes, seed, final_prompt = await flux_provider.generate_image(
            prompt=clean_prompt,
            aspect_ratio=aspect_ratio,
            style=style
        )

        photo_file = BufferedInputFile(image_bytes, filename=f"flux_{seed}.jpg")
        badge = theme.format_title("FLUX.1 HD ARTWORK")
        b = theme.bullet

        caption = (
            f"<blockquote><b>🎨 {badge}</b>\n\n"
            f"{b} <b>Prompt:</b> <code>{clean_prompt}</code>\n"
            f"{b} <b>Enhanced:</b> <i>{final_prompt}</i>\n"
            f"{b} <b>Model:</b> <code>FLUX.1 Realism</code>\n"
            f"{b} <b>Seed:</b> <code>{seed}</code></blockquote>"
        )

        # Send photo directly as reply to the user's prompt
        await message.reply_photo(
            photo=photo_file,
            caption=caption,
            parse_mode="HTML",
            reply_markup=get_image_action_keyboard(clean_prompt)
        )

        # Clean up thinking notice
        try:
            await thinking_msg.delete()
        except Exception:
            pass

        # Record usage
        await repo.record_usage(
            user_id=user_settings.user_id,
            model_used="flux_1",
            request_type="image"
        )

    except Exception as e:
        logger.exception(f"Error during FLUX image generation: {e}")
        await thinking_msg.edit_text(
            f"<blockquote><b>⚠️ {theme.format_title('IMAGE GENERATION FAILED')}</b>\n\n"
            f"Could not generate image. Please try again with a different prompt.</blockquote>",
            parse_mode="HTML"
        )


@router.message(Command("image"))
@router.message(Command("imagine"))
@router.message(Command("draw"))
@router.message(Command("flux"))
async def cmd_image(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    args = (message.text or "").partition(" ")[2].strip()
    if not args:
        await state.set_state(InteractivePromptForm.waiting_for_image_input)
        title = theme.format_title("FLUX.1 IMAGE STUDIO")
        text = (
            f"<blockquote><b>🎨 {theme.header_prefix} {title}</b>\n\n"
            f"Describe the image you want to generate.\n\n"
            f"<i>Example: 'A futuristic cybernetic samurai in a rainy neon Tokyo alley'</i></blockquote>"
        )
        await message.reply(text, parse_mode="HTML", reply_markup=get_back_keyboard("nav:start"))
        return

    await execute_image_generation(message, user_settings, theme, args)


@router.callback_query(F.data == "nav:image")
async def cb_image(callback: CallbackQuery, theme: Theme, state: FSMContext) -> None:
    await state.set_state(InteractivePromptForm.waiting_for_image_input)
    title = theme.format_title("FLUX.1 IMAGE STUDIO")
    text = (
        f"<blockquote><b>🎨 {theme.header_prefix} {title}</b>\n\n"
        f"Send any prompt to generate high-resolution artwork.\n\n"
        f"<i>Example: 'A majestic golden eagle soaring above snow mountains at sunset'</i></blockquote>"
    )
    if callback.message:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_back_keyboard("nav:start"))
    await callback.answer()


@router.callback_query(F.data.startswith("img_act:"))
async def cb_img_act(callback: CallbackQuery, user_settings: UserSettings, theme: Theme) -> None:
    parts = callback.data.split(":", 2)
    action = parts[1]
    prompt = parts[2] if len(parts) > 2 else "A stunning cinematic artwork"

    await callback.answer("🎨 Generating new image...")
    style = "flux-realism"
    if action in ("flux-anime", "flux-3d", "flux-realism"):
        style = action

    if callback.message:
        await execute_image_generation(callback.message, user_settings, theme, prompt, style=style)


@router.message(InteractivePromptForm.waiting_for_image_input)
async def process_image_input(message: Message, user_settings: UserSettings, theme: Theme, state: FSMContext) -> None:
    await state.clear()
    await execute_image_generation(message, user_settings, theme, message.text or "")
