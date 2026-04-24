"""Multi-page site audit — content depth, internal link topology, meta duplicates, CTA detection.

Crawls pages from sitemap.xml (or homepage links as fallback) and performs
cross-page analysis that single-page audits cannot do.
"""

from __future__ import annotations

import asyncio
import logging
import re
from collections import defaultdict
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx
from agents import function_tool

from opencmo.tools.browser_pool import browser_slot
from opencmo.tools.crawl import _extract_markdown

logger = logging.getLogger(__name__)

_MAX_PAGES = 30  # cap to avoid excessive crawl time
_CONTENT_DEPTH_THRESHOLD = 800  # words — per the growth checklist standard


# ---------------------------------------------------------------------------
# Lightweight HTML parser for per-page signals
# ---------------------------------------------------------------------------

class _PageMeta(HTMLParser):
    """Extract meta title, description, H1, and internal links from HTML."""

    def __init__(self, base_url: str):
        super().__init__()
        self._base = base_url
        self._origin = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
        self.title = ""
        self.meta_description = ""
        self.h1s: list[str] = []
        self.internal_links: list[str] = []
        self.external_links: list[str] = []
        self._capture_title = False
        self._capture_h1 = False
        self._tag_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        attr_dict = {k: (v or "") for k, v in attrs}
        self._tag_stack.append(tag)

        if tag == "title":
            self._capture_title = True
        if tag == "h1":
            self._capture_h1 = True
            self.h1s.append("")
        if tag == "meta":
            name = attr_dict.get("name", "").lower()
            if name == "description":
                self.meta_description = attr_dict.get("content", "")
        if tag == "a":
            href = attr_dict.get("href", "")
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                return
            resolved = urljoin(self._base, href).split("#")[0].split("?")[0]
            if resolved.startswith(self._origin):
                self.internal_links.append(resolved)
            elif resolved.startswith("http"):
                self.external_links.append(resolved)

    def handle_data(self, data: str):
        if self._capture_title:
            self.title += data.strip()
        if self._capture_h1 and self.h1s:
            self.h1s[-1] += data.strip()

    def handle_endtag(self, tag: str):
        if tag == "title":
            self._capture_title = False
        if tag == "h1":
            self._capture_h1 = False
        if self._tag_stack and self._tag_stack[-1] == tag:
            self._tag_stack.pop()


# ---------------------------------------------------------------------------
# Sitemap URL extraction
# ---------------------------------------------------------------------------

async def _get_sitemap_urls(base_url: str) -> list[str]:
    """Fetch sitemap.xml and extract page URLs."""
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    urls: list[str] = []

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(f"{origin}/sitemap.xml")
            if resp.status_code == 200 and "<urlset" in resp.text.lower():
                # Extract <loc> values
                for match in re.finditer(r"<loc>\s*(.*?)\s*</loc>", resp.text, re.IGNORECASE):
                    url = match.group(1).strip()
                    if url.startswith("http"):
                        urls.append(url)
    except Exception as exc:
        logger.debug("Sitemap fetch failed: %s", exc)

    return urls


