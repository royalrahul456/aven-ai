"""Rich formatting and safe Telegram Markdown/HTML conversion utilities with typography enhancements."""
from __future__ import annotations

import html
import re
from typing import Optional
from utils.themes import Theme, get_theme
from utils.fonts import to_sans_bold, to_serif_bold, to_mono


def escape_html(text: str) -> str:
    """Escapes raw text for safe inclusion in Telegram HTML messages."""
    return html.escape(text, quote=False)


def markdown_to_telegram_html(markdown_text: str, theme: Optional[Theme] = None) -> str:
    """
    Converts standard LLM Markdown into stylish Telegram-compatible HTML.
    Supports:
      - Multi-line fenced code blocks with language tag
      - Inline code: `code` -> <code>code</code>
      - Blockquotes: lines starting with > -> <blockquote>...</blockquote>
      - Bold: **bold** or __bold__ -> <b>bold</b>
      - Italic: *italic* or _italic_ -> <i>italic</i>
      - Strikethrough: ~~strike~~ -> <s>strike</s>
      - Links: [title](url) -> <a href="url">title</a>
      - Headings: ### Header -> stylized <b>Header</b>
    """
    if not markdown_text:
        return ""

    bullet_sym = theme.bullet if theme else "•"

    # Step 1: Protect and extract fenced code blocks
    code_blocks = []
    
    def code_block_replacer(match):
        lang = match.group(1) or ""
        code_content = match.group(2)
        escaped_code = escape_html(code_content)
        index = len(code_blocks)
        if lang:
            code_blocks.append(f'<pre><code class="language-{escape_html(lang.strip())}">{escaped_code}</code></pre>')
        else:
            code_blocks.append(f'<pre><code>{escaped_code}</code></pre>')
        return f"__CODE_BLOCK_PLACEHOLDER_{index}__"

    text = re.sub(
        r"```([a-zA-Z0-9_\-\+]*)\n?(.*?)```",
        code_block_replacer,
        markdown_text,
        flags=re.DOTALL
    )

    # Step 2: Protect and extract inline code
    inline_codes = []

    def inline_code_replacer(match):
        code_content = match.group(1)
        escaped_code = escape_html(code_content)
        index = len(inline_codes)
        inline_codes.append(f"<code>{escaped_code}</code>")
        return f"__INLINE_CODE_PLACEHOLDER_{index}__"

    text = re.sub(r"`([^`\n]+)`", inline_code_replacer, text)

    # Step 3: Handle blockquotes (lines starting with >)
    lines = text.split("\n")
    processed_lines = []
    in_quote = False
    quote_acc = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("&gt;") or stripped.startswith(">"):
            in_quote = True
            if stripped.startswith("&gt;"):
                clean = re.sub(r"^&gt;\s?", "", stripped)
            else:
                clean = re.sub(r"^>\s?", "", stripped)
            quote_acc.append(clean)
        else:
            if in_quote:
                quote_text = "\n".join(quote_acc)
                processed_lines.append(f"<blockquote>{quote_text}</blockquote>")
                quote_acc = []
                in_quote = False
            processed_lines.append(line)

    if in_quote:
        quote_text = "\n".join(quote_acc)
        processed_lines.append(f"<blockquote>{quote_text}</blockquote>")

    text = "\n".join(processed_lines)

    # Step 4: Normalize bullet points (* item or - item -> bullet item)
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        if re.match(r"^\s*[\*\-]\s+(.+)$", line) and not line.strip().startswith("__CODE_BLOCK_PLACEHOLDER_"):
            line = re.sub(r"^\s*[\*\-]\s+", f"{bullet_sym} ", line)
        cleaned_lines.append(line)
    text = "\n".join(cleaned_lines)

    # Step 5: Escape remaining HTML in text (outside code placeholders and blockquotes)
    parts = re.split(r"(__CODE_BLOCK_PLACEHOLDER_\d+__|__INLINE_CODE_PLACEHOLDER_\d+__|<blockquote>.*?</blockquote>)", text, flags=re.DOTALL)
    for i in range(len(parts)):
        part = parts[i]
        if part.startswith("__CODE_BLOCK_PLACEHOLDER_") or part.startswith("__INLINE_CODE_PLACEHOLDER_"):
            continue
        elif part.startswith("<blockquote>") and part.endswith("</blockquote>"):
            inner = part[12:-13]
            escaped_inner = escape_html(inner)
            escaped_inner = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped_inner)
            escaped_inner = re.sub(r"__(.+?)__", r"<b>\1</b>", escaped_inner)
            escaped_inner = re.sub(r"(?<!\*)\*([^\*\n]+)\*(?!\*)", r"<i>\1</i>", escaped_inner)
            escaped_inner = re.sub(r"(?<!_)_([^_\n]+)_(?!_)", r"<i>\1</i>", escaped_inner)
            parts[i] = f"<blockquote>{escaped_inner}</blockquote>"
        else:
            escaped_part = escape_html(part)
            # Headers: ### Header -> <b>▪ Header</b>
            escaped_part = re.sub(r"^(?:#{1,6})\s+(.+)$", rf"\n<b>{bullet_sym} \1</b>", escaped_part, flags=re.MULTILINE)
            # Bold: **text** or __text__
            escaped_part = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped_part)
            escaped_part = re.sub(r"__(.+?)__", r"<b>\1</b>", escaped_part)
            # Italic: *text* or _text_
            escaped_part = re.sub(r"(?<!\*)\*([^\*\n]+)\*(?!\*)", r"<i>\1</i>", escaped_part)
            escaped_part = re.sub(r"(?<!_)_([^_\n]+)_(?!_)", r"<i>\1</i>", escaped_part)
            # Strikethrough: ~~text~~
            escaped_part = re.sub(r"~~(.+?)~~", r"<s>\1</s>", escaped_part)
            # Links: [label](url)
            escaped_part = re.sub(r"\[([^\]]+)\]\((https?://[^\)]+)\)", r'<a href="\2">\1</a>', escaped_part)
            parts[i] = escaped_part

    text = "".join(parts)

    # Step 6: Restore inline codes and code blocks
    for idx, inline_html in enumerate(inline_codes):
        text = text.replace(f"__INLINE_CODE_PLACEHOLDER_{idx}__", inline_html)

    for idx, block_html in enumerate(code_blocks):
        text = text.replace(f"__CODE_BLOCK_PLACEHOLDER_{idx}__", block_html)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def format_aven_response_card(body: str, model_name: str, theme_id: Optional[str] = "aven") -> str:
    """Formats full bot answer card with beautiful theme headers and distinct typography."""
    theme: Theme = get_theme(theme_id)
    formatted_body = markdown_to_telegram_html(body, theme=theme)
    
    title_styled = theme.format_title("AVEN AI")
    header = f"<blockquote><b>{theme.header_prefix} {title_styled}</b> │ <code>{model_name}</code></blockquote>"
    return f"{header}\n\n{formatted_body}"
