"""Shared Tavily helpers for search and URL extraction."""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TavilyResult:
    """A single search result from Tavily."""
    title: str
    url: str
    snippet: str


def tavily_available() -> bool:
    """Return True if the Tavily API key is configured."""
    from opencmo import llm
    return bool(llm.get_key("TAVILY_API_KEY"))


async def tavily_search(
    query: str,
    *,
    max_results: int = 5,
    search_depth: str = "basic",
    topic: str = "general",
) -> list[TavilyResult] | None:
    """Perform a Tavily search and return structured results.

    Returns None if TAVILY_API_KEY is not set or the search fails,
    allowing callers to fall back to their existing logic.
    """
    if not tavily_available():
        return None

    try:
        from tavily import AsyncTavilyClient

        client = AsyncTavilyClient()
        response = await client.search(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            topic=topic,
        )

        results = []
        for item in response.get("results", []):
            results.append(TavilyResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
            ))
        return results

    except Exception as exc:
        logger.warning("Tavily search failed for %r: %s", query, exc)
        return None


def _extract_result_content(result: dict) -> str:
    """Normalize Tavily extract payloads into plain string content."""
    content = result.get("raw_content") or result.get("content") or ""
    if not isinstance(content, str):
        content = str(content)
    return content.strip()


async def tavily_extract(
    url: str,
    *,
    extract_depth: str = "basic",
    format: str = "markdown",
) -> str | None:
    """Extract page content from a URL via Tavily.

    Returns None when Tavily is unavailable, extraction fails, or the response
    contains no usable content so callers can fall back to crawl-based fetching.
    """
    if not tavily_available():
        return None

    try:
        from tavily import AsyncTavilyClient

        from opencmo import llm
        client = AsyncTavilyClient(api_key=llm.get_key("TAVILY_API_KEY"))
        response = await client.extract(
            urls=[url],
            extract_depth=extract_depth,
            format=format,
        )
        results = response.get("results", []) if isinstance(response, dict) else []
        for item in results:
            if not isinstance(item, dict):
                continue
            content = _extract_result_content(item)
            if content:
                return content
        return None
    except Exception as exc:
        logger.warning("Tavily extract failed for %r: %s", url, exc)
        return None
