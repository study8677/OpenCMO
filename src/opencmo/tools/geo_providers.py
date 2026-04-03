"""GEO provider architecture for multi-platform AI visibility scanning."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass

from crawl4ai import AsyncWebCrawler

from opencmo.tools.crawl import _extract_markdown

# ---------------------------------------------------------------------------
# Conditional imports for API-based providers
# ---------------------------------------------------------------------------

try:
    import anthropic

    _HAS_ANTHROPIC = True
except ImportError:
    anthropic = None
    _HAS_ANTHROPIC = False

try:
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        import google.generativeai as genai

    _HAS_GENAI = True
except ImportError:
    genai = None
    _HAS_GENAI = False


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class GeoProviderResult:
    platform: str
    mentioned: bool
    mention_count: int
    position_pct: float | None  # first mention position %, None if not mentioned
    content_snippet: str  # <=snippet_chars
    error: str | None
    query: str = ""  # which query produced this result


@dataclass
class GeoAggregatedResult:
    """Aggregated result from multiple queries on one provider."""
    platform: str
    mentioned: bool             # True if mentioned in ANY query
    total_mention_count: int    # sum of all mentions across queries
    best_position_pct: float | None  # best (lowest) position %
    per_query_results: list[GeoProviderResult]
    error: str | None


# ---------------------------------------------------------------------------
# Query templates
# ---------------------------------------------------------------------------

_QUERY_TEMPLATES = [
    "best {category} tools",
    "best {category} tools 2026",
    "{brand_name} review",
    "{brand_name} vs alternatives",
    "{category} comparison",
]


def _get_query_templates(brand_name: str, category: str) -> list[str]:
    """Generate query list based on scrape depth."""
    from opencmo.scrape_config import get_scrape_profile
    profile = get_scrape_profile()
    n = min(profile.geo_query_templates, len(_QUERY_TEMPLATES))
    templates = _QUERY_TEMPLATES[:n]
    return [
        t.format(brand_name=brand_name, category=category)
        for t in templates
    ]


def _get_snippet_chars() -> int:
    from opencmo.scrape_config import get_scrape_profile
    return get_scrape_profile().geo_content_snippet_chars


def _get_request_delay() -> float:
    from opencmo.scrape_config import get_scrape_profile
    return get_scrape_profile().request_delay_seconds


# ---------------------------------------------------------------------------
# Shared text analysis helper
# ---------------------------------------------------------------------------


def _analyze_text(content: str, brand_name: str) -> tuple[bool, int, float | None]:
    """Analyze text for brand mentions.

    Returns:
        (mentioned, mention_count, position_pct) where position_pct is the
        percentage through the text where the first mention appears, or None.
    """
    content_lower = content.lower()
    brand_lower = brand_name.lower()

    mentioned = brand_lower in content_lower
    mention_count = content_lower.count(brand_lower)

    position_pct: float | None = None
    if mentioned and content_lower:
        first_idx = content_lower.index(brand_lower)
        position_pct = round(first_idx / len(content_lower) * 100, 1)

    return mentioned, mention_count, position_pct


# ---------------------------------------------------------------------------
# ABC
# ---------------------------------------------------------------------------


class GeoProvider(ABC):
    name: str
    status: str  # "enabled" | "disabled"
    requires_auth: bool
    auth_env_vars: list[str]

    @property
    def is_enabled(self) -> bool:
        if self.status == "disabled":
            return False
        if self.requires_auth:
            from opencmo import llm
            return all(llm.get_key(v) for v in self.auth_env_vars)
        return True

    @abstractmethod
    async def check_visibility(
        self, brand_name: str, category: str
    ) -> GeoProviderResult: ...

    async def check_visibility_multi(
        self, brand_name: str, category: str
    ) -> GeoAggregatedResult:
        """Run check_visibility across multiple query templates and aggregate."""
        queries = _get_query_templates(brand_name, category)
        results: list[GeoProviderResult] = []

        for i, query in enumerate(queries):
            try:
                result = await self._check_single_query(brand_name, query)
                results.append(result)
            except Exception as e:
                results.append(GeoProviderResult(
                    platform=self.name,
                    mentioned=False,
                    mention_count=0,
                    position_pct=None,
                    content_snippet="",
                    error=str(e),
                    query=query,
                ))

            if i < len(queries) - 1:
                delay = _get_request_delay()
                if delay > 0:
                    await asyncio.sleep(delay)

        # Aggregate
        any_mentioned = any(r.mentioned for r in results)
        total_mentions = sum(r.mention_count for r in results)
        positions = [r.position_pct for r in results if r.position_pct is not None]
        best_pos = min(positions) if positions else None
        errors = [r.error for r in results if r.error]

        return GeoAggregatedResult(
            platform=self.name,
            mentioned=any_mentioned,
            total_mention_count=total_mentions,
            best_position_pct=best_pos,
            per_query_results=results,
            error="; ".join(errors) if errors else None,
        )

    async def _check_single_query(
        self, brand_name: str, query: str
    ) -> GeoProviderResult:
        """Override in subclasses to check a single query."""
        # Default: call check_visibility (backward compat for API providers)
        return await self.check_visibility(brand_name, query)


# ---------------------------------------------------------------------------
# Crawl-based providers
# ---------------------------------------------------------------------------


class PerplexityProvider(GeoProvider):
    name = "Perplexity"
    status = "enabled"
    requires_auth = False
    auth_env_vars: list[str] = []

    async def check_visibility(
        self, brand_name: str, category: str
    ) -> GeoProviderResult:
        # For backward compat, use default query
        query = f"best {category} tools"
        return await self._check_single_query(brand_name, query)

    async def _check_single_query(
        self, brand_name: str, query: str
    ) -> GeoProviderResult:
        snippet_chars = _get_snippet_chars()
        url = f"https://www.perplexity.ai/search?q={query.replace(' ', '+')}"
        try:
            async with AsyncWebCrawler() as crawler:
                crawl_result = await crawler.arun(url=url)
                content = _extract_markdown(crawl_result)
                mentioned, mention_count, position_pct = _analyze_text(
                    content, brand_name
                )
                return GeoProviderResult(
                    platform=self.name,
                    mentioned=mentioned,
                    mention_count=mention_count,
                    position_pct=position_pct,
                    content_snippet=content[:snippet_chars],
                    error=None,
                    query=query,
                )
        except Exception as e:
            return GeoProviderResult(
                platform=self.name,
                mentioned=False,
                mention_count=0,
                position_pct=None,
                content_snippet="",
                error=str(e),
                query=query,
            )


class YouDotComProvider(GeoProvider):
    name = "You.com"
    status = "enabled"
    requires_auth = False
    auth_env_vars: list[str] = []

    async def check_visibility(
        self, brand_name: str, category: str
    ) -> GeoProviderResult:
        query = f"best {category} tools"
        return await self._check_single_query(brand_name, query)

    async def _check_single_query(
        self, brand_name: str, query: str
    ) -> GeoProviderResult:
        snippet_chars = _get_snippet_chars()
        url = f"https://you.com/search?q={query.replace(' ', '+')}"
        try:
            async with AsyncWebCrawler() as crawler:
                crawl_result = await crawler.arun(url=url)
                content = _extract_markdown(crawl_result)
                mentioned, mention_count, position_pct = _analyze_text(
                    content, brand_name
                )
                return GeoProviderResult(
                    platform=self.name,
                    mentioned=mentioned,
                    mention_count=mention_count,
                    position_pct=position_pct,
                    content_snippet=content[:snippet_chars],
                    error=None,
                    query=query,
                )
        except Exception as e:
            return GeoProviderResult(
                platform=self.name,
                mentioned=False,
                mention_count=0,
                position_pct=None,
                content_snippet="",
                error=str(e),
                query=query,
            )


# ---------------------------------------------------------------------------
# API-based providers
# ---------------------------------------------------------------------------

_API_QUERY_TEMPLATE = (
    "What are the best {category} tools? List the top options with brief descriptions."
)


class ChatGPTProvider(GeoProvider):
    name = "ChatGPT"
    status = "disabled"
    requires_auth = True
    auth_env_vars = ["OPENAI_API_KEY"]

    @property
    def is_enabled(self) -> bool:
        from opencmo import llm
        return (
            llm.get_key("OPENCMO_GEO_CHATGPT") == "1"
            and bool(llm.get_key("OPENAI_API_KEY"))
        )

    async def check_visibility(
        self, brand_name: str, category: str
    ) -> GeoProviderResult:
        query = _API_QUERY_TEMPLATE.format(category=category)
        return await self._check_single_query(brand_name, query)

    async def _check_single_query(
        self, brand_name: str, query: str
    ) -> GeoProviderResult:
        snippet_chars = _get_snippet_chars()
        try:
            from openai import AsyncOpenAI

            from opencmo import llm

            client = AsyncOpenAI(
                api_key=llm.get_key("OPENAI_API_KEY"),
                base_url=llm.get_key("OPENAI_BASE_URL") or None,
            )
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": query,
                    }
                ],
                max_tokens=1024,
            )
            content = response.choices[0].message.content or ""
            mentioned, mention_count, position_pct = _analyze_text(
                content, brand_name
            )
            return GeoProviderResult(
                platform=self.name,
                mentioned=mentioned,
                mention_count=mention_count,
                position_pct=position_pct,
                content_snippet=content[:snippet_chars],
                error=None,
                query=query,
            )
        except Exception as e:
            return GeoProviderResult(
                platform=self.name,
                mentioned=False,
                mention_count=0,
                position_pct=None,
                content_snippet="",
                error=str(e),
                query=query,
            )


class ClaudeProvider(GeoProvider):
    name = "Claude"
    status = "disabled"
    requires_auth = True
    auth_env_vars = ["ANTHROPIC_API_KEY"]

    @property
    def is_enabled(self) -> bool:
        if not _HAS_ANTHROPIC:
            return False
        from opencmo import llm
        return bool(llm.get_key("ANTHROPIC_API_KEY"))

    async def check_visibility(
        self, brand_name: str, category: str
    ) -> GeoProviderResult:
        query = _API_QUERY_TEMPLATE.format(category=category)
        return await self._check_single_query(brand_name, query)

    async def _check_single_query(
        self, brand_name: str, query: str
    ) -> GeoProviderResult:
        snippet_chars = _get_snippet_chars()
        try:
            from opencmo import llm
            client = anthropic.AsyncAnthropic(
                api_key=llm.get_key("ANTHROPIC_API_KEY"),
            )
            response = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": query,
                    }
                ],
            )
            content = response.content[0].text if response.content else ""
            mentioned, mention_count, position_pct = _analyze_text(
                content, brand_name
            )
            return GeoProviderResult(
                platform=self.name,
                mentioned=mentioned,
                mention_count=mention_count,
                position_pct=position_pct,
                content_snippet=content[:snippet_chars],
                error=None,
                query=query,
            )
        except Exception as e:
            return GeoProviderResult(
                platform=self.name,
                mentioned=False,
                mention_count=0,
                position_pct=None,
                content_snippet="",
                error=str(e),
                query=query,
            )


class GeminiProvider(GeoProvider):
    name = "Gemini"
    status = "disabled"
    requires_auth = True
    auth_env_vars = ["GOOGLE_AI_API_KEY"]

    @property
    def is_enabled(self) -> bool:
        if not _HAS_GENAI:
            return False
        from opencmo import llm
        return bool(llm.get_key("GOOGLE_AI_API_KEY"))

    async def check_visibility(
        self, brand_name: str, category: str
    ) -> GeoProviderResult:
        query = _API_QUERY_TEMPLATE.format(category=category)
        return await self._check_single_query(brand_name, query)

    async def _check_single_query(
        self, brand_name: str, query: str
    ) -> GeoProviderResult:
        snippet_chars = _get_snippet_chars()
        try:
            from opencmo import llm
            genai.configure(api_key=llm.get_key("GOOGLE_AI_API_KEY"))
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = await model.generate_content_async(query)
            content = response.text or ""
            mentioned, mention_count, position_pct = _analyze_text(
                content, brand_name
            )
            return GeoProviderResult(
                platform=self.name,
                mentioned=mentioned,
                mention_count=mention_count,
                position_pct=position_pct,
                content_snippet=content[:snippet_chars],
                error=None,
                query=query,
            )
        except Exception as e:
            return GeoProviderResult(
                platform=self.name,
                mentioned=False,
                mention_count=0,
                position_pct=None,
                content_snippet="",
                error=str(e),
                query=query,
            )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

GEO_PROVIDER_REGISTRY: list[GeoProvider] = [
    PerplexityProvider(),
    YouDotComProvider(),
    ChatGPTProvider(),
    ClaudeProvider(),
    GeminiProvider(),
]
