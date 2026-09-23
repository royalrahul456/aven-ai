"""FLUX.1 AI Image Generation Provider with Smart AI Prompt Enrichment."""
from __future__ import annotations

import re
import random
import urllib.parse
import aiohttp
from utils.logger import logger
from providers.registry import registry

ASPECT_RATIOS = {
    "1:1": (1024, 1024),
    "16:9": (1280, 720),
    "9:16": (720, 1280),
    "4:3": (1024, 768),
    "3:4": (768, 1024),
}


def sanitize_raw_prompt(prompt: str) -> str:
    """Removes conversational fluff like 'generate an image of', 'draw me', etc."""
    cleaned = prompt.strip()
    patterns = [
        r"^(?:please\s+)?(?:generate|create|make|draw|paint|render|show)\s+(?:an?\s+)?(?:image|picture|photo|artwork|wallpaper|portrait)\s+(?:of\s+)?",
        r"^(?:can\s+you\s+)?(?:generate|create|make|draw|paint)\s+(?:an?\s+)?(?:image|picture|photo)\s+(?:of\s+)?",
        r"^(?:image|photo|picture)\s+(?:of\s+)?",
    ]
    for p in patterns:
        cleaned = re.sub(p, "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned if cleaned else prompt.strip()


async def enrich_image_prompt(raw_prompt: str, style_hint: str | None = None) -> str:
    """Uses LLM to transform short/vague user prompts into professional photography/art prompts."""
    sanitized = sanitize_raw_prompt(raw_prompt)
    
    # If user already wrote a super detailed prompt (> 120 chars), just clean it
    if len(sanitized) > 120:
        return sanitized[:200]

    sys_prompt = (
        "You are an expert visual prompt engineer for FLUX.1. "
        "Convert the user's short prompt into a concise (under 25 words), visually stunning image prompt. "
        "Add cinematic lighting, camera perspective, rich textures, and artistic quality (e.g. 8k, photorealistic, dramatic lighting, Octane render). "
        "Output ONLY the prompt text. No quotes, no preamble, no explanations."
    )

    try:
        res = await registry.execute_query(
            model_id="aven_pro",
            prompt=f"Subject: {sanitized}" + (f" (Style: {style_hint})" if style_hint else ""),
            system_prompt=sys_prompt,
            temperature=0.6
        )
        expanded = res.text.strip().strip('"').strip("'").replace("\n", " ")
        if len(expanded) > 200:
            expanded = expanded[:200]
        logger.info(f"Enriched prompt: '{sanitized}' -> '{expanded}'")
        return expanded
    except Exception as e:
        logger.warning(f"Could not enrich prompt via LLM: {e}. Using sanitized prompt.")
        # Fallback enhancement
        return f"{sanitized}, masterpiece, highly detailed, photorealistic 8k, cinematic lighting"


class FluxImageProvider:
    """Free, high-speed FLUX.1 image generation provider with multi-model fallback."""

    def __init__(self):
        self.base_url = "https://image.pollinations.ai/prompt"

    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        seed: int | None = None,
        style: str = "flux-realism"
    ) -> tuple[bytes, int, str]:
        """
        Generates an image using FLUX.1.
        Returns: (image_bytes, seed_used, final_prompt_used)
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        # 1. Enrich prompt with AI
        final_prompt = await enrich_image_prompt(prompt, style_hint=style)
        encoded_prompt = urllib.parse.quote(final_prompt)
        
        width, height = ASPECT_RATIOS.get(aspect_ratio, (1024, 1024))
        actual_seed = seed if seed is not None else random.randint(1, 99999999)

        models_to_try = [style, "flux-realism", "flux", "turbo"]
        models_to_try = list(dict.fromkeys(models_to_try))

        timeout = aiohttp.ClientTimeout(total=45)

        for model_candidate in models_to_try:
            url = (
                f"{self.base_url}/{encoded_prompt}"
                f"?width={width}&height={height}&seed={actual_seed}"
                f"&model={model_candidate}&nologo=true"
            )

            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            image_bytes = await response.read()
                            if len(image_bytes) > 2000:
                                return image_bytes, actual_seed, final_prompt
                            logger.warning(f"Model '{model_candidate}' returned image too small ({len(image_bytes)}b). Trying next...")
                        else:
                            logger.warning(f"Model '{model_candidate}' returned HTTP {response.status}. Trying fallback...")
            except Exception as err:
                logger.warning(f"Error fetching from '{model_candidate}': {err}. Trying next...")

        raise RuntimeError("All image generation engines are currently busy. Please try again in a few seconds.")


flux_provider = FluxImageProvider()
