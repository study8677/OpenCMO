"""Community provider architecture for multi-platform discussion monitoring."""

from __future__ import annotations

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
# Unified HTTP helper
# ---------------------------------------------------------------------------

_USER_AGENT = "OpenCMO/0.1 (community-monitor)"


async def _http_get_json(
    url: str,
    params: dict | None = None,
    headers: dict | None = None,
) -> HttpResult:
    """Unified HTTP GET -> JSON with 10s timeout."""
    merged_headers = {"User-Agent": _USER_AGENT}
    if headers:
        merged_headers.update(headers)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params, headers=merged_headers)
        if resp.status_code == 429:
            return HttpResult(data=None, error="rate_limited", status_code=429)
        if resp.status_code >= 400:
            return HttpResult(data=None, error=f"http_{resp.status_code}", status_code=resp.status_code)
        try:
            data = resp.json()
        except Exception:
            return HttpResult(data=None, error="parse_error", status_code=resp.status_code)
        return HttpResult(data=data, error=None, status_code=resp.status_code)
    except httpx.TimeoutException:
        return HttpResult(data=None, error="timeout", status_code=None)
    except Exception:
        return HttpResult(data=None, error="timeout", status_code=None)


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
# Reddit
# ---------------------------------------------------------------------------


class RedditProvider(CommunityProvider):
    name = "reddit"
    status = "enabled"
    requires_auth = False
    auth_env_vars: list[str] = []
    capabilities = {"search", "detail"}
    max_search_calls = 2
    recommended_max_details = 3

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
            if len(comments) >= 10:
                break
        return DiscussionDetail(
            platform="reddit",
            detail_id=hit.detail_id,
            title=title,
            full_content=full_content,
            url=url,
            comments=comments,
        )

    # ---- public API ----

    async def search(self, brand_name: str, category: str) -> ProviderSearchResult:
        errors: list[str] = []
        all_hits: list[DiscussionHit] = []

        # Brand search
        r1 = await _http_get_json(
            "https://www.reddit.com/search.json",
            params={"q": brand_name, "sort": "relevance", "t": "year", "limit": "15"},
        )
        if r1.error:
            errors.append(f"brand search: {r1.error}")
        elif r1.data:
            all_hits.extend(self.parse_search_response(r1.data, "brand_search"))

        # Category search
        r2 = await _http_get_json(
            "https://www.reddit.com/search.json",
            params={"q": category, "sort": "relevance", "t": "year", "limit": "5"},
        )
        if r2.error:
            errors.append(f"category search: {r2.error}")
        elif r2.data:
            all_hits.extend(self.parse_search_response(r2.data, "category_search"))

        # Deduplicate by detail_id, keep higher raw_score
        seen: dict[str, DiscussionHit] = {}
        for h in all_hits:
            key = (h.platform, h.detail_id)
            existing = seen.get(key)
            if existing is None or h.raw_score > existing.raw_score:
                seen[key] = h
        return ProviderSearchResult(hits=list(seen.values()), errors=errors)

    async def fetch_detail(self, hit: DiscussionHit) -> DiscussionDetail | None:
        subreddit = hit.extra_param_1 or "all"
        r = await _http_get_json(
            f"https://www.reddit.com/r/{subreddit}/comments/{hit.detail_id}.json",
            params={"limit": "10", "depth": "1", "sort": "best"},
        )
        if r.error or not r.data:
            return None
        return self.parse_detail_response(r.data, hit)


# ---------------------------------------------------------------------------
# Hacker News
# ---------------------------------------------------------------------------


