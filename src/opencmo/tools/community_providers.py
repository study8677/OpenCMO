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
# Stub providers
# ---------------------------------------------------------------------------


class TwitterProvider(CommunityProvider):
    name = "twitter"
    status = "stub"
    requires_auth = True
    auth_env_vars = ["TWITTER_API_KEY"]
    capabilities: set[str] = set()
    max_search_calls = 0
    recommended_max_details = 0

    async def search(self, brand_name: str, category: str) -> ProviderSearchResult:
        return ProviderSearchResult()


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
    TwitterProvider(),
    LinkedInProvider(),
    ProductHuntProvider(),
    BlogSearchProvider(),
]
