"""Community monitoring tools — scan_community + fetch_discussion_detail."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime

from agents import function_tool

from opencmo.tools.community_providers import (
    PROVIDER_REGISTRY,
    DiscussionDetail,
    DiscussionHit,
    DisabledProvider,
    ProviderError,
    ScanResult,
    SuggestedQuery,
    _truncate,
)

# ---------------------------------------------------------------------------
# Stub query templates (brand / category / current_year placeholders)
# ---------------------------------------------------------------------------

_STUB_QUERIES: dict[str, list[dict]] = {
    "twitter": [
        {"query": '"{brand}" site:x.com OR site:twitter.com', "reason": "stub — no free API"},
    ],
    "linkedin": [
        {"query": '"{brand}" site:linkedin.com', "reason": "stub — no public search API"},
    ],
    "producthunt": [
        {"query": '"{brand}" site:producthunt.com', "reason": "stub — requires API token"},
    ],
    "blog": [
        {"query": '"{brand}" review OR alternative OR vs', "reason": "stub — no unified API"},
        {"query": "best {category} tools {current_year}", "reason": "stub — category discovery"},
    ],
}


def _render_stub_queries(
    provider_name: str, brand_name: str, category: str,
) -> list[SuggestedQuery]:
    templates = _STUB_QUERIES.get(provider_name, [])
    year = str(datetime.now().year)
    out: list[SuggestedQuery] = []
    for t in templates:
        q = t["query"].replace("{brand}", brand_name).replace("{category}", category).replace("{current_year}", year)
        out.append(SuggestedQuery(
            platform=provider_name,
            provider=provider_name,
            query=q,
            reason=t["reason"],
        ))
    return out


# ---------------------------------------------------------------------------
# Output trimming
# ---------------------------------------------------------------------------

_MAX_JSON_CHARS = 8000


def _trim_scan_result(sr: ScanResult) -> ScanResult:
    """Trim ScanResult to fit within output budget. Mutates and returns sr."""
    serialized = json.dumps(asdict(sr), ensure_ascii=False)
    if len(serialized) <= _MAX_JSON_CHARS:
        return sr

    # Step 1: shorten all previews to 100 chars
    for h in sr.hits:
        h.preview = _truncate(h.preview, 100)
    serialized = json.dumps(asdict(sr), ensure_ascii=False)
    if len(serialized) <= _MAX_JSON_CHARS:
        return sr

    # Step 2: remove lowest-engagement hits one at a time
    sr.hits.sort(key=lambda h: (h.engagement_score, h.raw_score))
    while len(serialized) > _MAX_JSON_CHARS and sr.hits:
        sr.hits.pop(0)
        serialized = json.dumps(asdict(sr), ensure_ascii=False)

    return sr


# ---------------------------------------------------------------------------
# scan_community
# ---------------------------------------------------------------------------


async def _scan_community_impl(brand_name: str, category: str) -> str:
    """Core scan logic — called by the function_tool wrapper and tests."""
    result = ScanResult()

    for provider in PROVIDER_REGISTRY:
        if not provider.is_enabled:
            # Disabled / stub → generate suggested queries + record
            result.disabled_providers.append(DisabledProvider(
                name=provider.name,
                reason=f"stub — {provider.status}" if provider.status == "stub" else "disabled",
            ))
            result.suggested_queries.extend(
                _render_stub_queries(provider.name, brand_name, category),
            )
            continue

        # Enabled provider → call search
        try:
            pr = await provider.search(brand_name, category)
        except Exception as exc:
            result.provider_errors.append(ProviderError(
                provider=provider.name,
                errors=[str(exc)],
            ))
            continue

        # Merge hits (per-provider top-10 by engagement_score)
        sorted_hits = sorted(pr.hits, key=lambda h: h.engagement_score, reverse=True)[:10]
        result.hits.extend(sorted_hits)

        # Collect errors
        if pr.errors:
            result.provider_errors.append(ProviderError(
                provider=provider.name,
                errors=pr.errors,
            ))

        # Collect suggested queries
        result.suggested_queries.extend(pr.suggested_queries)

    # Deduplicate suggested_queries by (platform, query)
    seen_sq: set[tuple[str, str]] = set()
    unique_sq: list[SuggestedQuery] = []
    for sq in result.suggested_queries:
        key = (sq.platform, sq.query)
        if key not in seen_sq:
            seen_sq.add(key)
            unique_sq.append(sq)
    result.suggested_queries = unique_sq

    # Deterministic sort: platform asc, engagement desc, raw_score desc, detail_id asc
    result.hits.sort(key=lambda h: (h.platform, -h.engagement_score, -h.raw_score, h.detail_id))

    # Trim to fit output budget
    result = _trim_scan_result(result)

    return json.dumps(asdict(result), ensure_ascii=False)


@function_tool
async def scan_community(brand_name: str, category: str) -> str:
    """Scan Reddit, Hacker News, Dev.to and other platforms for brand/category discussions.

    Returns a structured JSON envelope with hits, disabled platforms, errors, and
    suggested web-search queries for platforms without free API access.

    Args:
        brand_name: The brand or product name to search for.
        category: The product category for broader search context.
    """
    return await _scan_community_impl(brand_name, category)


# ---------------------------------------------------------------------------
# fetch_discussion_detail
# ---------------------------------------------------------------------------

# Build provider lookup once
_PROVIDER_MAP = {p.name: p for p in PROVIDER_REGISTRY}


@function_tool
async def fetch_discussion_detail(
    platform: str,
    detail_id: str,
    extra_param_1: str = "",
    extra_param_2: str = "",
) -> str:
    """Fetch full post content and top comments for a discussion.

    Use the platform, detail_id, extra_param_1 and extra_param_2 values
    directly from scan_community results.

    Args:
        platform: The platform name (e.g. "reddit", "hackernews", "devto").
        detail_id: The post/story/article ID from scan_community results.
        extra_param_1: Platform-specific parameter (e.g. subreddit name for Reddit). Empty if not needed.
        extra_param_2: Reserved for future platforms. Currently always empty.
    """
    provider = _PROVIDER_MAP.get(platform)
    if provider is None:
        return json.dumps({"ok": False, "error": "platform_not_found"})

    if "detail" not in provider.capabilities:
        return json.dumps({"ok": False, "error": "detail_not_supported"})

    # Build a minimal DiscussionHit for the provider
    hit = DiscussionHit(
        platform=platform,
        title="",
        url="",
        engagement_score=0,
        raw_score=0,
        comments_count=0,
        age_days=0,
        author="",
        detail_id=detail_id,
        extra_param_1=extra_param_1,
        extra_param_2=extra_param_2,
        preview="",
        source="",
    )

    try:
        detail = await provider.fetch_detail(hit)
    except Exception:
        return json.dumps({"ok": False, "error": "fetch_failed"})

    if detail is None:
        return json.dumps({"ok": False, "error": "not_found"})

    # Enforce limits
    detail.full_content = _truncate(detail.full_content, 2000)
    detail.comments = detail.comments[:10]
    for c in detail.comments:
        c["text"] = _truncate(c.get("text", ""), 500)

    return json.dumps({"ok": True, "detail": asdict(detail)}, ensure_ascii=False)