class HackerNewsProvider(CommunityProvider):
    name = "hackernews"
    status = "enabled"
    requires_auth = False
    auth_env_vars: list[str] = []
    capabilities = {"search", "detail"}
    max_search_calls = 2
    recommended_max_details = 3

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
            if len(comments) >= 10:
                break
        return comments

    async def search(self, brand_name: str, category: str) -> ProviderSearchResult:
        errors: list[str] = []
        all_hits: list[DiscussionHit] = []

        r1 = await _http_get_json(
            "https://hn.algolia.com/api/v1/search",
            params={"query": brand_name, "tags": "story", "hitsPerPage": "10"},
        )
        if r1.error:
            errors.append(f"brand search: {r1.error}")
        elif r1.data:
            all_hits.extend(self.parse_search_response(r1.data, "brand_search"))

        r2 = await _http_get_json(
            "https://hn.algolia.com/api/v1/search",
            params={"query": category, "tags": "story", "hitsPerPage": "5"},
        )
        if r2.error:
            errors.append(f"category search: {r2.error}")
        elif r2.data:
            all_hits.extend(self.parse_search_response(r2.data, "category_search"))

        seen: dict[str, DiscussionHit] = {}
        for h in all_hits:
            key = (h.platform, h.detail_id)
            existing = seen.get(key)
            if existing is None or h.raw_score > existing.raw_score:
                seen[key] = h
        return ProviderSearchResult(hits=list(seen.values()), errors=errors)

    async def fetch_detail(self, hit: DiscussionHit) -> DiscussionDetail | None:
        # Fetch story
        r1 = await _http_get_json(
            f"https://hn.algolia.com/api/v1/items/{hit.detail_id}",
        )
        title = hit.title
        full_content = ""
        if r1.error or not r1.data:
            # Even if story fetch fails, try comments
            pass
        else:
            title = r1.data.get("title", hit.title)
            full_content = _truncate(r1.data.get("text") or "", 2000)

        # Fetch comments
        r2 = await _http_get_json(
            "https://hn.algolia.com/api/v1/search",
            params={"tags": f"comment,story_{hit.detail_id}", "hitsPerPage": "15"},
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
# Dev.to
# ---------------------------------------------------------------------------


class DevtoProvider(CommunityProvider):
    name = "devto"
    status = "enabled"
    requires_auth = False
    auth_env_vars: list[str] = []
    capabilities = {"search", "detail"}
    max_search_calls = 2
    recommended_max_details = 3

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

    async def search(self, brand_name: str, category: str) -> ProviderSearchResult:
        errors: list[str] = []
        all_hits: list[DiscussionHit] = []
        suggested: list[SuggestedQuery] = []

        # Brand search
        r1 = await _http_get_json(
            "https://dev.to/api/articles",
            params={"per_page": "10", "page": "1"},
            headers={"Accept": "application/json"},
        )
        # Dev.to search via tag endpoint is more reliable
        # First try brand as tag
        r_brand = await _http_get_json(
            "https://dev.to/api/articles",
            params={"tag": brand_name.lower().replace(" ", ""), "per_page": "10", "page": "1"},
        )
        if r_brand.error:
            errors.append(f"brand tag search: {r_brand.error}")
        elif r_brand.data and isinstance(r_brand.data, list) and len(r_brand.data) > 0:
            all_hits.extend(self.parse_search_response(r_brand.data, "brand_search"))

        # Category tag search — split category into words, try each as tag
        words = category.lower().replace("-", " ").split()
        tag_hits_found = False
        calls_made = 1  # brand tag already used 1 call
        for word in words:
            if calls_made >= self.max_search_calls:
                break
            if len(word) < 2:
                continue
            r_tag = await _http_get_json(
                "https://dev.to/api/articles",
                params={"tag": word, "per_page": "10", "page": "1"},
            )
            calls_made += 1
            if r_tag.error:
                errors.append(f"tag '{word}' search: {r_tag.error}")
                continue
            if r_tag.data and isinstance(r_tag.data, list) and len(r_tag.data) > 0:
                all_hits.extend(self.parse_search_response(r_tag.data, "tag_monitor"))
                tag_hits_found = True
                break  # found results, stop trying tags

        # If all tag searches returned empty → suggest web fallback
        if not tag_hits_found and not all_hits:
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
            for c in r2.data[:10]:
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
