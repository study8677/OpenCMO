"""Blog research tool — gathers competing content data for full article generation."""

from __future__ import annotations

import json
import logging

from agents import function_tool

logger = logging.getLogger(__name__)


async def _research_topic_impl(topic: str, keywords: str) -> str:
    """Research a topic by searching and crawling competing articles.

    Uses httpx + crawl4ai directly (not function_tools) to avoid circular deps.
    Returns JSON with competing_articles and data_points.
    """
    import httpx
    from urllib.parse import quote_plus

    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    query = f"{topic} {keyword_list[0]}" if keyword_list else topic

    competing_articles = []
    data_points = []

    # Step 1: Search for competing content
    search_urls = []
    try:
        search_url = f"https://www.google.com/search?q={quote_plus(query)}&num=10"
        async with httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
            follow_redirects=True,
            timeout=15,
        ) as client:
            resp = await client.get(search_url)
            resp.raise_for_status()

        import re

        for m in re.finditer(r'href="/url\?q=(https?://[^&"]+)', resp.text):
            url = m.group(1)
            if "google.com" not in url:
                search_urls.append(url)
        for m in re.finditer(r'<a href="(https?://[^"]+)"[^>]*data-', resp.text):
            url = m.group(1)
            if "google.com" not in url and url not in search_urls:
                search_urls.append(url)
    except Exception as exc:
        logger.warning("Search failed: %s", exc)

    # Step 2: Crawl top 2 articles for content
    crawl_urls = search_urls[:5]  # try up to 5, take first 2 that succeed
    crawled = 0
    for url in crawl_urls:
        if crawled >= 2:
            break
        try:
            from crawl4ai import AsyncWebCrawler

            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)
            md = getattr(result, "markdown", None)
            if md and hasattr(md, "raw_markdown"):
                text = md.raw_markdown
            elif isinstance(md, str):
                text = md
            else:
                text = str(md) if md else ""

            # Extract key points (first ~1000 chars)
            text = text[:3000] if text else ""

            # Try to extract title from content
            title = ""
            for line in text.split("\n"):
                line = line.strip()
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
                if line and len(line) > 10 and not line.startswith("["):
                    title = line[:100]
                    break

            key_points = []
            for line in text.split("\n"):
                line = line.strip()
                if line.startswith("## ") and len(line) > 5:
                    key_points.append(line[3:].strip())
                if len(key_points) >= 5:
                    break

            competing_articles.append({
                "title": title or url,
                "url": url,
                "key_points": key_points,
                "excerpt": text[:500],
            })
            crawled += 1
        except Exception as exc:
            logger.debug("Crawl failed for %s: %s", url, exc)

    # Step 3: Extract data points from found content
    for article in competing_articles:
        import re

        # Look for numbers, statistics, percentages
        for pattern in [
            r'\d+%\s+[a-zA-Z]+',
            r'\$[\d,.]+\s+\w+',
            r'\d+x\s+\w+',
        ]:
            for m in re.finditer(pattern, article.get("excerpt", "")):
                data_points.append(m.group(0))

    return json.dumps({
        "topic": topic,
        "keywords": keyword_list,
        "competing_articles": competing_articles,
        "data_points": list(set(data_points))[:10],
        "search_urls_found": len(search_urls),
    }, ensure_ascii=False)


@function_tool
async def research_blog_topic(topic: str, keywords: str) -> str:
    """Research a topic by analyzing competing articles and gathering data points.

    Args:
        topic: The article topic to research.
        keywords: Comma-separated target keywords for the article.
    """
    return await _research_topic_impl(topic, keywords)
