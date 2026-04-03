"""Trend research tool — open-ended topic exploration across community platforms."""

from __future__ import annotations

import json
import re

from agents import function_tool

from opencmo.tools.community_providers import (
    PROVIDER_REGISTRY,
    DiscussionHit,
    ProviderError,
)
from opencmo.tools.community_scoring import rescore_hits

# ---------------------------------------------------------------------------
# Query expansion
# ---------------------------------------------------------------------------


def expand_queries(topic: str) -> list[str]:
    """Generate 2-3 search query variants from a topic.

    Uses simple template patterns, no LLM calls.
    """
    topic = topic.strip()
    queries = [topic]

    # Comparative mode: "X vs Y" → search each independently
    vs_match = re.match(r"(.+?)\s+(?:vs\.?|versus|compared?\s+to)\s+(.+)", topic, re.IGNORECASE)
    if vs_match:
        queries.append(vs_match.group(1).strip())
        queries.append(vs_match.group(2).strip())
        return queries

    # Add variant with "review" or "alternative"
    words = topic.split()
    if len(words) >= 2:
        queries.append(f"{topic} review")
    if len(words) <= 4:
        queries.append(f"best {topic} tools")

    return queries[:3]


def is_comparative(topic: str) -> bool:
    """Check if the topic is a comparative query."""
    return bool(re.search(r"\b(?:vs\.?|versus|compared?\s+to)\b", topic, re.IGNORECASE))


# ---------------------------------------------------------------------------
# Core implementation
# ---------------------------------------------------------------------------


async def _research_trend_impl(
    topic: str,
    time_window_days: int = 30,
    platforms: str = "all",
    mode: str = "summary",
) -> str:
    """Core trend research logic."""
    from opencmo.scrape_config import get_scrape_profile

    profile = get_scrape_profile()
    halflife = getattr(profile, "scoring_recency_halflife_days", 23.0)
    convergence_threshold = getattr(profile, "scoring_convergence_threshold", 0.5)

    # Determine which providers to use
    platform_set = None
    if platforms != "all":
        platform_set = {p.strip().lower() for p in platforms.split(",")}

    active_providers = [
        p for p in PROVIDER_REGISTRY
        if p.is_enabled and (platform_set is None or p.name in platform_set)
    ]

    if not active_providers:
        return json.dumps({
            "error": "No enabled providers match the requested platforms.",
            "available": [p.name for p in PROVIDER_REGISTRY if p.is_enabled],
        })

    # Expand queries
    queries = expand_queries(topic)
    all_hits: list[DiscussionHit] = []
    all_errors: list[ProviderError] = []

    # Run queries across providers
    for provider in active_providers:
        for query in queries:
            try:
                pr = await provider.search(query, topic)
                all_hits.extend(pr.hits)
                if pr.errors:
                    all_errors.append(ProviderError(provider=provider.name, errors=pr.errors))
            except Exception as exc:
                all_errors.append(ProviderError(provider=provider.name, errors=[str(exc)]))

    # Filter by time window
    if time_window_days > 0:
        all_hits = [h for h in all_hits if h.age_days <= time_window_days or h.age_days == 0]

    # Deduplicate by (platform, detail_id)
    seen: dict[tuple[str, str], DiscussionHit] = {}
    for h in all_hits:
        key = (h.platform, h.detail_id)
        existing = seen.get(key)
        if existing is None or h.raw_score > existing.raw_score:
            seen[key] = h
    deduped = list(seen.values())

    # Rescore with multi-signal scoring
    rescore_hits(deduped, topic, halflife_days=halflife, convergence_threshold=convergence_threshold)

    # Sort by engagement_score descending
    deduped.sort(key=lambda h: -h.engagement_score)

    # Build output based on mode
    if mode == "comparative" or is_comparative(topic):
        return _format_comparative(topic, deduped, all_errors)
    else:
        return _format_summary(topic, deduped, all_errors, time_window_days)


