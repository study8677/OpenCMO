"""Community provider architecture for multi-platform discussion monitoring."""

from __future__ import annotations

import asyncio
import math
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import quote_plus

import httpx


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class HttpResult:
    data: dict | list | None
    error: str | None
    status_code: int | None


@dataclass
class SuggestedQuery:
    platform: str
    provider: str
    query: str
    reason: str


@dataclass
class DisabledProvider:
    name: str
    reason: str


@dataclass
class ProviderError:
    provider: str
    errors: list[str]


@dataclass
class DiscussionHit:
    platform: str
    title: str
    url: str
    engagement_score: int
    raw_score: int
    comments_count: int
    age_days: int
    author: str
    detail_id: str
    extra_param_1: str
    extra_param_2: str
    preview: str
    source: str


@dataclass
class DiscussionDetail:
    platform: str
    detail_id: str
    title: str
    full_content: str
    url: str
    comments: list[dict]


@dataclass
class ProviderSearchResult:
    hits: list[DiscussionHit] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    suggested_queries: list[SuggestedQuery] = field(default_factory=list)


@dataclass
class ScanResult:
    hits: list[DiscussionHit] = field(default_factory=list)
    disabled_providers: list[DisabledProvider] = field(default_factory=list)
    provider_errors: list[ProviderError] = field(default_factory=list)
    suggested_queries: list[SuggestedQuery] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Unified HTTP helper with retry
# ---------------------------------------------------------------------------

_USER_AGENT = "OpenCMO/0.1 (community-monitor)"


def _get_profile():
    """Lazy import to avoid circular deps."""
    from opencmo.scrape_config import get_scrape_profile
    return get_scrape_profile()


async def _http_get_json(
    url: str,
    params: dict | None = None,
    headers: dict | None = None,
) -> HttpResult:
    """Unified HTTP GET -> JSON with configurable timeout and retry on 429."""
    profile = _get_profile()
    merged_headers = {"User-Agent": _USER_AGENT}
    if headers:
        merged_headers.update(headers)

    last_result = HttpResult(data=None, error="timeout", status_code=None)
    for attempt in range(1, profile.max_retries_on_429 + 1):
        try:
            async with httpx.AsyncClient(timeout=profile.http_timeout_seconds) as client:
                resp = await client.get(url, params=params, headers=merged_headers)
            if resp.status_code == 429:
                last_result = HttpResult(data=None, error="rate_limited", status_code=429)
                if attempt < profile.max_retries_on_429:
                    await asyncio.sleep(2.0 * attempt)  # exponential backoff
                    continue
                return last_result
            if resp.status_code >= 400:
                return HttpResult(data=None, error=f"http_{resp.status_code}", status_code=resp.status_code)
            try:
                data = resp.json()
            except Exception:
                return HttpResult(data=None, error="parse_error", status_code=resp.status_code)
            return HttpResult(data=data, error=None, status_code=resp.status_code)
        except httpx.TimeoutException:
            last_result = HttpResult(data=None, error="timeout", status_code=None)
            if attempt < profile.max_retries_on_429:
                await asyncio.sleep(1.0)
                continue
        except Exception:
            last_result = HttpResult(data=None, error="timeout", status_code=None)
            break
    return last_result


async def _delay():
    """Insert configurable delay between requests."""
    profile = _get_profile()
    if profile.request_delay_seconds > 0:
        await asyncio.sleep(profile.request_delay_seconds)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _age_days(iso_str: str) -> int:
    """Return age in days from an ISO-8601-ish timestamp string."""
    if not iso_str:
        return 0
    try:
        # strip trailing 'Z' and parse
        cleaned = iso_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        return max(0, delta.days)
    except Exception:
        return 0


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit]


# ---------------------------------------------------------------------------
# Category -> subreddit mapping for targeted search
# ---------------------------------------------------------------------------

_CATEGORY_SUBREDDITS: dict[str, list[str]] = {
    "devtools": ["programming", "webdev", "devops", "coding", "learnprogramming", "softwareengineering"],
    "ai": ["MachineLearning", "artificial", "ChatGPT", "LocalLLaMA", "OpenAI", "deeplearning"],
    "saas": ["SaaS", "startups", "Entrepreneur", "smallbusiness", "indiehackers"],
    "marketing": ["marketing", "digital_marketing", "SEO", "socialmedia", "content_marketing", "PPC"],
    "analytics": ["analytics", "datascience", "BusinessIntelligence", "bigdata"],
    "ecommerce": ["ecommerce", "shopify", "dropship", "FulfillmentByAmazon"],
    "web scraping": ["webscraping", "DataHoarder", "datasets"],
    "security": ["netsec", "cybersecurity", "hacking", "AskNetsec"],
    "design": ["web_design", "UI_Design", "userexperience", "graphic_design"],
    "database": ["Database", "PostgreSQL", "mongodb", "redis"],
    "cloud": ["aws", "googlecloud", "azure", "selfhosted", "homelab"],
    "mobile": ["androiddev", "iOSProgramming", "reactnative", "FlutterDev"],
    "gaming": ["gamedev", "IndieGaming", "unity3d", "godot"],
    "fintech": ["fintech", "CryptoCurrency", "algotrading", "personalfinance"],
    "education": ["edtech", "learnprogramming", "OnlineEducation"],
    "healthcare": ["healthIT", "digitalhealth", "medical"],
    "productivity": ["productivity", "selfhosted", "Notion", "ObsidianMD"],
}


def _get_subreddits_for_category(category: str) -> list[str]:
    """Return relevant subreddits for a category."""
    cat_lower = category.lower()
    for key, subs in _CATEGORY_SUBREDDITS.items():
        if key in cat_lower or cat_lower in key:
            return subs
    # Fallback: try each word
    for word in cat_lower.split():
        for key, subs in _CATEGORY_SUBREDDITS.items():
            if word in key or key in word:
                return subs
    return []


