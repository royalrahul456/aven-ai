"""Keyboards for Bot Settings, Theme Selector, Temperature, Instructions, and Reset."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.themes import THEMES


def get_settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🤖 Model", callback_data="nav:models"),
                InlineKeyboardButton(text="🎨 Theme", callback_data="nav:theme")
            ],
            [
                InlineKeyboardButton(text="🌡 Temperature", callback_data="nav:temperature"),
                InlineKeyboardButton(text="📝 Instructions", callback_data="nav:instructions")
            ],
            [
                InlineKeyboardButton(text="🔄 Reset", callback_data="settings:reset_confirm")
            ],
            [
                InlineKeyboardButton(text="🔙 Back", callback_data="nav:start")
            ]
        ]
    )


def get_theme_keyboard(current_theme_id: str) -> InlineKeyboardMarkup:
    buttons = []
    theme_keys = list(THEMES.keys())
    # Group in rows of 2
    row = []
    for k in theme_keys:
        th = THEMES[k]
        is_active = (k == current_theme_id)
        btn_text = f"✅ {th.name}" if is_active else th.name
        row.append(InlineKeyboardButton(text=btn_text, callback_data=f"theme_set:{k}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="nav:settings")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_temperature_keyboard(current_temp: float) -> InlineKeyboardMarkup:
    temp_options = [
        (0.2, "❄️ 0.2"),
        (0.5, "⚖️ 0.5"),
        (0.7, "🔥 0.7"),
        (1.0, "🎨 1.0"),
        (1.2, "🚀 1.2"),
    ]
    row1 = []
    row2 = []
    for idx, (val, label) in enumerate(temp_options):
        is_active = abs(val - current_temp) < 0.05
        btn_text = f"✅ {val}" if is_active else label
        if idx < 3:
            row1.append(InlineKeyboardButton(text=btn_text, callback_data=f"temp_set:{val}"))
        else:
            row2.append(InlineKeyboardButton(text=btn_text, callback_data=f"temp_set:{val}"))

    return InlineKeyboardMarkup(
        inline_keyboard=[
            row1,
            row2,
            [InlineKeyboardButton(text="🔙 Back", callback_data="nav:settings")]
        ]
    )


def get_instructions_keyboard(has_instructions: bool = False) -> InlineKeyboardMarkup:
    action_row = [InlineKeyboardButton(text="✏️ Edit", callback_data="instructions:edit")]
    if has_instructions:
        action_row.append(InlineKeyboardButton(text="🗑 Clear", callback_data="instructions:clear"))

    return InlineKeyboardMarkup(
        inline_keyboard=[
            action_row,
            [InlineKeyboardButton(text="🔙 Back", callback_data="nav:settings")]
        ]
    )


def get_reset_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Confirm Reset", callback_data="settings:do_reset"),
                InlineKeyboardButton(text="❌ Cancel", callback_data="nav:settings")
            ]
        ]
    )
