from agents import function_tool
from crawl4ai import AsyncWebCrawler

from opencmo.tools.crawl import _extract_markdown


@function_tool
async def scan_geo_visibility(brand_name: str, category: str) -> str:
    """Scan AI search platforms for brand visibility and compute a GEO score.

    Checks Perplexity and You.com for brand mentions, position, and sentiment.
    Returns a GEO Score (0-100) with breakdown and improvement suggestions.

    Args:
        brand_name: The brand or product name to search for.
        category: The product category (e.g., "web scraping", "project management").
    """
    platforms = {
        "Perplexity": f"https://www.perplexity.ai/search?q=best+{category.replace(' ', '+')}+tools",
        "You.com": f"https://you.com/search?q=best+{category.replace(' ', '+')}+tools",
    }

    results: dict[str, dict] = {}

    try:
        async with AsyncWebCrawler() as crawler:
            for platform, url in platforms.items():
                try:
                    crawl_result = await crawler.arun(url=url)
                    content = _extract_markdown(crawl_result)
                    content_lower = content.lower()
                    brand_lower = brand_name.lower()

                    mentioned = brand_lower in content_lower
                    mention_count = content_lower.count(brand_lower)

                    # Rough position detection: first mention location as percentage
                    position = -1
                    if mentioned and content_lower:
                        first_idx = content_lower.index(brand_lower)
                        position = first_idx / len(content_lower) * 100

                    results[platform] = {
                        "mentioned": mentioned,
                        "mention_count": mention_count,
                        "position_pct": round(position, 1) if position >= 0 else None,
                        "content_snippet": content[:2000],
                    }
                except Exception as e:
                    results[platform] = {
                        "mentioned": False,
                        "mention_count": 0,
                        "position_pct": None,
                        "error": str(e),
                    }
    except Exception as e:
        return f"Failed to scan: {e}"

    # Compute GEO Score
    # Visibility (0-40): mentioned on how many platforms
    platforms_mentioned = sum(1 for r in results.values() if r["mentioned"])
    visibility_score = int(platforms_mentioned / len(platforms) * 40)

    # Position (0-30): earlier mentions = higher score
    position_scores = []
    for r in results.values():
        if r.get("position_pct") is not None:
            # 0% position = score 30, 100% = score 0
            position_scores.append(30 * (1 - r["position_pct"] / 100))
    position_score = int(sum(position_scores) / len(position_scores)) if position_scores else 0

    # Sentiment (0-30): placeholder — needs NLP in future versions
    # For now, give 15/30 if mentioned (neutral), 0 if not
    sentiment_score = 15 if platforms_mentioned > 0 else 0

    geo_score = visibility_score + position_score + sentiment_score

    # Build report
    lines = [
        f"# GEO Visibility Report: {brand_name}",
        f"**Category**: {category}\n",
        f"## GEO Score: {geo_score}/100\n",
        f"| Component | Score | Max |",
        f"|-----------|-------|-----|",
        f"| Visibility | {visibility_score} | 40 |",
        f"| Position | {position_score} | 30 |",
        f"| Sentiment | {sentiment_score} | 30 |",
        f"| **Total** | **{geo_score}** | **100** |",
        "",
        "## Platform Results\n",
    ]

    for platform, data in results.items():
        if data.get("error"):
            lines.append(f"### {platform}: ERROR — {data['error']}\n")
            continue
        status = "FOUND" if data["mentioned"] else "NOT FOUND"
        lines.append(f"### {platform}: {status}")
        if data["mentioned"]:
            lines.append(f"- Mentions: {data['mention_count']}")
            if data["position_pct"] is not None:
                lines.append(f"- First mention at: {data['position_pct']}% through the response")
        lines.append("")

    lines.extend([
        "## Raw Context (for agent analysis)\n",
        "Below are content snippets from each platform for the agent to analyze sentiment and context:\n",
    ])
    for platform, data in results.items():
        snippet = data.get("content_snippet", "")
        if snippet:
            lines.append(f"### {platform} snippet\n{snippet[:1500]}\n")

    lines.append("\n*Note: Sentiment scoring is approximate in v1. GEO tracking over time will be added in a future version.*")

    return "\n".join(lines)