# ---------------------------------------------------------------------------
# ABC
# ---------------------------------------------------------------------------


class CommunityProvider(ABC):
    name: str
    status: str  # "enabled" | "disabled" | "stub"
    requires_auth: bool
    auth_env_vars: list[str]
    capabilities: set[str]
    max_search_calls: int
    recommended_max_details: int

    @property
    def is_enabled(self) -> bool:
        if self.status in ("stub", "disabled"):
            return False
        if self.requires_auth:
            return all(os.environ.get(v) for v in self.auth_env_vars)
        return True

    @abstractmethod
    async def search(self, brand_name: str, category: str) -> ProviderSearchResult: ...

    async def fetch_detail(self, hit: DiscussionHit) -> DiscussionDetail | None:
        return None


# ---------------------------------------------------------------------------
# Reddit — deep scraping with pagination + multi-query
# ---------------------------------------------------------------------------


class RedditProvider(CommunityProvider):
    name = "reddit"
    status = "enabled"
    requires_auth = False
    auth_env_vars: list[str] = []
    capabilities = {"search", "detail"}
    max_search_calls = 8
    recommended_max_details = 5

    # ---- internal parsers (tested separately) ----

    @staticmethod
    def parse_search_response(data: dict, source: str) -> list[DiscussionHit]:
        hits: list[DiscussionHit] = []
        children = []
        if isinstance(data, dict):
            children = data.get("data", {}).get("children", [])
        for child in children:
            d = child.get("data", {})
            if not d.get("title"):
                continue
            raw_score = int(d.get("score", 0))
            hits.append(DiscussionHit(
                platform="reddit",
                title=d.get("title", ""),
                url=f"https://www.reddit.com{d.get('permalink', '')}",
                engagement_score=min(100, raw_score * 2),
                raw_score=raw_score,
                comments_count=int(d.get("num_comments", 0)),
                age_days=_age_days(
                    datetime.fromtimestamp(d.get("created_utc", 0), tz=timezone.utc).isoformat()
                    if d.get("created_utc") else ""
                ),
                author=d.get("author", ""),
                detail_id=d.get("id", ""),
                extra_param_1=d.get("subreddit", ""),
                extra_param_2="",
                preview=_truncate(d.get("selftext", ""), 300),
                source=source,
            ))
        return hits

    @staticmethod
    def _get_after_token(data: dict) -> str | None:
        """Extract the 'after' pagination token from Reddit response."""
        if isinstance(data, dict):
            return data.get("data", {}).get("after")
        return None

    @staticmethod
    def parse_detail_response(data: list, hit: DiscussionHit) -> DiscussionDetail | None:
        if not data or not isinstance(data, list) or len(data) < 2:
            return None
        # First element: post listing
        post_children = data[0].get("data", {}).get("children", [])
        title = ""
        full_content = ""
        url = hit.url
        if post_children:
            pd = post_children[0].get("data", {})
            title = pd.get("title", hit.title)
            full_content = _truncate(pd.get("selftext", ""), 2000)
            url = f"https://www.reddit.com{pd.get('permalink', '')}" if pd.get("permalink") else hit.url
        # Second element: comment listing
        comment_children = data[1].get("data", {}).get("children", [])
        profile = _get_profile()
        comments = []
        for c in comment_children:
            if c.get("kind") != "t1":
                continue
            cd = c.get("data", {})
            comments.append({
                "author": cd.get("author", ""),
                "text": _truncate(cd.get("body", ""), 500),
                "score": int(cd.get("score", 0)),
            })
            if len(comments) >= profile.reddit_comments_per_post:
                break
        return DiscussionDetail(
            platform="reddit",
            detail_id=hit.detail_id,
            title=title,
            full_content=full_content,
            url=url,
            comments=comments,
        )

    # ---- paginated search helper ----

    async def _paginated_search(
        self, query: str, source: str, pages: int, per_page: int, time_filter: str,
    ) -> tuple[list[DiscussionHit], list[str]]:
        """Fetch multiple pages of Reddit search results."""
        all_hits: list[DiscussionHit] = []
        errors: list[str] = []
        after: str | None = None

        for page in range(pages):
            params: dict[str, str] = {
                "q": query, "sort": "relevance", "t": time_filter,
                "limit": str(min(per_page, 100)),  # Reddit max is 100
            }
            if after:
                params["after"] = after

            r = await _http_get_json(
                "https://www.reddit.com/search.json",
                params=params,
            )
            if r.error:
                errors.append(f"{source} page {page}: {r.error}")
                break
            if r.data:
                page_hits = self.parse_search_response(r.data, source)
                all_hits.extend(page_hits)
                after = self._get_after_token(r.data)
                if not after or not page_hits:
                    break  # no more pages
            else:
                break

            if page < pages - 1:
                await _delay()

        return all_hits, errors

    async def _subreddit_search(
        self, subreddit: str, query: str, source: str, per_page: int, time_filter: str,
    ) -> tuple[list[DiscussionHit], list[str]]:
        """Search within a specific subreddit."""
        errors: list[str] = []
        r = await _http_get_json(
            f"https://www.reddit.com/r/{subreddit}/search.json",
            params={
                "q": query, "sort": "relevance", "t": time_filter,
                "restrict_sr": "1", "limit": str(min(per_page, 100)),
            },
        )
        if r.error:
            return [], [f"r/{subreddit} {source}: {r.error}"]
        if r.data:
            return self.parse_search_response(r.data, source), errors
        return [], errors

    # ---- public API ----

    async def search(self, brand_name: str, category: str) -> ProviderSearchResult:
        profile = _get_profile()
        errors: list[str] = []
        all_hits: list[DiscussionHit] = []

        # 1. Brand search (paginated)
        hits, errs = await self._paginated_search(
            brand_name, "brand_search",
            pages=profile.reddit_brand_pages,
            per_page=profile.reddit_brand_per_page,
            time_filter=profile.reddit_time_filter,
        )
        all_hits.extend(hits)
        errors.extend(errs)
        await _delay()

        # 2. Category search (paginated)
        hits, errs = await self._paginated_search(
            category, "category_search",
            pages=profile.reddit_category_pages,
            per_page=profile.reddit_category_per_page,
            time_filter=profile.reddit_time_filter,
        )
        all_hits.extend(hits)
        errors.extend(errs)
        await _delay()

        # 3. Extra combo queries
        extra_queries = []
        if profile.reddit_extra_queries >= 1:
            extra_queries.append(f"{brand_name} {category}")
        if profile.reddit_extra_queries >= 2:
            extra_queries.append(f"{brand_name} review")
        if profile.reddit_extra_queries >= 3:
            extra_queries.append(f"{brand_name} alternative")
        if profile.reddit_extra_queries >= 4:
            extra_queries.append(f"best {category} tools")

        for eq in extra_queries:
            hits, errs = await self._paginated_search(
                eq, f"extra_search:{eq}",
                pages=1,
                per_page=profile.reddit_extra_per_page,
                time_filter=profile.reddit_time_filter,
            )
            all_hits.extend(hits)
            errors.extend(errs)
            await _delay()

        # 4. Subreddit-targeted search
        if profile.reddit_subreddit_search:
            subreddits = _get_subreddits_for_category(category)
            for sub in subreddits[:4]:  # limit to 4 subreddits
                hits, errs = await self._subreddit_search(
                    sub, brand_name, f"subreddit:{sub}",
                    per_page=min(profile.reddit_brand_per_page, 50),
                    time_filter=profile.reddit_time_filter,
                )
                all_hits.extend(hits)
                errors.extend(errs)
                await _delay()

        # Deduplicate by detail_id, keep higher raw_score
        seen: dict[str, DiscussionHit] = {}
        for h in all_hits:
            key = (h.platform, h.detail_id)
            existing = seen.get(key)
            if existing is None or h.raw_score > existing.raw_score:
                seen[key] = h
        return ProviderSearchResult(hits=list(seen.values()), errors=errors)

    async def fetch_detail(self, hit: DiscussionHit) -> DiscussionDetail | None:
        profile = _get_profile()
        subreddit = hit.extra_param_1 or "all"
        r = await _http_get_json(
            f"https://www.reddit.com/r/{subreddit}/comments/{hit.detail_id}.json",
            params={"limit": str(profile.reddit_comments_per_post), "depth": "1", "sort": "best"},
        )
        if r.error or not r.data:
            return None
        return self.parse_detail_response(r.data, hit)


