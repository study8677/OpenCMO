"""Query planning for multi-platform community retrieval."""

from __future__ import annotations

from urllib.parse import urlparse

from opencmo.tools.community_providers import (
    QuerySpec,
    SearchQueryPlan,
    _get_subreddits_for_category,
    _get_v2ex_nodes_for_category,
)

_TEXT_SEARCH_PROVIDERS = (
    "reddit",
    "hackernews",
    "devto",
    "youtube",
    "bluesky",
    "twitter",
    "linkedin",
    "producthunt",
    "blog",
    "v2ex",
    "weibo",
    "bilibili",
    "xueqiu",
    "xiaohongshu",
    "wechat",
    "douyin",
)


def _unique_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        cleaned = value.strip()
        key = cleaned.lower()
        if not cleaned or key in seen:
            continue
        seen.add(key)
        unique.append(cleaned)
    return unique


def _derive_domain_terms(canonical_url: str | None) -> list[str]:
    if not canonical_url:
        return []
    parsed = urlparse(canonical_url)
    host = (parsed.hostname or "").lower().removeprefix("www.")
    if not host:
        return []
    parts = [host]
    label = host.split(".")[0]
    if label and label != host:
        parts.append(label)
    return _unique_keep_order(parts)


def _is_placeholder_category(category: str) -> bool:
    """Return True if the category is a placeholder that should not be used as a search term."""
    return not category or category.lower() in ("auto", "unknown", "other", "general")


def _english_queries(
    brand_name: str,
    category: str,
    tracked_keywords: list[str],
    competitor_names: list[str],
    competitor_keywords: list[str],
    domain_terms: list[str],
) -> tuple[list[QuerySpec], list[QuerySpec], list[QuerySpec], list[QuerySpec], list[QuerySpec]]:
    direct = [
        QuerySpec(
            query=f'"{brand_name}"',
            source="brand_exact",
            intent_type="direct_mention",
            matched_terms=[brand_name],
            confidence=0.95,
            reason="Matched the exact brand name query.",
        ),
    ]
    direct.extend(
        QuerySpec(
            query=f'"{brand_name}" "{term}"',
            source="brand_domain",
            intent_type="direct_mention",
            matched_terms=[brand_name, term],
            confidence=0.98,
            reason="Matched a brand plus domain disambiguation query.",
        )
        for term in domain_terms
    )
    direct.extend(
        QuerySpec(
            query=keyword,
            source="tracked_keyword",
            intent_type="direct_mention",
            matched_terms=[brand_name, keyword],
            confidence=0.82,
            reason="Matched a tracked keyword derived from the project context.",
        )
        for keyword in tracked_keywords[:4]
    )

    problem = [
        QuerySpec(
            query=keyword,
            source="problem_keyword",
            intent_type="opportunity",
            matched_terms=[keyword],
            confidence=0.62,
            reason="Matched a problem-first community query.",
        )
        for keyword in tracked_keywords[:6]
    ]

    category_specs = [] if _is_placeholder_category(category) else [
        QuerySpec(
            query=category,
            source="category_search",
            intent_type="opportunity",
            matched_terms=[category],
            confidence=0.55,
            reason="Matched the broader category query.",
        ),
        QuerySpec(
            query=f"best {category} tools",
            source="category_best_tools",
            intent_type="opportunity",
            matched_terms=[category],
            confidence=0.58,
            reason="Matched a category shortlist query.",
        ),
    ]

    competitor = []
    for name in competitor_names[:4]:
        competitor.append(QuerySpec(
            query=f"{brand_name} vs {name}",
            source="competitor_comparison",
            intent_type="competitor_mention",
            matched_terms=[brand_name, name],
            confidence=0.76,
            reason="Matched a competitor comparison query.",
        ))
        competitor.append(QuerySpec(
            query=f"{name} alternative",
            source="competitor_alternative",
            intent_type="competitor_mention",
            matched_terms=[name, "alternative"],
            confidence=0.68,
            reason="Matched a competitor alternative query.",
        ))
    competitor.extend(
        QuerySpec(
            query=keyword,
            source="competitor_keyword",
            intent_type="competitor_mention",
            matched_terms=[keyword],
            confidence=0.64,
            reason="Matched a competitor keyword query.",
        )
        for keyword in competitor_keywords[:4]
    )

    opportunity = [] if _is_placeholder_category(category) else [
        QuerySpec(
            query=f"{category} alternatives",
            source="opportunity_alternatives",
            intent_type="opportunity",
            matched_terms=[category],
            confidence=0.6,
            reason="Matched a category alternatives opportunity query.",
        ),
        QuerySpec(
            query=f"looking for {category}",
            source="opportunity_looking_for",
            intent_type="opportunity",
            matched_terms=[category],
            confidence=0.52,
            reason="Matched a high-intent opportunity query.",
        ),
    ]

    return (
        _dedupe_query_specs(direct),
        _dedupe_query_specs(problem),
        _dedupe_query_specs(category_specs),
        _dedupe_query_specs(competitor),
        _dedupe_query_specs(opportunity),
    )


