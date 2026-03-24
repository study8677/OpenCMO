"""Shared Tavily search helper — used by blog_writer and graph_expansion.

Returns structured results when TAVILY_API_KEY is set, otherwise returns None
so callers can fall back to their existing scraping logic.
"""

from __future__ import annotations

import logging
import os
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
    return bool(os.environ.get("TAVILY_API_KEY"))


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