# ---------------------------------------------------------------------------
# Hacker News — deep scraping with pagination + date sort
# ---------------------------------------------------------------------------


class HackerNewsProvider(CommunityProvider):
    name = "hackernews"
    status = "enabled"
    requires_auth = False
    auth_env_vars: list[str] = []
    capabilities = {"search", "detail"}
    max_search_calls = 6
    recommended_max_details = 5

    @staticmethod
    def parse_search_response(data: dict, source: str) -> list[DiscussionHit]:
        hits: list[DiscussionHit] = []
        for item in (data.get("hits") or []):
            title = item.get("title", "")
            if not title:
                continue
            oid = str(item.get("objectID", ""))
            points = int(item.get("points") or 0)
            hits.append(DiscussionHit(
                platform="hackernews",
                title=title,
                url=f"https://news.ycombinator.com/item?id={oid}",
                engagement_score=min(100, math.floor(points * 1.5)),
                raw_score=points,
                comments_count=int(item.get("num_comments") or 0),
                age_days=_age_days(item.get("created_at", "")),
                author=item.get("author", ""),
                detail_id=oid,
                extra_param_1="",
                extra_param_2="",
                preview=_truncate(item.get("story_text") or title, 300),
                source=source,
            ))
        return hits

    @staticmethod
    def parse_comments_response(data: dict) -> list[dict]:
        profile = _get_profile()
        comments: list[dict] = []
        for item in (data.get("hits") or []):
            text = item.get("comment_text", "")
            if not text:
                continue
            comments.append({
                "author": item.get("author", ""),
                "text": _truncate(text, 500),
                "score": int(item.get("points") or 0),
            })
            if len(comments) >= profile.hn_comments_per_post:
                break
        return comments

    async def _paginated_search(
        self, query: str, source: str, pages: int, per_page: int,
        endpoint: str = "search",
    ) -> tuple[list[DiscussionHit], list[str]]:
        """Fetch multiple pages of HN search results."""
        all_hits: list[DiscussionHit] = []
        errors: list[str] = []

        for page in range(pages):
            r = await _http_get_json(
                f"https://hn.algolia.com/api/v1/{endpoint}",
                params={
                    "query": query, "tags": "story",
                    "hitsPerPage": str(per_page), "page": str(page),
                },
            )
            if r.error:
                errors.append(f"{source} page {page}: {r.error}")
                break
            if r.data:
                page_hits = self.parse_search_response(r.data, source)
                all_hits.extend(page_hits)
                if not page_hits:
                    break
            else:
                break

            if page < pages - 1:
                await _delay()

        return all_hits, errors

    async def search(self, brand_name: str, category: str) -> ProviderSearchResult:
        profile = _get_profile()
        errors: list[str] = []
        all_hits: list[DiscussionHit] = []

        # 1. Brand search by relevance (paginated)
        hits, errs = await self._paginated_search(
            brand_name, "brand_search",
            pages=profile.hn_brand_pages,
            per_page=profile.hn_brand_per_page,
        )
        all_hits.extend(hits)
        errors.extend(errs)
        await _delay()

        # 2. Category search by relevance (paginated)
        hits, errs = await self._paginated_search(
            category, "category_search",
            pages=profile.hn_category_pages,
            per_page=profile.hn_category_per_page,
        )
        all_hits.extend(hits)
        errors.extend(errs)
        await _delay()

        # 3. Brand search by date (newest first) — extra signal
        if profile.hn_include_date_sort:
            hits, errs = await self._paginated_search(
                brand_name, "brand_date_search",
                pages=1,
                per_page=profile.hn_brand_per_page,
                endpoint="search_by_date",
            )
            all_hits.extend(hits)
            errors.extend(errs)
            await _delay()

            # Category by date too
            hits, errs = await self._paginated_search(
                category, "category_date_search",
                pages=1,
                per_page=profile.hn_category_per_page,
                endpoint="search_by_date",
            )
            all_hits.extend(hits)
            errors.extend(errs)

        # Deduplicate
        seen: dict[str, DiscussionHit] = {}
        for h in all_hits:
            key = (h.platform, h.detail_id)
            existing = seen.get(key)
            if existing is None or h.raw_score > existing.raw_score:
                seen[key] = h
        return ProviderSearchResult(hits=list(seen.values()), errors=errors)

    async def fetch_detail(self, hit: DiscussionHit) -> DiscussionDetail | None:
        profile = _get_profile()
        # Fetch story
        r1 = await _http_get_json(
            f"https://hn.algolia.com/api/v1/items/{hit.detail_id}",
        )
        title = hit.title
        full_content = ""
        if r1.error or not r1.data:
            pass
        else:
            title = r1.data.get("title", hit.title)
            full_content = _truncate(r1.data.get("text") or "", 2000)

        # Fetch comments
        r2 = await _http_get_json(
            "https://hn.algolia.com/api/v1/search",
            params={
                "tags": f"comment,story_{hit.detail_id}",
                "hitsPerPage": str(profile.hn_comments_per_post),
            },
        )
        comments: list[dict] = []
        if not r2.error and r2.data:
            comments = self.parse_comments_response(r2.data)

        if not full_content and not comments:
            return None

        return DiscussionDetail(
            platform="hackernews",
            detail_id=hit.detail_id,
            title=title,
            full_content=full_content,
            url=hit.url,
            comments=comments,
        )


