"""Unicode typography and font styling utilities for Telegram UI."""
from __future__ import annotations
import unicodedata

# Unicode offset mappings for various mathematical alphanumeric characters
_NORMAL = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

# Sans-Serif Bold
_SANS_BOLD = (
    "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇"
    "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭"
    "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
)

# Serif Bold
_SERIF_BOLD = (
    "𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳"
    "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙"
    "𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗"
)

# Sans-Serif Italic
_SANS_ITALIC = (
    "𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻"
    "𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡"
    "0123456789"
)

# Monospace
_MONO = (
    "𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣"
    "𝙰𝙱𝙲𝙳𝙴𝙵𝙶𝙷𝙸𝙹𝙺𝙻𝙼𝙽𝙾𝙿𝚀𝚁𝚂𝚃𝚄𝚅𝚆𝚇𝚈𝚉"
    "𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿"
)

# Double-Struck
_DOUBLE_STRUCK = (
    "𝕒𝕓𝕔𝕕𝕖𝕗𝕘𝕙𝕚𝕛𝕜𝕝𝕞𝕟𝕠𝕡𝕢𝕣𝕤𝕥𝕦𝕧𝕨𝕩𝕪𝕫"
    "𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ"
    "𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡"
)

# Small Caps
_SMALL_CAPS_MAP = {
    "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ғ", "g": "ɢ", "h": "ʜ",
    "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ",
    "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x",
    "y": "ʏ", "z": "ᴢ",
    "A": "ᴀ", "B": "ʙ", "C": "ᴄ", "D": "ᴅ", "E": "ᴇ", "F": "ғ", "G": "ɢ", "H": "ʜ",
    "I": "ɪ", "J": "ᴊ", "K": "ᴋ", "L": "ʟ", "M": "ᴍ", "N": "ɴ", "O": "ᴏ", "P": "ᴘ",
    "Q": "ǫ", "R": "ʀ", "S": "s", "T": "ᴛ", "U": "ᴜ", "V": "ᴠ", "W": "ᴡ", "X": "x",
    "Y": "ʏ", "Z": "ᴢ",
}

_TRANS_SANS_BOLD = str.maketrans(_NORMAL, _SANS_BOLD)
_TRANS_SERIF_BOLD = str.maketrans(_NORMAL, _SERIF_BOLD)
_TRANS_SANS_ITALIC = str.maketrans(_NORMAL, _SANS_ITALIC)
_TRANS_MONO = str.maketrans(_NORMAL, _MONO)
_TRANS_DOUBLE_STRUCK = str.maketrans(_NORMAL, _DOUBLE_STRUCK)


def to_sans_bold(text: str) -> str:
    """Converts text to stylish mathematical Sans-Serif Bold."""
    return text.translate(_TRANS_SANS_BOLD)


def to_serif_bold(text: str) -> str:
    """Converts text to elegant Serif Bold."""
    return text.translate(_TRANS_SERIF_BOLD)


def to_sans_italic(text: str) -> str:
    """Converts text to Sans-Serif Italic."""
    return text.translate(_TRANS_SANS_ITALIC)


def to_mono(text: str) -> str:
    """Converts text to mathematical Monospace."""
    return text.translate(_TRANS_MONO)


def to_double_struck(text: str) -> str:
    """Converts text to Double-Struck / Blackboard bold."""
    return text.translate(_TRANS_DOUBLE_STRUCK)


def to_small_caps(text: str) -> str:
    """Converts text to aesthetic Small Caps."""
    return "".join(_SMALL_CAPS_MAP.get(c, c) for c in text)


def style_header(text: str, style: str = "sans_bold") -> str:
    """Applies a typography style to headers."""
    if style == "sans_bold":
        return to_sans_bold(text)
    elif style == "serif_bold":
        return to_serif_bold(text)
    elif style == "mono":
        return to_mono(text)
    elif style == "double_struck":
        return to_double_struck(text)
    elif style == "small_caps":
        return to_small_caps(text)
    return text
