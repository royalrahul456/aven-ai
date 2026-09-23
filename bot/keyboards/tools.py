"""Keyboards for AI Tools and interactive utilities."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_language_selector_keyboard(action_prefix: str) -> InlineKeyboardMarkup:
    """Creates a quick language selection keyboard."""
    languages = [
        ("English", "English"),
        ("Spanish", "Spanish"),
        ("French", "French"),
        ("German", "German"),
        ("Chinese", "Chinese"),
        ("Japanese", "Japanese"),
        ("Russian", "Russian"),
        ("Hindi", "Hindi"),
    ]
    rows = []
    current_row = []
    for label, code in languages:
        current_row.append(InlineKeyboardButton(text=label, callback_data=f"{action_prefix}:{code}"))
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)

    rows.append([InlineKeyboardButton(text="🔙 Cancel", callback_data="nav:start")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_code_lang_keyboard(action_prefix: str = "convert_to") -> InlineKeyboardMarkup:
    """Creates programming language selector keyboard."""
    code_langs = [
        ("Python", "Python"),
        ("JavaScript", "JavaScript"),
        ("TypeScript", "TypeScript"),
        ("Go", "Go"),
        ("Rust", "Rust"),
        ("C++", "C++"),
        ("Java", "Java"),
        ("C#", "C#"),
    ]
    rows = []
    current_row = []
    for label, code in code_langs:
        current_row.append(InlineKeyboardButton(text=label, callback_data=f"{action_prefix}:{code}"))
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)

    rows.append([InlineKeyboardButton(text="🔙 Cancel", callback_data="nav:start")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