# ---------------------------------------------------------------------------
# Dev.to — deep scraping with pagination + multi-tag
# ---------------------------------------------------------------------------


class DevtoProvider(CommunityProvider):
    name = "devto"
    status = "enabled"
    requires_auth = False
    auth_env_vars: list[str] = []
    capabilities = {"search", "detail"}
    max_search_calls = 6
    recommended_max_details = 5

    @staticmethod
    def parse_search_response(data: list, source: str) -> list[DiscussionHit]:
        hits: list[DiscussionHit] = []
        if not isinstance(data, list):
            return hits
        for item in data:
            title = item.get("title", "")
            if not title:
                continue
            reactions = int(item.get("positive_reactions_count") or item.get("public_reactions_count") or 0)
            hits.append(DiscussionHit(
                platform="devto",
                title=title,
                url=item.get("url", ""),
                engagement_score=min(100, reactions * 3),
                raw_score=reactions,
                comments_count=int(item.get("comments_count") or 0),
                age_days=_age_days(item.get("published_at", "")),
                author=item.get("user", {}).get("username", ""),
                detail_id=str(item.get("id", "")),
                extra_param_1="",
                extra_param_2="",
                preview=_truncate(item.get("description", ""), 300),
                source=source,
            ))
        return hits

    async def _paginated_tag_search(
        self, tag: str, source: str, pages: int, per_page: int,
    ) -> tuple[list[DiscussionHit], list[str]]:
        """Fetch multiple pages of Dev.to tag search results."""
        all_hits: list[DiscussionHit] = []
        errors: list[str] = []

        for page in range(1, pages + 1):
            r = await _http_get_json(
                "https://dev.to/api/articles",
                params={"tag": tag, "per_page": str(per_page), "page": str(page)},
            )
            if r.error:
                errors.append(f"{source} page {page}: {r.error}")
                break
            if r.data and isinstance(r.data, list) and len(r.data) > 0:
                page_hits = self.parse_search_response(r.data, source)
                all_hits.extend(page_hits)
                if len(r.data) < per_page:
                    break  # last page
            else:
                break

            if page < pages:
                await _delay()

        return all_hits, errors

    async def search(self, brand_name: str, category: str) -> ProviderSearchResult:
        profile = _get_profile()
        errors: list[str] = []
        all_hits: list[DiscussionHit] = []
        suggested: list[SuggestedQuery] = []

        # 1. Brand tag search (paginated)
        brand_tag = brand_name.lower().replace(" ", "")
        hits, errs = await self._paginated_tag_search(
            brand_tag, "brand_search",
            pages=profile.devto_brand_pages,
            per_page=profile.devto_brand_per_page,
        )
        all_hits.extend(hits)
        errors.extend(errs)
        await _delay()

        # 2. Category tag search — try each word in category (paginated)
        words = category.lower().replace("-", " ").split()
        tags_tried = 0
        max_category_tags = len(words) if profile.devto_multi_tag else 1

        for word in words:
            if tags_tried >= max_category_tags:
                break
            if len(word) < 2:
                continue
            hits, errs = await self._paginated_tag_search(
                word, f"category_search:{word}",
                pages=profile.devto_category_pages,
                per_page=profile.devto_category_per_page,
            )
            all_hits.extend(hits)
            errors.extend(errs)
            tags_tried += 1
            await _delay()

        # If all tag searches returned empty → suggest web fallback
        if not all_hits:
            suggested.append(SuggestedQuery(
                platform="devto",
                provider="devto",
                query=f'"{brand_name}" site:dev.to',
                reason="tag search returned empty",
            ))

        # Deduplicate
        seen: dict[str, DiscussionHit] = {}
        for h in all_hits:
            key = (h.platform, h.detail_id)
            existing = seen.get(key)
            if existing is None or h.raw_score > existing.raw_score:
                seen[key] = h

        return ProviderSearchResult(
            hits=list(seen.values()),
            errors=errors,
            suggested_queries=suggested,
        )

    async def fetch_detail(self, hit: DiscussionHit) -> DiscussionDetail | None:
        profile = _get_profile()
        # Fetch article
        r1 = await _http_get_json(f"https://dev.to/api/articles/{hit.detail_id}")
        if r1.error or not r1.data:
            return None
        article = r1.data
        body = article.get("body_markdown") or article.get("body_html") or ""

        # Fetch comments
        r2 = await _http_get_json(
            "https://dev.to/api/comments",
            params={"a_id": hit.detail_id},
        )
        comments: list[dict] = []
        if not r2.error and r2.data and isinstance(r2.data, list):
            for c in r2.data[:profile.devto_comments_per_post]:
                comments.append({
                    "author": c.get("user", {}).get("username", ""),
                    "text": _truncate(c.get("body_html", ""), 500),
                    "score": 0,  # Dev.to comments don't have public score
                })

        return DiscussionDetail(
            platform="devto",
            detail_id=hit.detail_id,
            title=article.get("title", hit.title),
            full_content=_truncate(body, 2000),
            url=article.get("url", hit.url),
            comments=comments,
        )


