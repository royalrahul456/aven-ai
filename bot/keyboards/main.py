"""Main navigation and menu keyboards."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.themes import get_theme


def get_start_keyboard(theme_id: str = "aven") -> InlineKeyboardMarkup:
    theme = get_theme(theme_id)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💬 Chat", callback_data="nav:chat"),
                InlineKeyboardButton(text="🎨 Image", callback_data="nav:image")
            ],
            [
                InlineKeyboardButton(text="🧠 Think", callback_data="nav:think"),
                InlineKeyboardButton(text="🌐 Web", callback_data="nav:web")
            ],
            [
                InlineKeyboardButton(text="🤖 Models", callback_data="nav:models"),
                InlineKeyboardButton(text="⚙️ Settings", callback_data="nav:settings")
            ],
            [
                InlineKeyboardButton(text="🏓 Ping", callback_data="nav:ping"),
                InlineKeyboardButton(text="❓ Help", callback_data="nav:help")
            ]
        ]
    )


def get_back_keyboard(target: str = "nav:start") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Back", callback_data=target)]
        ]
    )


def get_ping_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Ping Again", callback_data="nav:ping"),
                InlineKeyboardButton(text="🔙 Back", callback_data="nav:start")
            ]
        ]
    )


def get_help_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚀 Basic", callback_data="help_cat:basic"),
                InlineKeyboardButton(text="🧠 AI Tools", callback_data="help_cat:tools")
            ],
            [
                InlineKeyboardButton(text="💻 Code", callback_data="help_cat:code"),
                InlineKeyboardButton(text="⚙️ Settings", callback_data="help_cat:settings")
            ],
            [
                InlineKeyboardButton(text="🌐 Special", callback_data="help_cat:special"),
                InlineKeyboardButton(text="📋 Full List", callback_data="help_cat:all")
            ],
            [
                InlineKeyboardButton(text="🔙 Back", callback_data="nav:start")
            ]
        ]
    )


def get_response_action_keyboard() -> InlineKeyboardMarkup:
    """Action bar attached below AI answers with rich emoji buttons."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Regenerate", callback_data="ai_act:regen"),
                InlineKeyboardButton(text="🧠 Think", callback_data="ai_act:think"),
                InlineKeyboardButton(text="💡 Explain", callback_data="ai_act:explain"),
                InlineKeyboardButton(text="🗑 Delete", callback_data="ai_act:del")
            ]
        ]
    )

