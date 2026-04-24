"""Content publishing frequency tracker.

Detects blog/changelog pages from sitemap or common paths, extracts
publication dates, and computes posting frequency.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

import httpx
from agents import function_tool

logger = logging.getLogger(__name__)

# Common blog/content URL patterns
_BLOG_PATTERNS = re.compile(
    r"/(blog|articles?|posts?|news|changelog|updates?|resources?|learn|guides?|insights?)(/|$)",
    re.IGNORECASE,
)

# Date extraction patterns from URLs (e.g., /2024/03/15/ or /2024-03-15)
_URL_DATE_PATTERN = re.compile(r"/(\d{4})[/-](\d{2})(?:[/-](\d{2}))?")

# Sitemap <lastmod> date pattern
_LASTMOD_PATTERN = re.compile(
    r"<url>\s*<loc>\s*(.*?)\s*</loc>\s*(?:.*?<lastmod>\s*([\d\-T:+Z]+)\s*</lastmod>)?",
    re.DOTALL | re.IGNORECASE,
)


async def _get_sitemap_entries(base_url: str) -> list[dict]:
    """Extract URLs and lastmod dates from sitemap.xml."""
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    entries: list[dict] = []

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(f"{origin}/sitemap.xml")
            if resp.status_code != 200:
                return entries

            text = resp.text

            # Handle sitemap index — fetch first child sitemap
            if "<sitemapindex" in text.lower():
                child_locs = re.findall(r"<loc>\s*(.*?)\s*</loc>", text, re.IGNORECASE)
                for child_url in child_locs[:3]:
                    try:
                        child_resp = await client.get(child_url.strip())
                        if child_resp.status_code == 200:
                            text = child_resp.text
                            break
                    except Exception:
                        continue

            for match in _LASTMOD_PATTERN.finditer(text):
                url = match.group(1).strip()
                lastmod = match.group(2)
                date = None
                if lastmod:
                    try:
                        date = datetime.fromisoformat(lastmod.replace("Z", "+00:00")).date().isoformat()
                    except ValueError:
                        pass
                entries.append({"url": url, "lastmod": date})

    except Exception as exc:
        logger.debug("Sitemap fetch failed: %s", exc)

    return entries


def _extract_date_from_url(url: str) -> str | None:
    """Try to extract a publication date from the URL path."""
    match = _URL_DATE_PATTERN.search(url)
    if match:
        year, month = int(match.group(1)), int(match.group(2))
        day = int(match.group(3)) if match.group(3) else 1
        if 2010 <= year <= 2030 and 1 <= month <= 12:
            try:
                return datetime(year, month, day).date().isoformat()
            except ValueError:
                pass
    return None


def _is_content_url(url: str) -> bool:
    """Check if URL looks like a blog/content page."""
    return bool(_BLOG_PATTERNS.search(url))


async def _analyze_content_frequency(base_url: str) -> dict:
    """Analyze content publishing frequency from sitemap data."""
    entries = await _get_sitemap_entries(base_url)

    # Filter to content/blog URLs
    content_entries = []
    for entry in entries:
        url = entry["url"]
        if not _is_content_url(url):
            continue

        date = entry.get("lastmod") or _extract_date_from_url(url)
        if date:
            content_entries.append({"url": url, "date": date})

    if not content_entries:
        # Fallback: check common blog paths
        parsed = urlparse(base_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        blog_candidates = ["/blog", "/articles", "/posts", "/news", "/changelog"]

        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                for path in blog_candidates:
                    try:
                        resp = await client.head(urljoin(origin, path))
                        if resp.status_code == 200:
                            return {
                                "has_blog": True,
                                "blog_url": urljoin(origin, path),
                                "content_pages": 0,
                                "dated_pages": 0,
                                "frequency_label": "unknown",
                                "posts_per_month": None,
                                "recent_posts": [],
                                "note": "Blog section detected but no dated content found in sitemap. Add lastmod to sitemap entries for tracking.",
                            }
                    except Exception:
                        continue
        except Exception:
            pass

        return {
            "has_blog": False,
            "blog_url": None,
            "content_pages": 0,
            "dated_pages": 0,
            "frequency_label": "none",
            "posts_per_month": 0,
            "recent_posts": [],
        }

    # Sort by date descending
    content_entries.sort(key=lambda x: x["date"], reverse=True)

    # Calculate frequency over last 6 months
    six_months_ago = (datetime.now() - timedelta(days=180)).date().isoformat()
    recent = [e for e in content_entries if e["date"] >= six_months_ago]
    posts_per_month = round(len(recent) / 6, 1) if recent else 0

    if posts_per_month >= 4:
        freq_label = "excellent"
    elif posts_per_month >= 2:
        freq_label = "good"
    elif posts_per_month >= 0.5:
        freq_label = "low"
    else:
        freq_label = "very_low"

    return {
        "has_blog": True,
        "blog_url": content_entries[0]["url"].rsplit("/", 2)[0] + "/" if content_entries else None,
        "content_pages": len(content_entries),
        "dated_pages": len(content_entries),
        "frequency_label": freq_label,
        "posts_per_month": posts_per_month,
        "recent_posts": content_entries[:10],
    }


def _format_frequency_report(data: dict) -> str:
    """Format content frequency analysis as markdown."""
    lines = ["# Content Publishing Frequency\n"]

    if not data["has_blog"]:
        lines.append("**No blog or content section detected.**\n")
        lines.append("A regularly updated blog is essential for SEO growth. Without one, "
                     "you're missing opportunities to rank for problem, tool, and comparison keywords.\n")
        lines.append("**Recommendation:** Create a blog or content hub and publish at least 2 posts per month.")
        return "\n".join(lines)

    freq = data["frequency_label"]
    ppm = data["posts_per_month"]
    total = data["content_pages"]

    freq_display = {
        "excellent": "Excellent (4+ posts/month)",
        "good": "Good (2+ posts/month)",
        "low": "Low (< 2 posts/month)",
        "very_low": "Very low (< 1 post/month)",
        "unknown": "Unknown (no dated content in sitemap)",
        "none": "None detected",
    }

    lines.append(f"**Publishing frequency: {freq_display.get(freq, freq)}**")
    if ppm is not None:
        lines.append(f"**Posts per month (6-month avg): {ppm}**")
    lines.append(f"**Total content pages found: {total}**\n")

    if freq in ("low", "very_low"):
        lines.append("⚠️ Publishing frequency is below the recommended minimum of 2 posts/month. "
                     "Consistent content production is a key SEO growth lever.\n")

    recent = data.get("recent_posts", [])
    if recent:
        lines.append("### Recent Content\n")
        lines.append("| Date | URL |")
        lines.append("|------|-----|")
        for post in recent[:10]:
            lines.append(f"| {post['date']} | {post['url']} |")

    if data.get("note"):
        lines.append(f"\n> **Note:** {data['note']}")

    return "\n".join(lines)


@function_tool
async def check_content_frequency(url: str) -> str:
    """Analyze content publishing frequency from sitemap data. Detects blog/content pages, extracts publication dates, and calculates posting frequency. Flags sites publishing fewer than 2 posts per month.

    Args:
        url: The website URL to analyze.
    """
    data = await _analyze_content_frequency(url)
    return _format_frequency_report(data)