# ---------------------------------------------------------------------------
# YouTube — Data API v3
# ---------------------------------------------------------------------------


class YouTubeProvider(CommunityProvider):
    """YouTube community monitoring via Data API v3 or Tavily fallback."""
    name = "youtube"
    status = "enabled"
    requires_auth = False
    auth_env_vars: list[str] = []
    capabilities = {"search", "detail"}
    max_search_calls = 4
    recommended_max_details = 3

    @staticmethod
    def _has_api_key() -> bool:
        return bool(os.environ.get("YOUTUBE_API_KEY"))

    @staticmethod
    def _has_tavily() -> bool:
        return bool(os.environ.get("TAVILY_API_KEY"))

    @property
    def is_enabled(self) -> bool:
        return self._has_api_key() or self._has_tavily()

    @staticmethod
    def parse_search_and_stats(
        search_items: list, stats_map: dict[str, dict], source: str,
    ) -> list[DiscussionHit]:
        hits: list[DiscussionHit] = []
        for item in search_items:
            vid_id = item.get("id", {}).get("videoId", "")
            if not vid_id:
                continue
            snippet = item.get("snippet", {})
            title = snippet.get("title", "")
            if not title:
                continue
            stats = stats_map.get(vid_id, {})
            view_count = int(stats.get("viewCount", 0))
            like_count = int(stats.get("likeCount", 0))
            comment_count = int(stats.get("commentCount", 0))
            raw_score = like_count + comment_count
            hits.append(DiscussionHit(
                platform="youtube",
                title=title,
                url=f"https://www.youtube.com/watch?v={vid_id}",
                engagement_score=min(100, int(view_count / 1000 + like_count * 2 + comment_count * 5)),
                raw_score=raw_score,
                comments_count=comment_count,
                age_days=_age_days(snippet.get("publishedAt", "")),
                author=snippet.get("channelTitle", ""),
                detail_id=vid_id,
                extra_param_1=snippet.get("channelId", ""),
                extra_param_2=snippet.get("channelTitle", ""),
                preview=snippet.get("description", "")[:300],
                source=source,
            ))
        return hits

    @staticmethod
    def parse_tavily_results(results: list, source: str) -> list[DiscussionHit]:
        hits: list[DiscussionHit] = []
        for r in results:
            url = r.get("url", "")
            title = r.get("title", "")
            content = r.get("content", "")
            if not title and not content:
                continue
            vid_id = ""
            if "watch?v=" in url:
                vid_id = url.split("watch?v=")[-1].split("&")[0]
            elif "youtu.be/" in url:
                vid_id = url.split("youtu.be/")[-1].split("?")[0]
            hits.append(DiscussionHit(
                platform="youtube",
                title=title or content.split("\n")[0][:120],
                url=url,
                engagement_score=min(100, int(r.get("score", 0.5) * 100)),
                raw_score=0,
                comments_count=0,
                age_days=0,
                author="",
                detail_id=vid_id or url,
                extra_param_1="",
                extra_param_2="",
                preview=content[:300] if content else "",
                source=source,
            ))
        return hits

    @staticmethod
    def parse_comments_response(data: dict) -> list[dict]:
        comments: list[dict] = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
            text = snippet.get("textDisplay", "")
            if not text:
                continue
            comments.append({
                "author": snippet.get("authorDisplayName", ""),
                "text": text[:500],
                "score": int(snippet.get("likeCount", 0)),
            })
        return comments

    async def _search_via_api(self, query: str, source: str) -> tuple[list[DiscussionHit], list[str]]:
        profile = _get_profile()
        max_results = getattr(profile, "youtube_max_results", 15)
        api_key = os.environ.get("YOUTUBE_API_KEY", "")
        errors: list[str] = []

        # Step 1: search.list (100 quota units)
        from datetime import timedelta
        published_after = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        r = await _http_get_json(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "key": api_key, "part": "snippet", "type": "video",
                "q": query, "order": "relevance",
                "publishedAfter": published_after,
                "maxResults": str(min(max_results, 50)),
            },
        )
        if r.error or not r.data:
            return [], [f"youtube search {source}: {r.error or 'empty'}"]

        items = r.data.get("items", [])
        if not items:
            return [], errors

        # Step 2: videos.list for stats (1 quota unit per call)
        vid_ids = [it.get("id", {}).get("videoId", "") for it in items if it.get("id", {}).get("videoId")]
        stats_map: dict[str, dict] = {}
        if vid_ids:
            await _delay()
            r2 = await _http_get_json(
                "https://www.googleapis.com/youtube/v3/videos",
                params={
                    "key": api_key, "part": "statistics",
                    "id": ",".join(vid_ids[:50]),
                },
            )
            if not r2.error and r2.data:
                for v in r2.data.get("items", []):
                    stats_map[v["id"]] = v.get("statistics", {})

        return self.parse_search_and_stats(items, stats_map, source), errors

    async def _search_via_tavily(self, query: str, source: str) -> tuple[list[DiscussionHit], list[str]]:
        try:
            from tavily import AsyncTavilyClient
        except ImportError:
            return [], ["tavily-python not installed"]
        try:
            client = AsyncTavilyClient(api_key=os.environ["TAVILY_API_KEY"])
            resp = await client.search(
                query=f"{query} site:youtube.com",
                max_results=10,
                search_depth="basic",
            )
            results = resp.get("results", []) if isinstance(resp, dict) else []
            return self.parse_tavily_results(results, source), []
        except Exception as e:
            return [], [f"tavily youtube {source}: {e}"]

    async def search(self, brand_name: str, category: str) -> ProviderSearchResult:
        errors: list[str] = []
        all_hits: list[DiscussionHit] = []
        suggested: list[SuggestedQuery] = []

        use_api = self._has_api_key()
        use_tavily = self._has_tavily()

        for query, source in [
            (brand_name, "brand_search"),
            (category, "category_search"),
        ]:
            if use_api:
                hits, errs = await self._search_via_api(query, source)
            elif use_tavily:
                hits, errs = await self._search_via_tavily(query, source)
            else:
                hits, errs = [], []
                suggested.append(SuggestedQuery(
                    platform="youtube", provider="youtube",
                    query=f'"{query}" site:youtube.com',
                    reason="no YOUTUBE_API_KEY or TAVILY_API_KEY",
                ))
            all_hits.extend(hits)
            errors.extend(errs)
            await _delay()

        # Deduplicate
        seen: dict[str, DiscussionHit] = {}
        for h in all_hits:
            existing = seen.get(h.detail_id)
            if existing is None or h.raw_score > existing.raw_score:
                seen[h.detail_id] = h
        return ProviderSearchResult(hits=list(seen.values()), errors=errors, suggested_queries=suggested)

    async def fetch_detail(self, hit: DiscussionHit) -> DiscussionDetail | None:
        if not self._has_api_key() or not hit.detail_id:
            return None
        api_key = os.environ.get("YOUTUBE_API_KEY", "")
        profile = _get_profile()
        max_comments = getattr(profile, "youtube_comments_per_post", 10)
        r = await _http_get_json(
            "https://www.googleapis.com/youtube/v3/commentThreads",
            params={
                "key": api_key, "part": "snippet",
                "videoId": hit.detail_id,
                "maxResults": str(min(max_comments, 100)),
                "order": "relevance",
            },
        )
        if r.error or not r.data:
            return None
        comments = self.parse_comments_response(r.data)
        return DiscussionDetail(
            platform="youtube",
            detail_id=hit.detail_id,
            title=hit.title,
            full_content=hit.preview[:2000],
            url=hit.url,
            comments=comments,
        )