def _format_summary(
    topic: str,
    hits: list[DiscussionHit],
    errors: list[ProviderError],
    time_window_days: int,
) -> str:
    """Format hits as a summary briefing."""
    # Platform distribution
    platform_counts: dict[str, int] = {}
    for h in hits:
        platform_counts[h.platform] = platform_counts.get(h.platform, 0) + 1

    lines = [
        f"# Trend Research: {topic}",
        f"**Time window**: last {time_window_days} days",
        f"**Total discussions found**: {len(hits)}",
        f"**Platform distribution**: {', '.join(f'{k} ({v})' for k, v in sorted(platform_counts.items()))}",
        "",
    ]

    if errors:
        error_platforms = {e.provider for e in errors}
        lines.append(f"**Provider errors**: {', '.join(error_platforms)}\n")

    # Top discussions
    top = hits[:20]
    if top:
        lines.append("## Top Discussions\n")
        lines.append("| # | Platform | Title | Score | Comments | Age |")
        lines.append("|---|----------|-------|-------|----------|-----|")
        for i, h in enumerate(top, 1):
            title_short = h.title[:60] + ("..." if len(h.title) > 60 else "")
            age = f"{h.age_days}d" if h.age_days > 0 else "?"
            lines.append(
                f"| {i} | {h.platform} | [{title_short}]({h.url}) "
                f"| {h.engagement_score} | {h.comments_count} | {age} |"
            )

    # Platform breakdown
    lines.append("\n## By Platform\n")
    for platform in sorted(platform_counts.keys()):
        platform_hits = [h for h in hits if h.platform == platform][:5]
        lines.append(f"### {platform.title()} ({platform_counts[platform]} results)\n")
        for h in platform_hits:
            lines.append(f"- [{h.title[:80]}]({h.url}) — score {h.engagement_score}, {h.comments_count} comments")
        lines.append("")

    return "\n".join(lines)


def _format_comparative(
    topic: str,
    hits: list[DiscussionHit],
    errors: list[ProviderError],
) -> str:
    """Format comparative analysis for 'X vs Y' queries."""
    parts = re.split(r"\s+(?:vs\.?|versus|compared?\s+to)\s+", topic, flags=re.IGNORECASE)
    if len(parts) < 2:
        return _format_summary(topic, hits, errors, 30)

    side_a, side_b = parts[0].strip(), parts[1].strip()

    def classify(h: DiscussionHit) -> str:
        text = f"{h.title} {h.preview}".lower()
        has_a = side_a.lower() in text
        has_b = side_b.lower() in text
        if has_a and has_b:
            return "both"
        elif has_a:
            return "a"
        elif has_b:
            return "b"
        return "both"

    hits_a = [h for h in hits if classify(h) in ("a", "both")]
    hits_b = [h for h in hits if classify(h) in ("b", "both")]

    lines = [
        f"# Comparative Analysis: {side_a} vs {side_b}",
        f"**Total discussions**: {len(hits)}",
        "",
        f"## {side_a} ({len(hits_a)} mentions)\n",
    ]

    for h in hits_a[:10]:
        lines.append(f"- [{h.title[:80]}]({h.url}) ({h.platform}, score {h.engagement_score})")

    lines.append(f"\n## {side_b} ({len(hits_b)} mentions)\n")
    for h in hits_b[:10]:
        lines.append(f"- [{h.title[:80]}]({h.url}) ({h.platform}, score {h.engagement_score})")

    # Platform breakdown
    lines.append("\n## Platform Sentiment Signals\n")
    for platform in sorted({h.platform for h in hits}):
        p_hits = [h for h in hits if h.platform == platform]
        a_count = sum(1 for h in p_hits if classify(h) in ("a", "both"))
        b_count = sum(1 for h in p_hits if classify(h) in ("b", "both"))
        lines.append(f"- **{platform}**: {side_a} mentioned {a_count}x, {side_b} mentioned {b_count}x")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Function tool
# ---------------------------------------------------------------------------


@function_tool
async def research_trend(
    topic: str,
    time_window_days: int = 30,
    platforms: str = "all",
    mode: str = "summary",
) -> str:
    """Research a topic across community platforms and synthesize findings.

    Searches Reddit, Hacker News, Dev.to, YouTube, Bluesky, Twitter/X for
    recent discussions, ranks by multi-signal scoring (velocity, relevance,
    recency, cross-platform convergence), and produces a structured briefing.

    Args:
        topic: The topic to research (e.g. "AI code review tools", "Cursor vs Windsurf").
        time_window_days: Only include discussions from the last N days (default 30).
        platforms: Comma-separated platform names or "all" (e.g. "reddit,hackernews").
        mode: "summary" for ranked overview, "comparative" for "X vs Y" side-by-side analysis.
    """
    return await _research_trend_impl(topic, time_window_days, platforms, mode)
