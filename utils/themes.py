"""Interface themes and typography styling for AVEN AI."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
from utils.fonts import to_sans_bold, to_serif_bold, to_mono, to_double_struck, to_small_caps


@dataclass
class Theme:
    id: str
    name: str
    emoji: str
    header_prefix: str
    font_style: str
    bullet: str
    divider: str
    badge_style: str
    accent_emoji: str
    code_emoji: str
    success_emoji: str
    warning_emoji: str
    error_emoji: str

    def format_title(self, text: str) -> str:
        """Formats titles according to the theme's typography."""
        if self.font_style == "sans_bold":
            return to_sans_bold(text)
        elif self.font_style == "serif_bold":
            return to_serif_bold(text)
        elif self.font_style == "mono":
            return to_mono(text)
        elif self.font_style == "double_struck":
            return to_double_struck(text)
        elif self.font_style == "small_caps":
            return to_small_caps(text)
        return text


THEMES: Dict[str, Theme] = {
    "aven": Theme(
        id="aven",
        name="⚡ AVEN PRO",
        emoji="⚡",
        header_prefix="⚡",
        font_style="sans_bold",
        bullet="✦",
        divider="━" * 22,
        badge_style="⚡",
        accent_emoji="✨",
        code_emoji="💻",
        success_emoji="✅",
        warning_emoji="⚠️",
        error_emoji="❌",
    ),
    "dark": Theme(
        id="dark",
        name="🌑 OBSIDIAN",
        emoji="🌑",
        header_prefix="✦",
        font_style="serif_bold",
        bullet="▪",
        divider="─" * 22,
        badge_style="🌑",
        accent_emoji="🔮",
        code_emoji="🖥",
        success_emoji="✔️",
        warning_emoji="⚠️",
        error_emoji="🚫",
    ),
    "cyber": Theme(
        id="cyber",
        name="💎 CYBERPUNK",
        emoji="💎",
        header_prefix="💠",
        font_style="mono",
        bullet="🔹",
        divider="═" * 22,
        badge_style="💎",
        accent_emoji="⚡",
        code_emoji="📟",
        success_emoji="💎",
        warning_emoji="⚠️",
        error_emoji="🛑",
    ),
    "neon": Theme(
        id="neon",
        name="🔮 VIOLET NEON",
        emoji="🔮",
        header_prefix="🟣",
        font_style="double_struck",
        bullet="◈",
        divider="┈" * 22,
        badge_style="🔮",
        accent_emoji="✨",
        code_emoji="🕹",
        success_emoji="✨",
        warning_emoji="⚠️",
        error_emoji="❌",
    ),
    "light": Theme(
        id="light",
        name="☀️ SOLAR GOLD",
        emoji="☀️",
        header_prefix="☀️",
        font_style="sans_bold",
        bullet="▫",
        divider="·" * 26,
        badge_style="🌟",
        accent_emoji="🌟",
        code_emoji="📝",
        success_emoji="✅",
        warning_emoji="⚠️",
        error_emoji="❌",
    ),
    "stellar": Theme(
        id="stellar",
        name="🪐 STELLAR",
        emoji="🪐",
        header_prefix="🪐",
        font_style="small_caps",
        bullet="✧",
        divider="⋯" * 24,
        badge_style="🌌",
        accent_emoji="✨",
        code_emoji="🛰",
        success_emoji="🌟",
        warning_emoji="⚠️",
        error_emoji="💥",
    ),
}


def get_theme(theme_id: str | None) -> Theme:
    if not theme_id or theme_id not in THEMES:
        return THEMES["aven"]
    return THEMES[theme_id]