# ---------------------------------------------------------------------------
# Bluesky — AT Protocol public search API
# ---------------------------------------------------------------------------


class BlueskyProvider(CommunityProvider):
    name = "bluesky"
    status = "enabled"
    requires_auth = False
    auth_env_vars: list[str] = []
    capabilities = {"search", "detail"}
    max_search_calls = 4
    recommended_max_details = 5

    @staticmethod
    def parse_search_response(data: dict, source: str) -> list[DiscussionHit]:
        hits: list[DiscussionHit] = []
        for post in data.get("posts", []):
            record = post.get("record", {})
            text = record.get("text", "")
            if not text:
                continue
            author = post.get("author", {})
            handle = author.get("handle", "")
            like_count = post.get("likeCount", 0) or 0
            repost_count = post.get("repostCount", 0) or 0
            reply_count = post.get("replyCount", 0) or 0
            raw_score = like_count + repost_count + reply_count
            # Build web URL from AT URI: at://did/app.bsky.feed.post/rkey
            uri = post.get("uri", "")
            rkey = uri.rsplit("/", 1)[-1] if "/" in uri else ""
            web_url = f"https://bsky.app/profile/{handle}/post/{rkey}" if handle and rkey else ""
            hits.append(DiscussionHit(
                platform="bluesky",
                title=_truncate(text.split("\n")[0], 120),  # first line as title
                url=web_url,
                engagement_score=min(100, like_count * 2 + repost_count * 4 + reply_count * 3),
                raw_score=raw_score,
                comments_count=reply_count,
                age_days=_age_days(record.get("createdAt", "")),
                author=handle,
                detail_id=uri,
                extra_param_1=handle,
                extra_param_2=author.get("did", ""),
                preview=_truncate(text, 300),
                source=source,
            ))
        return hits

    @staticmethod
    def parse_thread_response(data: dict, hit: DiscussionHit) -> DiscussionDetail | None:
        thread = data.get("thread", {})
        post = thread.get("post", {})
        record = post.get("record", {})
        text = record.get("text", "")
        if not text:
            return None
        comments: list[dict] = []
        profile = _get_profile()
        max_comments = getattr(profile, "bluesky_comments_per_post", 10)
        for reply in thread.get("replies", [])[:max_comments]:
            reply_post = reply.get("post", {})
            reply_record = reply_post.get("record", {})
            reply_author = reply_post.get("author", {})
            reply_text = reply_record.get("text", "")
            if reply_text:
                comments.append({
                    "author": reply_author.get("handle", ""),
                    "text": _truncate(reply_text, 500),
                    "score": (reply_post.get("likeCount", 0) or 0),
                })
        return DiscussionDetail(
            platform="bluesky",
            detail_id=hit.detail_id,
            title=_truncate(text.split("\n")[0], 120),
            full_content=_truncate(text, 2000),
            url=hit.url,
            comments=comments,
        )

    async def search(self, brand_name: str, category: str) -> ProviderSearchResult:
        profile = _get_profile()
        max_results = getattr(profile, "bluesky_max_results", 25)
        errors: list[str] = []
        all_hits: list[DiscussionHit] = []

        for query, source in [
            (brand_name, "brand_search"),
            (category, "category_search"),
        ]:
            r = await _http_get_json(
                "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts",
                params={"q": query, "limit": str(min(max_results, 100))},
            )
            if r.error:
                errors.append(f"{source}: {r.error}")
            elif r.data:
                all_hits.extend(self.parse_search_response(r.data, source))
            await _delay()

        # Deduplicate by AT URI
        seen: dict[str, DiscussionHit] = {}
        for h in all_hits:
            existing = seen.get(h.detail_id)
            if existing is None or h.raw_score > existing.raw_score:
                seen[h.detail_id] = h
        return ProviderSearchResult(hits=list(seen.values()), errors=errors)

    async def fetch_detail(self, hit: DiscussionHit) -> DiscussionDetail | None:
        if not hit.detail_id:
            return None
        r = await _http_get_json(
            "https://public.api.bsky.app/xrpc/app.bsky.feed.getPostThread",
            params={"uri": hit.detail_id, "depth": "1"},
        )
        if r.error or not r.data:
            return None
        return self.parse_thread_response(r.data, hit)