def _chinese_queries(
    brand_name: str,
    category: str,
    tracked_keywords: list[str],
    competitor_names: list[str],
    competitor_keywords: list[str],
    domain_terms: list[str],
) -> tuple[list[QuerySpec], list[QuerySpec], list[QuerySpec], list[QuerySpec], list[QuerySpec]]:
    direct = [
        QuerySpec(
            query=f'"{brand_name}"',
            source="brand_exact",
            intent_type="direct_mention",
            matched_terms=[brand_name],
            confidence=0.95,
            reason="Matched the exact brand name query.",
        ),
    ]
    direct.extend(
        QuerySpec(
            query=f'"{brand_name}" "{term}"',
            source="brand_domain",
            intent_type="direct_mention",
            matched_terms=[brand_name, term],
            confidence=0.98,
            reason="Matched a brand plus domain disambiguation query.",
        )
        for term in domain_terms
    )
    direct.extend(
        QuerySpec(
            query=keyword,
            source="tracked_keyword",
            intent_type="direct_mention",
            matched_terms=[brand_name, keyword],
            confidence=0.82,
            reason="Matched a tracked keyword derived from the project context.",
        )
        for keyword in tracked_keywords[:4]
    )

    problem = [
        QuerySpec(
            query=keyword,
            source="problem_keyword",
            intent_type="opportunity",
            matched_terms=[keyword],
            confidence=0.62,
            reason="Matched a problem-first community query.",
        )
        for keyword in tracked_keywords[:6]
    ]

    category_specs = [] if _is_placeholder_category(category) else [
        QuerySpec(
            query=category,
            source="category_search",
            intent_type="opportunity",
            matched_terms=[category],
            confidence=0.55,
            reason="Matched the broader category query.",
        ),
        QuerySpec(
            query=f"{category} 推荐",
            source="category_recommendation",
            intent_type="opportunity",
            matched_terms=[category, "推荐"],
            confidence=0.58,
            reason="Matched a recommendation-style category query.",
        ),
        QuerySpec(
            query=f"{category} 怎么样",
            source="category_how_is_it",
            intent_type="opportunity",
            matched_terms=[category, "怎么样"],
            confidence=0.54,
            reason="Matched an evaluation-style category query.",
        ),
    ]

    competitor = []
    for name in competitor_names[:4]:
        competitor.append(QuerySpec(
            query=f"{brand_name} {name} 对比",
            source="competitor_comparison",
            intent_type="competitor_mention",
            matched_terms=[brand_name, name, "对比"],
            confidence=0.76,
            reason="Matched a competitor comparison query.",
        ))
        competitor.append(QuerySpec(
            query=f"{name} 替代",
            source="competitor_alternative",
            intent_type="competitor_mention",
            matched_terms=[name, "替代"],
            confidence=0.68,
            reason="Matched a competitor alternative query.",
        ))
    competitor.extend(
        QuerySpec(
            query=keyword,
            source="competitor_keyword",
            intent_type="competitor_mention",
            matched_terms=[keyword],
            confidence=0.64,
            reason="Matched a competitor keyword query.",
        )
        for keyword in competitor_keywords[:4]
    )

    opportunity = [] if _is_placeholder_category(category) else [
        QuerySpec(
            query=f"{category} 平替",
            source="opportunity_budget_alternative",
            intent_type="opportunity",
            matched_terms=[category, "平替"],
            confidence=0.6,
            reason="Matched a budget-alternative opportunity query.",
        ),
        QuerySpec(
            query=f"{category} 测评",
            source="opportunity_review",
            intent_type="opportunity",
            matched_terms=[category, "测评"],
            confidence=0.6,
            reason="Matched a review-style opportunity query.",
        ),
    ]

    return (
        _dedupe_query_specs(direct),
        _dedupe_query_specs(problem),
        _dedupe_query_specs(category_specs),
        _dedupe_query_specs(competitor),
        _dedupe_query_specs(opportunity),
    )


def _dedupe_query_specs(specs: list[QuerySpec]) -> list[QuerySpec]:
    seen: set[str] = set()
    unique: list[QuerySpec] = []
    for spec in specs:
        key = spec.query.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(spec)
    return unique


def _provider_query_map(
    direct: list[QuerySpec],
    problem: list[QuerySpec],
    category_specs: list[QuerySpec],
    competitor: list[QuerySpec],
    opportunity: list[QuerySpec],
) -> dict[str, list[QuerySpec]]:
    short_text = _dedupe_query_specs(direct[:3] + category_specs[:2] + opportunity[:2] + competitor[:2])
    return {
        provider: (
            _dedupe_query_specs(direct[:4] + problem[:3] + competitor[:3] + opportunity[:2])
            if provider == "reddit"
            else _dedupe_query_specs(direct[:3] + category_specs[:2] + competitor[:2] + opportunity[:2])
            if provider in {"hackernews", "bluesky", "twitter", "youtube", "weibo", "bilibili", "xueqiu"}
            else short_text
        )
        for provider in _TEXT_SEARCH_PROVIDERS
    }


def build_query_plan(
    brand_name: str,
    category: str,
    tracked_keywords: list[str] | None = None,
    competitor_names: list[str] | None = None,
    competitor_keywords: list[str] | None = None,
    canonical_url: str | None = None,
    locale: str | None = None,
) -> SearchQueryPlan:
    tracked = _unique_keep_order(list(tracked_keywords or []))
    competitors = _unique_keep_order(list(competitor_names or []))
    competitor_kw = _unique_keep_order(list(competitor_keywords or []))
    domain_terms = _derive_domain_terms(canonical_url)

    if (locale or "").lower().startswith("zh"):
        direct, problem, category_specs, competitor, opportunity = _chinese_queries(
            brand_name,
            category,
            tracked,
            competitors,
            competitor_kw,
            domain_terms,
        )
    else:
        direct, problem, category_specs, competitor, opportunity = _english_queries(
            brand_name,
            category,
            tracked,
            competitors,
            competitor_kw,
            domain_terms,
        )

    return SearchQueryPlan(
        direct_brand_queries=direct,
        problem_queries=problem,
        category_queries=category_specs,
        competitor_queries=competitor,
        opportunity_queries=opportunity,
        provider_queries=_provider_query_map(direct, problem, category_specs, competitor, opportunity),
        platform_targeting={
            "reddit": _get_subreddits_for_category(category),
            "v2ex": _get_v2ex_nodes_for_category(category),
        },
    )
