import json
from urllib.parse import quote_plus

from agents import function_tool
from crawl4ai import AsyncWebCrawler

from opencmo.tools.crawl import _extract_markdown


@function_tool
async def scan_community(brand_name: str, category: str) -> str:
    """Scan Reddit and Hacker News for brand/category discussions.

    Uses HN Algolia API (free, no key needed) and crawls Reddit search results.
    Returns structured list of relevant discussions with titles, links, and scores.

    Args:
        brand_name: The brand or product name to search for.
        category: The product category for broader search context.
    """
    results: dict[str, list[dict]] = {"hackernews": [], "reddit": []}

    async with AsyncWebCrawler() as crawler:
        # --- Hacker News via Algolia API ---
        hn_url = f"https://hn.algolia.com/api/v1/search?query={quote_plus(brand_name)}&tags=story&hitsPerPage=10"
        try:
            hn_result = await crawler.arun(url=hn_url)
            hn_content = _extract_markdown(hn_result)
            # Try to parse JSON from the response
            try:
                hn_data = json.loads(hn_content.strip())
                for hit in hn_data.get("hits", [])[:10]:
                    results["hackernews"].append({
                        "title": hit.get("title", ""),
                        "url": f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}",
                        "points": hit.get("points", 0),
                        "comments": hit.get("num_comments", 0),
                        "date": hit.get("created_at", ""),
                        "author": hit.get("author", ""),
                    })
            except (json.JSONDecodeError, TypeError):
                # Fallback: return raw content for agent analysis
                results["hackernews"] = [{"raw_content": hn_content[:3000]}]
        except Exception as e:
            results["hackernews"] = [{"error": str(e)}]

        # Also search by category for broader context
        hn_cat_url = f"https://hn.algolia.com/api/v1/search?query={quote_plus(category)}&tags=story&hitsPerPage=5"
        try:
            hn_cat_result = await crawler.arun(url=hn_cat_url)
            hn_cat_content = _extract_markdown(hn_cat_result)
            try:
                hn_cat_data = json.loads(hn_cat_content.strip())
                for hit in hn_cat_data.get("hits", [])[:5]:
                    results["hackernews"].append({
                        "title": hit.get("title", ""),
                        "url": f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}",
                        "points": hit.get("points", 0),
                        "comments": hit.get("num_comments", 0),
                        "date": hit.get("created_at", ""),
                        "author": hit.get("author", ""),
                        "source": "category_search",
                    })
            except (json.JSONDecodeError, TypeError):
                pass
        except Exception:
            pass

        # --- Reddit via crawl ---
        reddit_url = f"https://www.reddit.com/search/?q={quote_plus(brand_name)}&sort=relevance&t=year"
        try:
            reddit_result = await crawler.arun(url=reddit_url)
            reddit_content = _extract_markdown(reddit_result)
            # Reddit search results are HTML, the agent will need to analyze the markdown
            results["reddit"] = [{"raw_content": reddit_content[:5000]}]
        except Exception as e:
            results["reddit"] = [{"error": str(e)}]

    # Build report
    lines = [
        f"# Community Scan: {brand_name}",
        f"**Category**: {category}\n",
        "## Hacker News Discussions\n",
    ]

    hn_items = results["hackernews"]
    if hn_items and "error" in hn_items[0]:
        lines.append(f"Error: {hn_items[0]['error']}\n")
    elif hn_items and "raw_content" in hn_items[0]:
        lines.append("Could not parse structured data. Raw content:\n")
        lines.append(hn_items[0]["raw_content"][:2000])
    else:
        for item in hn_items:
            points = item.get("points", 0)
            comments = item.get("comments", 0)
            lines.append(
                f"- **{item['title']}** — {points} points, {comments} comments"
            )
            lines.append(f"  {item['url']}")
            if item.get("date"):
                lines.append(f"  Date: {item['date']}")
            lines.append("")

    lines.append("\n## Reddit Discussions\n")
    reddit_items = results["reddit"]
    if reddit_items and "error" in reddit_items[0]:
        lines.append(f"Error: {reddit_items[0]['error']}\n")
    else:
        lines.append("Raw search results (for agent analysis):\n")
        for item in reddit_items:
            lines.append(item.get("raw_content", "No content found")[:3000])

    lines.append(
        "\n---\n*The community agent will analyze these results, identify high-value discussions, "
        "and draft suggested replies. Replies are never auto-posted.*"
    )

    return "\n".join(lines)