# ---------------------------------------------------------------------------
# Stub providers
# ---------------------------------------------------------------------------


class TwitterProvider(CommunityProvider):
    """Twitter/X community monitoring.

    Primary: tweepy Bearer Token search (requires TWITTER_BEARER_TOKEN, 7-day window).
    Fallback: Tavily site-restricted search (requires TAVILY_API_KEY).
    If neither key is set, degrades to suggested queries (same as old stub).
    """
    name = "twitter"
    status = "enabled"
    requires_auth = False  # graceful fallback chain, no hard requirement
    auth_env_vars: list[str] = []
    capabilities = {"search"}
    max_search_calls = 4
    recommended_max_details = 0

    @staticmethod
    def _has_bearer_token() -> bool:
        return bool(os.environ.get("TWITTER_BEARER_TOKEN"))

    @staticmethod
    def _has_tavily() -> bool:
        return bool(os.environ.get("TAVILY_API_KEY"))

    @property
    def is_enabled(self) -> bool:
        return self._has_bearer_token() or self._has_tavily()

    @staticmethod
    def parse_tweepy_results(tweets: list, users_map: dict, source: str) -> list[DiscussionHit]:
        hits: list[DiscussionHit] = []
        for tweet in tweets:
            text = tweet.text if hasattr(tweet, "text") else str(tweet)
            tweet_id = str(tweet.id) if hasattr(tweet, "id") else ""
            metrics = tweet.public_metrics if hasattr(tweet, "public_metrics") and tweet.public_metrics else {}
            like_count = metrics.get("like_count", 0) or 0
            retweet_count = metrics.get("retweet_count", 0) or 0
            reply_count = metrics.get("reply_count", 0) or 0
            raw_score = like_count + retweet_count + reply_count
            author_id = str(tweet.author_id) if hasattr(tweet, "author_id") and tweet.author_id else ""
            author_username = users_map.get(author_id, "")
            created_at_str = tweet.created_at.isoformat() if hasattr(tweet, "created_at") and tweet.created_at else ""
            hits.append(DiscussionHit(
                platform="twitter",
                title=_truncate(text.split("\n")[0], 120),
                url=f"https://x.com/{author_username}/status/{tweet_id}" if author_username else f"https://x.com/i/status/{tweet_id}",
                engagement_score=min(100, retweet_count * 3 + like_count + reply_count * 2),
                raw_score=raw_score,
                comments_count=reply_count,
                age_days=_age_days(created_at_str),
                author=author_username,
                detail_id=tweet_id,
                extra_param_1=author_username,
                extra_param_2=str(tweet.conversation_id) if hasattr(tweet, "conversation_id") and tweet.conversation_id else "",
                preview=_truncate(text, 300),
                source=source,
            ))
        return hits

    @staticmethod
    def parse_tavily_results(results: list, source: str) -> list[DiscussionHit]:
        hits: list[DiscussionHit] = []
        for r in results:
            url = r.get("url", "")
            title = r.get("title", "")
            content = r.get("content", "")
            if not title and not content:
                continue
            # Extract username from x.com URL
            author = ""
            if "x.com/" in url or "twitter.com/" in url:
                parts = url.split("/")
                for i, p in enumerate(parts):
                    if p in ("x.com", "twitter.com") and i + 1 < len(parts):
                        author = parts[i + 1]
                        break
            # Extract tweet ID from URL
            tweet_id = ""
            if "/status/" in url:
                tweet_id = url.split("/status/")[-1].split("?")[0].split("/")[0]
            hits.append(DiscussionHit(
                platform="twitter",
                title=_truncate(title or content.split("\n")[0], 120),
                url=url,
                engagement_score=min(100, int(r.get("score", 0.5) * 100)),
                raw_score=0,
                comments_count=0,
                age_days=0,
                author=author,
                detail_id=tweet_id or url,
                extra_param_1=author,
                extra_param_2="",
                preview=_truncate(content, 300),
                source=source,
            ))
        return hits

    async def _search_via_tweepy(self, query: str, source: str) -> tuple[list[DiscussionHit], list[str]]:
        errors: list[str] = []
        try:
            import tweepy
        except ImportError:
            return [], ["tweepy not installed"]

        profile = _get_profile()
        max_results = getattr(profile, "twitter_max_results", 25)
        try:
            client = tweepy.Client(bearer_token=os.environ["TWITTER_BEARER_TOKEN"])
            resp = client.search_recent_tweets(
                query=f"{query} -is:retweet lang:en",
                max_results=min(max(10, max_results), 100),
                tweet_fields=["created_at", "public_metrics", "author_id", "conversation_id"],
                expansions=["author_id"],
            )
            users_map: dict[str, str] = {}
            if resp.includes and "users" in resp.includes:
                for u in resp.includes["users"]:
                    users_map[str(u.id)] = u.username
            tweets = resp.data or []
            return self.parse_tweepy_results(tweets, users_map, source), errors
        except Exception as e:
            return [], [f"tweepy {source}: {e}"]

    async def _search_via_tavily(self, query: str, source: str) -> tuple[list[DiscussionHit], list[str]]:
        errors: list[str] = []
        try:
            from tavily import AsyncTavilyClient
        except ImportError:
            return [], ["tavily-python not installed"]

        try:
            client = AsyncTavilyClient(api_key=os.environ["TAVILY_API_KEY"])
            resp = await client.search(
                query=f"{query} site:x.com OR site:twitter.com",
                max_results=10,
                search_depth="basic",
            )
            results = resp.get("results", []) if isinstance(resp, dict) else []
            return self.parse_tavily_results(results, source), errors
        except Exception as e:
            return [], [f"tavily {source}: {e}"]

    async def search(self, brand_name: str, category: str) -> ProviderSearchResult:
        errors: list[str] = []
        all_hits: list[DiscussionHit] = []
        suggested: list[SuggestedQuery] = []

        use_tweepy = self._has_bearer_token()
        use_tavily = self._has_tavily()

        for query, source in [
            (brand_name, "brand_search"),
            (category, "category_search"),
        ]:
            if use_tweepy:
                hits, errs = await self._search_via_tweepy(query, source)
            elif use_tavily:
                hits, errs = await self._search_via_tavily(query, source)
            else:
                hits, errs = [], []
                suggested.append(SuggestedQuery(
                    platform="twitter", provider="twitter",
                    query=f'"{query}" site:x.com OR site:twitter.com',
                    reason="no TWITTER_BEARER_TOKEN or TAVILY_API_KEY",
                ))
            all_hits.extend(hits)
            errors.extend(errs)
            await _delay()

        # Deduplicate by detail_id
        seen: dict[str, DiscussionHit] = {}
        for h in all_hits:
            existing = seen.get(h.detail_id)
            if existing is None or h.raw_score > existing.raw_score:
                seen[h.detail_id] = h
        return ProviderSearchResult(hits=list(seen.values()), errors=errors, suggested_queries=suggested)


