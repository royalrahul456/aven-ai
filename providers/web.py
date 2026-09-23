"""Web-enabled search and AI synthesis provider."""
from __future__ import annotations

import asyncio
from typing import List, Optional, Tuple
import aiohttp
from config import settings
from providers.base import (
    AIProvider,
    ProviderMessage,
    ProviderResponse,
    SourceCitation,
    ProviderUnavailableError,
    AIProviderError
)
from utils.logger import logger


class WebProvider(AIProvider):
    def __init__(self, fallback_llm_provider: Optional[AIProvider] = None):
        super().__init__(name="Web Search AI")
        self.fallback_llm_provider = fallback_llm_provider

    def is_available(self) -> bool:
        # Needs at least one underlying LLM provider to synthesize results
        return True

    async def search_multi_engine(self, query: str, max_results: int = 6) -> List[SourceCitation]:
        """Performs async multi-engine search (DDGS + Google News RSS) to retrieve live web facts."""
        results: List[SourceCitation] = []

        # Engine 1: DuckDuckGo Search
        try:
            from duckduckgo_search import DDGS
            def _ddg_sync():
                with DDGS() as ddgs:
                    # Search text
                    r_list = list(ddgs.text(query, max_results=max_results))
                    if not r_list:
                        r_list = list(ddgs.news(query, max_results=max_results))
                    return r_list

            raw_results = await asyncio.to_thread(_ddg_sync)
            for r in raw_results:
                title = r.get("title", "Web Source")
                url = r.get("href") or r.get("link") or r.get("url", "")
                snippet = r.get("body") or r.get("snippet") or r.get("excerpt", "")
                if url and title:
                    results.append(SourceCitation(title=title, url=url, snippet=snippet))
            if results:
                return results[:max_results]
        except Exception as e:
            logger.warning(f"DDGS search warning: {e}, falling back to News RSS...")

        # Engine 2: Google News RSS for real-time / current topics
        try:
            import urllib.parse
            import xml.etree.ElementTree as ET
            encoded_q = urllib.parse.quote(query)
            rss_url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en-US&gl=US&ceid=US:en"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(rss_url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        root = ET.fromstring(text)
                        for item in root.findall(".//item")[:max_results]:
                            title = item.findtext("title") or "News Article"
                            link = item.findtext("link") or ""
                            pub_date = item.findtext("pubDate") or ""
                            description = item.findtext("description") or ""
                            # Strip HTML from description
                            import re
                            clean_desc = re.sub(r"<[^>]+>", "", description).strip()
                            snippet = f"{pub_date} - {clean_desc}" if pub_date else clean_desc
                            if link and title:
                                results.append(SourceCitation(title=title, url=link, snippet=snippet))
            if results:
                return results[:max_results]
        except Exception as e:
            logger.warning(f"Google News RSS search failed: {e}")

        return results

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[ProviderMessage]] = None,
        temperature: float = 0.5,
        max_tokens: int = 4096,
    ) -> ProviderResponse:
        logger.info(f"Executing web search for query: {prompt[:80]}...")
        sources = await self.search_multi_engine(prompt, max_results=5)

        # Build context from sources
        if sources:
            search_context_lines = []
            for idx, src in enumerate(sources, 1):
                search_context_lines.append(f"[{idx}] Source: {src.title}\nURL: {src.url}\nExcerpt/Summary: {src.snippet}")
            search_context = "\n\n".join(search_context_lines)
        else:
            search_context = "No direct real-time web results found. Please answer accurately with your latest knowledge."

        augmented_system_prompt = (
            "You are AVEN AI operating in Web-enabled search mode.\n"
            "Analyze the provided live web search results below and write a detailed, up-to-date, comprehensive answer to the user's question.\n"
            "Rules:\n"
            "- Ground your answer directly in the real-time facts and headlines provided in the search results.\n"
            "- Cite sources using numbered references like [1], [2].\n"
            "- Do not claim you lack real-time access; use the provided search findings to give an insightful summary."
        )

        if system_prompt:
            augmented_system_prompt = f"{system_prompt}\n\n{augmented_system_prompt}"

        grounded_prompt = (
            f"=== LIVE WEB SEARCH RESULTS ===\n"
            f"{search_context}\n"
            f"===============================\n\n"
            f"User Question: {prompt}\n\n"
            f"Please synthesize the live search findings above into a comprehensive, structured response with citations."
        )

        if not self.fallback_llm_provider:
            raise AIProviderError("No active LLM provider available to synthesize web search results.")

        response = await self.fallback_llm_provider.generate(
            prompt=grounded_prompt,
            system_prompt=augmented_system_prompt,
            history=history,
            temperature=temperature,
            max_tokens=max_tokens
        )

        # Format clean sources footer if sources exist
        if sources:
            sources_footer = "\n\n<b>🌐 Sources & Citations:</b>\n" + "\n".join(
                [f"• <a href=\"{s.url}\">{s.title}</a>" for s in sources if s.url]
            )
            response.text = response.text.strip() + sources_footer
            response.sources = sources

        response.model_name = "Aven Web"
        response.provider = "Web Engine"
        return response
