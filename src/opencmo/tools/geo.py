import json

from agents import function_tool

from opencmo.tools.geo_providers import GEO_PROVIDER_REGISTRY, GeoProviderResult


@function_tool
async def scan_geo_visibility(brand_name: str, category: str) -> str:
    """Scan AI search platforms for brand visibility and compute a GEO score.

    Checks multiple AI platforms (Perplexity, You.com, ChatGPT, Claude, Gemini)
    for brand mentions, position, and sentiment using multiple query templates.
    Crawl-based providers run by default; API-based providers require environment
    variables to enable.
    Returns a GEO Score (0-100) with breakdown and improvement suggestions.

    Args:
        brand_name: The brand or product name to search for.
        category: The product category (e.g., "web scraping", "project management").
    """
    enabled_providers = [p for p in GEO_PROVIDER_REGISTRY if p.is_enabled]
    disabled_providers = [p for p in GEO_PROVIDER_REGISTRY if not p.is_enabled]

    if not enabled_providers:
        return "No GEO providers are enabled. Check your environment configuration."

    # Use multi-query aggregation for deeper analysis
    aggregated_results = {}
    flat_results: dict[str, GeoProviderResult] = {}

    for provider in enabled_providers:
        try:
            agg = await provider.check_visibility_multi(brand_name, category)
            aggregated_results[provider.name] = agg
            # Create a backward-compatible flat result for scoring
            flat_results[provider.name] = GeoProviderResult(
                platform=provider.name,
                mentioned=agg.mentioned,
                mention_count=agg.total_mention_count,
                position_pct=agg.best_position_pct,
                content_snippet="",  # snippets are in per_query_results
                error=agg.error,
            )
        except Exception as e:
            flat_results[provider.name] = GeoProviderResult(
                platform=provider.name,
                mentioned=False,
                mention_count=0,
                position_pct=None,
                content_snippet="",
                error=str(e),
            )

    # Compute GEO Score
    # Visibility (0-40): mentioned on how many platforms
    platforms_mentioned = sum(1 for r in flat_results.values() if r.mentioned)
    visibility_score = int(platforms_mentioned / len(enabled_providers) * 40)

    # Position (0-30): earlier mentions = higher score
    position_scores = []
    for r in flat_results.values():
        if r.position_pct is not None:
            # 0% position = score 30, 100% = score 0
            position_scores.append(30 * (1 - r.position_pct / 100))
    position_score = (
        int(sum(position_scores) / len(position_scores)) if position_scores else 0
    )

    # Sentiment (0-30): LLM-based analysis of how AI platforms talk about the brand
    try:
        from opencmo.tools.text_signals import analyze_geo_sentiment

        # Collect snippets from all platforms for sentiment analysis
        sentiment_snippets: dict[str, str] = {}
        for name, agg in aggregated_results.items():
            parts = []
            for qr in agg.per_query_results:
                if qr.content_snippet:
                    parts.append(qr.content_snippet)
            if parts:
                sentiment_snippets[name] = "\n".join(parts)

        signal = await analyze_geo_sentiment(brand_name, sentiment_snippets)
        sentiment_score = signal.score
        sentiment_label = signal.label
        sentiment_reasoning = signal.reasoning
    except Exception:
        # Graceful fallback if sentiment analysis fails
        sentiment_score = 15 if platforms_mentioned > 0 else 0
        sentiment_label = "neutral" if platforms_mentioned > 0 else "not_mentioned"
        sentiment_reasoning = "Sentiment analysis unavailable"

    geo_score = visibility_score + position_score + sentiment_score

    # Persist scan (best-effort, do not block on failure)
    try:
        from opencmo import storage

        platform_results_json = json.dumps(
            {
                name: {
                    "mentioned": r.mentioned,
                    "mention_count": r.mention_count,
                    "position_pct": r.position_pct,
                    "error": r.error,
                }
                for name, r in flat_results.items()
            }
        )
        # save_geo_scan requires a project_id; use project_id=0 as ad-hoc scan
        await storage.save_geo_scan(
            project_id=0,
            geo_score=geo_score,
            visibility_score=visibility_score,
            position_score=position_score,
            sentiment_score=sentiment_score,
            platform_results_json=platform_results_json,
        )
    except Exception:
        pass  # storage persistence is best-effort

    # Build report
    lines = [
        f"# GEO Visibility Report: {brand_name}",
        f"**Category**: {category}\n",
        f"## GEO Score: {geo_score}/100\n",
        "| Component | Score | Max |",
        "|-----------|-------|-----|",
        f"| Visibility | {visibility_score} | 40 |",
        f"| Position | {position_score} | 30 |",
        f"| Sentiment ({sentiment_label}) | {sentiment_score} | 30 |",
        f"| **Total** | **{geo_score}** | **100** |",
        "",
        f"**Sentiment Analysis**: {sentiment_reasoning}",
        "",
        f"## Platform Results ({len(enabled_providers)} enabled, {len(disabled_providers)} disabled)\n",
    ]

    for name, data in flat_results.items():
        if data.error and not data.mentioned:
            lines.append(f"### {name} [enabled]: ERROR -- {data.error}\n")
            continue
        status = "FOUND" if data.mentioned else "NOT FOUND"
        lines.append(f"### {name} [enabled]: {status}")
        if data.mentioned:
            lines.append(f"- Total mentions: {data.mention_count}")
            if data.position_pct is not None:
                lines.append(
                    f"- Best mention position: {data.position_pct}% through response"
                )

        # Show per-query breakdown if available
        agg = aggregated_results.get(name)
        if agg and len(agg.per_query_results) > 1:
            lines.append(f"- Queries checked: {len(agg.per_query_results)}")
            for qr in agg.per_query_results:
                q_status = "✅" if qr.mentioned else "❌"
                q_mentions = f" ({qr.mention_count} mentions)" if qr.mentioned else ""
                lines.append(f"  - {q_status} `{qr.query}`{q_mentions}")
        lines.append("")

    if disabled_providers:
        lines.append("## Disabled Platforms\n")
        for p in disabled_providers:
            env_hint = ", ".join(p.auth_env_vars) if p.auth_env_vars else "N/A"
            extra = ""
            if p.name == "ChatGPT":
                extra = " (also requires OPENCMO_GEO_CHATGPT=1)"
            elif p.name == "Claude":
                extra = " (also requires `anthropic` package)"
            elif p.name == "Gemini":
                extra = " (also requires `google-generativeai` package)"
            lines.append(f"- **{p.name}**: set {env_hint}{extra} to enable")
        lines.append("")

    lines.extend(
        [
            "## Raw Context (for agent analysis)\n",
            "Below are content snippets from each platform for the agent to analyze sentiment and context:\n",
        ]
    )
    for name in aggregated_results:
        agg = aggregated_results[name]
        for qr in agg.per_query_results:
            snippet = qr.content_snippet
            if snippet:
                lines.append(f"### {name} — `{qr.query}`\n{snippet[:3000]}\n")

    return "\n".join(lines)