class LinkedInProvider(CommunityProvider):
    name = "linkedin"
    status = "stub"
    requires_auth = True
    auth_env_vars = ["LINKEDIN_ACCESS_TOKEN"]
    capabilities: set[str] = set()
    max_search_calls = 0
    recommended_max_details = 0

    async def search(self, brand_name: str, category: str) -> ProviderSearchResult:
        return ProviderSearchResult()


class ProductHuntProvider(CommunityProvider):
    name = "producthunt"
    status = "stub"
    requires_auth = True
    auth_env_vars = ["PRODUCTHUNT_TOKEN"]
    capabilities: set[str] = set()
    max_search_calls = 0
    recommended_max_details = 0

    async def search(self, brand_name: str, category: str) -> ProviderSearchResult:
        # TODO: 使用 Product Hunt GraphQL API v2 实现搜索功能
        # 实现思路：
        # 1. 使用 GraphQL 查询 'posts'，通过 term 参数搜索品牌名称或类别。
        # 2. 解析返回的数据，获取产品名称、Tagline、投票数 (votesCount)、评论数 (commentsCount) 和 URL。
        # 3. 需处理 OAuth2 认证，在请求头中携带 PRODUCTHUNT_TOKEN。
        return ProviderSearchResult()


class BlogSearchProvider(CommunityProvider):
    name = "blog"
    status = "stub"
    requires_auth = False
    auth_env_vars: list[str] = []
    capabilities: set[str] = set()
    max_search_calls = 0
    recommended_max_details = 0

    async def search(self, brand_name: str, category: str) -> ProviderSearchResult:
        return ProviderSearchResult()


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

PROVIDER_REGISTRY: list[CommunityProvider] = [
    RedditProvider(),
    HackerNewsProvider(),
    DevtoProvider(),
    YouTubeProvider(),
    BlueskyProvider(),
    TwitterProvider(),
    LinkedInProvider(),
    ProductHuntProvider(),
    BlogSearchProvider(),
]
