"""Keyboards for Model selection, information, and switching."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import MODELS_METADATA
from providers.registry import registry


def get_models_keyboard(current_model_id: str) -> InlineKeyboardMarkup:
    """Creates the model selector grid with active status badges."""
    def _btn_text(m_id: str) -> str:
        meta = MODELS_METADATA.get(m_id)
        if not meta:
            return m_id
        is_active = (m_id == current_model_id)
        prefix = "✅ " if is_active else ""
        return f"{prefix}{meta.display_name}"

    buttons = [
        [
            InlineKeyboardButton(text=_btn_text("aven_flash"), callback_data="model_view:aven_flash"),
            InlineKeyboardButton(text=_btn_text("aven_swift"), callback_data="model_view:aven_swift")
        ],
        [
            InlineKeyboardButton(text=_btn_text("aven_pro"), callback_data="model_view:aven_pro"),
            InlineKeyboardButton(text=_btn_text("aven_claude"), callback_data="model_view:aven_claude")
        ],
        [
            InlineKeyboardButton(text=_btn_text("aven_ultra"), callback_data="model_view:aven_ultra"),
            InlineKeyboardButton(text=_btn_text("aven_opus"), callback_data="model_view:aven_opus")
        ],
        [
            InlineKeyboardButton(text=_btn_text("aven_mistral"), callback_data="model_view:aven_mistral"),
            InlineKeyboardButton(text=_btn_text("aven_web"), callback_data="model_view:aven_web"),
        ],
        [
            InlineKeyboardButton(text=_btn_text("aven_auto"), callback_data="model_view:aven_auto"),
        ],
        [
            InlineKeyboardButton(text="🔙 Back", callback_data="nav:start")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_model_detail_keyboard(model_id: str, is_active: bool) -> InlineKeyboardMarkup:
    """Buttons displayed on individual model preview cards."""
    action_btn = (
        InlineKeyboardButton(text="⚡ Active Model", callback_data="noop")
        if is_active
        else InlineKeyboardButton(text="✅ Select Model", callback_data=f"model_select:{model_id}")
    )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                action_btn,
                InlineKeyboardButton(text="ℹ️ Model Info", callback_data=f"model_info:{model_id}")
            ],
            [
                InlineKeyboardButton(text="🔙 Back to Models", callback_data="nav:models")
            ]
        ]
    )
