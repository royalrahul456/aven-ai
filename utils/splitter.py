"""Message splitting utilities to keep responses within Telegram limits without breaking markup."""
from __future__ import annotations

import io
import re
from typing import List, Tuple


SAFE_CHUNK_SIZE = 3800  # Safe boundary well below Telegram's 4096 char limit


def split_message(text: str, max_length: int = SAFE_CHUNK_SIZE) -> List[str]:
    """
    Splits a message into chunks that fit within Telegram's character limit.
    Ensures Markdown code blocks and tags are not severed improperly.
    """
    if not text:
        return []
    if len(text) <= max_length:
        return [text]

    chunks: List[str] = []
    lines = text.split("\n")
    current_chunk = []
    current_length = 0
    in_code_block = False
    current_code_lang = ""

    for line in lines:
        line_len = len(line) + 1  # +1 for newline

        # Check for code fence
        code_fence_match = re.match(r"^```([a-zA-Z0-9_\-\+]*)\s*$", line.strip())
        if code_fence_match:
            if not in_code_block:
                in_code_block = True
                current_code_lang = code_fence_match.group(1)
            else:
                in_code_block = False
                current_code_lang = ""

        # If adding this line exceeds max length, finalize current chunk
        if current_length + line_len > max_length and current_chunk:
            if in_code_block:
                # Close code block in current chunk
                current_chunk.append("```")
                chunks.append("\n".join(current_chunk))
                # Reopen code block in next chunk
                current_chunk = [f"```{current_code_lang}", line]
                current_length = len(current_chunk[0]) + 1 + line_len
            else:
                chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_length = line_len
        else:
            current_chunk.append(line)
            current_length += line_len

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


def prepare_response_delivery(text: str) -> Tuple[List[str], bool, io.BytesIO | None]:
    """
    Analyzes response size:
    - If <= 4000 characters: returns [text], False, None
    - If 4000 < length <= 8000: returns split chunks, False, None
    - If length > 8000: returns initial preview chunk, True (is_file), BytesIO buffer for file upload
    """
    if len(text) <= SAFE_CHUNK_SIZE:
        return [text], False, None

    if len(text) > 8000:
        # Create file attachment
        file_buffer = io.BytesIO(text.encode("utf-8"))
        file_buffer.seek(0)
        # Create summary preview
        preview = text[:2000] + "\n\n...\n\n<i>[Full response exceeds Telegram limit and is attached above as a document]</i>"
        return [preview], True, file_buffer

    # Regular splitting for medium-large responses
    return split_message(text, SAFE_CHUNK_SIZE), False, None