async def _get_homepage_links(base_url: str) -> list[str]:
    """Fallback: crawl homepage and extract internal links."""
    try:
        from crawl4ai import AsyncWebCrawler

        async with browser_slot():
            async with AsyncWebCrawler() as crawler:
                result = await asyncio.wait_for(crawler.arun(url=base_url), timeout=60)
        html = getattr(result, "html", "") or ""
        parser = _PageMeta(base_url)
        parser.feed(html)
        return list(set(parser.internal_links))
    except Exception as exc:
        logger.debug("Homepage link extraction failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Per-page crawl
# ---------------------------------------------------------------------------

async def _crawl_page(url: str) -> dict | None:
    """Crawl a single page and extract signals."""
    try:
        from crawl4ai import AsyncWebCrawler

        async with browser_slot():
            async with AsyncWebCrawler() as crawler:
                result = await asyncio.wait_for(crawler.arun(url=url), timeout=60)

        html = getattr(result, "html", "") or ""
        parser = _PageMeta(url)
        parser.feed(html)

        content = _extract_markdown(result)
        word_count = len(content.split())

        return {
            "url": url,
            "title": parser.title,
            "meta_description": parser.meta_description,
            "h1s": parser.h1s,
            "word_count": word_count,
            "internal_links": list(set(parser.internal_links)),
            "external_links": list(set(parser.external_links)),
        }
    except Exception as exc:
        logger.debug("Failed to crawl %s: %s", url, exc)
        return None


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------

def _analyze_content_depth(pages: list[dict]) -> dict:
    """Check word counts against the 800-word threshold."""
    thin_pages = [p for p in pages if p["word_count"] < _CONTENT_DEPTH_THRESHOLD]
    adequate_pages = [p for p in pages if p["word_count"] >= _CONTENT_DEPTH_THRESHOLD]
    return {
        "total_pages": len(pages),
        "adequate_count": len(adequate_pages),
        "thin_count": len(thin_pages),
        "thin_pages": [
            {"url": p["url"], "title": p["title"], "word_count": p["word_count"]}
            for p in sorted(thin_pages, key=lambda x: x["word_count"])
        ],
        "avg_word_count": round(sum(p["word_count"] for p in pages) / len(pages)) if pages else 0,
    }


def _analyze_meta_duplicates(pages: list[dict]) -> dict:
    """Find duplicate meta titles and descriptions across pages."""
    title_map: dict[str, list[str]] = defaultdict(list)
    desc_map: dict[str, list[str]] = defaultdict(list)

    for p in pages:
        t = p["title"].strip()
        d = p["meta_description"].strip()
        if t:
            title_map[t].append(p["url"])
        if d:
            desc_map[d].append(p["url"])

    dup_titles = {k: v for k, v in title_map.items() if len(v) > 1}
    dup_descs = {k: v for k, v in desc_map.items() if len(v) > 1}
    missing_titles = [p["url"] for p in pages if not p["title"].strip()]
    missing_descs = [p["url"] for p in pages if not p["meta_description"].strip()]

    return {
        "duplicate_titles": dup_titles,
        "duplicate_descriptions": dup_descs,
        "missing_titles": missing_titles,
        "missing_descriptions": missing_descs,
    }


def _analyze_internal_links(pages: list[dict]) -> dict:
    """Build internal link graph and identify orphan / poorly-linked pages."""
    crawled_urls = {p["url"] for p in pages}
    # Normalize trailing slashes for matching
    normalized = {u.rstrip("/"): u for u in crawled_urls}

    # Build adjacency: who links to whom
    inbound: dict[str, set[str]] = defaultdict(set)  # target -> set of sources
    outbound: dict[str, set[str]] = defaultdict(set)  # source -> set of targets

    for p in pages:
        src = p["url"]
        for link in p["internal_links"]:
            # Match against crawled pages
            target = normalized.get(link.rstrip("/"))
            if target and target != src:
                outbound[src].add(target)
                inbound[target].add(src)

    orphan_pages = [u for u in crawled_urls if len(inbound.get(u, set())) == 0]
    low_inbound = [
        {"url": u, "inbound_count": len(inbound.get(u, set()))}
        for u in crawled_urls
        if 0 < len(inbound.get(u, set())) <= 1
    ]

    # Find pairs of important pages that don't link to each other
    missing_cross_links = []
    important = [p for p in pages if p["word_count"] >= _CONTENT_DEPTH_THRESHOLD]
    for i, a in enumerate(important):
        for b in important[i + 1:]:
            a_to_b = b["url"] in outbound.get(a["url"], set())
            b_to_a = a["url"] in outbound.get(b["url"], set())
            if not a_to_b and not b_to_a:
                missing_cross_links.append((a["url"], b["url"]))

    return {
        "total_crawled": len(crawled_urls),
        "orphan_pages": orphan_pages,
        "low_inbound_pages": low_inbound,
        "missing_cross_links": missing_cross_links[:10],  # cap output
        "avg_inbound": round(sum(len(v) for v in inbound.values()) / len(crawled_urls), 1) if crawled_urls else 0,
        "avg_outbound": round(sum(len(v) for v in outbound.values()) / len(crawled_urls), 1) if crawled_urls else 0,
    }


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def _format_site_audit(
    content_depth: dict,
    meta_dups: dict,
    link_topology: dict,
) -> str:
    """Format multi-page audit results as markdown."""
    lines = ["# Multi-Page Site Audit\n"]

    # ── Content Depth ─────────────────────────────────────────────
    lines.append("## Content Depth Analysis\n")
    cd = content_depth
    lines.append(f"**{cd['adequate_count']}/{cd['total_pages']}** pages meet the {_CONTENT_DEPTH_THRESHOLD}-word depth threshold. "
                 f"Average word count: **{cd['avg_word_count']}** words.\n")

    if cd["thin_pages"]:
        lines.append("### Thin pages (< 800 words)\n")
        lines.append("| URL | Title | Words |")
        lines.append("|-----|-------|-------|")
        for p in cd["thin_pages"][:15]:
            title = p["title"][:50] or "(no title)"
            lines.append(f"| {p['url']} | {title} | {p['word_count']} |")
    else:
        lines.append("All crawled pages have adequate content depth.")

    # ── Meta Duplicates ───────────────────────────────────────────
    lines.append("\n## Meta Title & Description Audit\n")
    md = meta_dups
    if md["duplicate_titles"]:
        lines.append(f"### Duplicate Titles ({len(md['duplicate_titles'])} groups)\n")
        for title, urls in list(md["duplicate_titles"].items())[:5]:
            lines.append(f"**\"{title[:60]}\"** — used on {len(urls)} pages:")
            for u in urls[:3]:
                lines.append(f"  - {u}")
    else:
        lines.append("No duplicate titles found.")

    if md["duplicate_descriptions"]:
        lines.append(f"\n### Duplicate Descriptions ({len(md['duplicate_descriptions'])} groups)\n")
        for desc, urls in list(md["duplicate_descriptions"].items())[:5]:
            lines.append(f"**\"{desc[:60]}...\"** — used on {len(urls)} pages:")
            for u in urls[:3]:
                lines.append(f"  - {u}")

    if md["missing_titles"]:
        lines.append(f"\n**{len(md['missing_titles'])}** pages missing title tag:")
        for u in md["missing_titles"][:5]:
            lines.append(f"  - {u}")

    if md["missing_descriptions"]:
        lines.append(f"\n**{len(md['missing_descriptions'])}** pages missing meta description:")
        for u in md["missing_descriptions"][:5]:
            lines.append(f"  - {u}")

    # ── Internal Link Topology ────────────────────────────────────
    lines.append("\n## Internal Link Topology\n")
    lt = link_topology
    lines.append(f"Analyzed **{lt['total_crawled']}** pages. "
                 f"Avg inbound links: **{lt['avg_inbound']}**, avg outbound: **{lt['avg_outbound']}**.\n")

    if lt["orphan_pages"]:
        lines.append(f"### Orphan Pages ({len(lt['orphan_pages'])} — zero inbound links)\n")
        lines.append("These pages are not linked from any other page on the site:\n")
        for u in lt["orphan_pages"][:10]:
            lines.append(f"- {u}")
    else:
        lines.append("No orphan pages detected.")

    if lt["low_inbound_pages"]:
        lines.append(f"\n### Low-Authority Pages (only 1 inbound link)\n")
        for p in lt["low_inbound_pages"][:10]:
            lines.append(f"- {p['url']} ({p['inbound_count']} inbound)")

    if lt["missing_cross_links"]:
        lines.append(f"\n### Missing Cross-Links Between Core Pages\n")
        lines.append("These content-rich pages don't link to each other:\n")
        for a, b in lt["missing_cross_links"][:8]:
            lines.append(f"- {a} ↔ {b}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def _site_audit_impl(base_url: str) -> dict:
    """Run multi-page audit. Returns structured results."""
    # Get page URLs from sitemap, fallback to homepage links
    urls = await _get_sitemap_urls(base_url)
    if not urls:
        urls = await _get_homepage_links(base_url)
    if not urls:
        urls = [base_url]

    # Always include base URL
    base_normalized = base_url.rstrip("/")
    if not any(u.rstrip("/") == base_normalized for u in urls):
        urls.insert(0, base_url)

    # Cap pages
    urls = urls[:_MAX_PAGES]

    # Crawl pages with concurrency limit
    sem = asyncio.Semaphore(3)

    async def _limited_crawl(url: str):
        async with sem:
            return await _crawl_page(url)

    results = await asyncio.gather(*[_limited_crawl(u) for u in urls], return_exceptions=True)
    pages = [r for r in results if isinstance(r, dict)]

    if not pages:
        return {"error": "Could not crawl any pages"}

    content_depth = _analyze_content_depth(pages)
    meta_dups = _analyze_meta_duplicates(pages)
    link_topology = _analyze_internal_links(pages)

    return {
        "pages_crawled": len(pages),
        "content_depth": content_depth,
        "meta_duplicates": meta_dups,
        "link_topology": link_topology,
    }


@function_tool
async def audit_site_pages(url: str) -> str:
    """Multi-page site audit: crawl pages from sitemap.xml and analyze content depth (800-word threshold), meta title/description duplicates, and internal link topology (orphan pages, missing cross-links). Use this for a site-wide health check beyond single-page SEO.

    Args:
        url: The homepage or base URL of the site to audit.
    """
    data = await _site_audit_impl(url)
    if data.get("error"):
        return f"Site audit failed: {data['error']}"
    return _format_site_audit(
        data["content_depth"],
        data["meta_duplicates"],
        data["link_topology"],
    )
