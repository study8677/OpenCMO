from __future__ import annotations

import asyncio
import json
import logging
from html.parser import HTMLParser
from urllib.parse import urlparse

import httpx
from agents import function_tool
from crawl4ai import AsyncWebCrawler

from opencmo.tools.crawl import _extract_markdown

logger = logging.getLogger(__name__)


class _SEOParser(HTMLParser):
    """Extract SEO-relevant elements from HTML."""

    def __init__(self):
        super().__init__()
        self._tag_stack: list[str] = []
        self.title = ""
        self.meta_description = ""
        self.og_tags: dict[str, str] = {}
        self.canonical = ""
        self.viewport = ""
        self.headings: dict[str, list[str]] = {f"h{i}": [] for i in range(1, 7)}
        self._capture_title = False
        # JSON-LD / Schema.org tracking
        self.schema_types: list[str] = []
        self._capture_jsonld = False
        self._jsonld_buffer = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        attr_dict = {k: v or "" for k, v in attrs}
        self._tag_stack.append(tag)

        if tag == "meta":
            name = attr_dict.get("name", "").lower()
            prop = attr_dict.get("property", "").lower()
            content = attr_dict.get("content", "")
            if name == "description":
                self.meta_description = content
            if name == "viewport":
                self.viewport = content
            if prop.startswith("og:"):
                self.og_tags[prop] = content

        if tag == "link":
            if attr_dict.get("rel", "").lower() == "canonical":
                self.canonical = attr_dict.get("href", "")

        if tag == "title":
            self._capture_title = True

        if tag == "script":
            if attr_dict.get("type", "").lower() == "application/ld+json":
                self._capture_jsonld = True
                self._jsonld_buffer = ""

        if tag in self.headings:
            self.headings[tag].append("")  # placeholder for text

    def handle_data(self, data: str):
        if self._capture_title:
            self.title += data.strip()
        if self._capture_jsonld:
            self._jsonld_buffer += data
        if self._tag_stack and self._tag_stack[-1] in self.headings:
            tag = self._tag_stack[-1]
            if self.headings[tag]:
                self.headings[tag][-1] += data.strip()

    def handle_endtag(self, tag: str):
        if tag == "title":
            self._capture_title = False
        if tag == "script" and self._capture_jsonld:
            self._capture_jsonld = False
            self._parse_jsonld(self._jsonld_buffer)
            self._jsonld_buffer = ""
        if self._tag_stack and self._tag_stack[-1] == tag:
            self._tag_stack.pop()

    def _parse_jsonld(self, raw: str) -> None:
        """Extract @type from a JSON-LD blob."""
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "@type" in item:
                    self.schema_types.append(item["@type"])
        elif isinstance(data, dict):
            if "@type" in data:
                self.schema_types.append(data["@type"])
            # Also check @graph
            graph = data.get("@graph", [])
            if isinstance(graph, list):
                for item in graph:
                    if isinstance(item, dict) and "@type" in item:
                        self.schema_types.append(item["@type"])


def _check(label: str, ok: bool, detail: str) -> str:
    tag = "[OK]" if ok else "[CRITICAL]"
    return f"{tag} {label}: {detail}"


def _warn(label: str, detail: str) -> str:
    return f"[WARNING] {label}: {detail}"


def _flatten_schema_types(values: list) -> list[str]:
    flattened: list[str] = []
    for value in values:
        if isinstance(value, str):
            flattened.append(value)
        elif isinstance(value, list):
            flattened.extend(_flatten_schema_types(value))
    return flattened


def _cwv_status(value: float, good: float, poor: float) -> str:
    """Return severity tag for a Core Web Vitals metric."""
    if value < good:
        return "[OK]"
    elif value >= poor:
        return "[CRITICAL]"
    else:
        return "[WARNING]"


def _compute_seo_health_score(
    parser: "_SEOParser",
    *,
    cwv: dict | None = None,
    robots_sitemap: dict | None = None,
) -> float:
    """Compute a holistic SEO health score in [0, 100].

    Three dimensions, each scored independently:

    1. Technical Foundation — 40 pts
       robots.txt present & not blocking (10) + sitemap.xml (10)
       + Schema.org markup (10) + canonical URL (10)

    2. On-Page Quality — 30 pts
       title quality (10) + meta description quality (10)
       + single H1 (5) + OG tag coverage (5)

    3. Page Performance — 30 pts
       PageSpeed Performance score × 30.
       When PageSpeed is unavailable (no API key / timeout), award a
       *neutral* 15 pts so the absence of the key doesn't crater the score.
    """
    score = 0.0

    # ── Technical Foundation (40 pts) ──────────────────────────────────────
    if robots_sitemap:
        has_robots = robots_sitemap.get("has_robots", False)
        disallow_all = robots_sitemap.get("robots_disallow_all", False)
        if has_robots and not disallow_all:
            score += 10
        elif has_robots:  # exists but blocks all crawlers — half credit
            score += 5
        if robots_sitemap.get("has_sitemap", False):
            score += 10

    if parser.schema_types:
        score += 10

    if parser.canonical:
        score += 10

    # ── On-Page Quality (30 pts) ────────────────────────────────────────────
    title_len = len(parser.title)
    if 30 <= title_len <= 60:
        score += 10   # ideal length
    elif parser.title:
        score += 5    # present but not ideal

    desc_len = len(parser.meta_description)
    if 70 <= desc_len <= 155:
        score += 10   # ideal length
    elif parser.meta_description:
        score += 5    # present but not ideal

    h1_count = len(parser.headings.get("h1", []))
    if h1_count == 1:
        score += 5    # exactly one H1
    elif h1_count > 1:
        score += 2    # multiple H1s is suboptimal

    og_present = sum(
        1 for tag in ["og:title", "og:description", "og:image"]
        if parser.og_tags.get(tag)
    )
    score += min(5.0, round(og_present / 3 * 5, 1))  # 0-5 proportional

    # ── Page Performance (30 pts) ───────────────────────────────────────────
    if cwv and cwv.get("performance") is not None:
        perf = float(cwv["performance"])  # 0.0 – 1.0
        score += perf * 30
    else:
        # PageSpeed unavailable — award neutral 15 pts (don't penalise absence
        # of API key on otherwise healthy sites like modern SPAs).
        score += 15

    return round(min(100.0, max(0.0, score)), 1)


async def _fetch_core_web_vitals(url: str) -> dict | None:
    """Fetch Core Web Vitals from Google PageSpeed Insights API.

    Returns dict with keys: performance, lcp, cls, tbt; or None on failure.
    """
    from opencmo import llm
    api_key = llm.get_key("PAGESPEED_API_KEY", "")
    params: dict[str, str] = {
        "url": url,
        "category": "performance",
        "strategy": "mobile",
    }
    if api_key:
        params["key"] = api_key

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        lighthouse = data.get("lighthouseResult", {})
        perf_score = lighthouse.get("categories", {}).get("performance", {}).get("score")
        audits = lighthouse.get("audits", {})
        lcp = audits.get("largest-contentful-paint", {}).get("numericValue")
        cls_ = audits.get("cumulative-layout-shift", {}).get("numericValue")
        tbt = audits.get("total-blocking-time", {}).get("numericValue")

        return {
            "performance": perf_score,
            "lcp": lcp,
            "cls": cls_,
            "tbt": tbt,
        }
    except Exception as exc:
        logger.debug("PageSpeed API failed for %s: %s", url, exc)
        return None


async def _check_robots_and_sitemap(url: str) -> dict:
    """Check robots.txt and sitemap.xml for the given URL's origin.

    Returns dict with keys: has_robots, robots_disallow_all, sitemap_in_robots,
    has_sitemap, sitemap_loc_count.
    """
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    result: dict = {
        "has_robots": False,
        "robots_disallow_all": False,
        "sitemap_in_robots": None,
        "has_sitemap": False,
        "sitemap_loc_count": 0,
    }

    def _looks_like_robots(body: str) -> bool:
        lowered = body.lower()
        if "<html" in lowered:
            return False
        return any(token in lowered for token in ("user-agent:", "disallow:", "allow:", "sitemap:"))

    def _looks_like_sitemap(body: str) -> bool:
        lowered = body.lower()
        if "<html" in lowered:
            return False
        return "<urlset" in lowered or "<sitemapindex" in lowered

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            # --- robots.txt ---
            try:
                robots_resp = await client.get(f"{origin}/robots.txt")
                if robots_resp.status_code == 200 and _looks_like_robots(robots_resp.text):
                    result["has_robots"] = True
                    body = robots_resp.text
                    for line in body.splitlines():
                        stripped = line.strip().lower()
                        if stripped.startswith("disallow") and "/ " not in stripped:
                            # Check for "Disallow: /" exactly (block everything)
                            parts = stripped.split(":", 1)
                            if len(parts) == 2 and parts[1].strip() == "/":
                                result["robots_disallow_all"] = True
                        if stripped.startswith("sitemap:"):
                            parts = line.strip().split(":", 1)
                            if len(parts) == 2:
                                result["sitemap_in_robots"] = parts[1].strip()
            except httpx.HTTPError:
                pass

            # --- sitemap.xml ---
            sitemap_url = result["sitemap_in_robots"] or f"{origin}/sitemap.xml"
            try:
                sitemap_resp = await client.get(sitemap_url)
                if sitemap_resp.status_code == 200 and _looks_like_sitemap(sitemap_resp.text):
                    result["has_sitemap"] = True
                    # Count <loc> entries
                    result["sitemap_loc_count"] = sitemap_resp.text.count("<loc>")
            except httpx.HTTPError:
                pass
    except Exception as exc:
        logger.debug("robots/sitemap check failed for %s: %s", origin, exc)

    return result


def _build_report(parser: _SEOParser, result, url: str, *, cwv: dict | None = None, robots_sitemap: dict | None = None) -> str:
    lines: list[str] = [f"# SEO Audit Report: {url}\n"]

    # Title
    t = parser.title
    if not t:
        lines.append(_check("Title", False, "Missing <title> tag"))
    elif len(t) < 30:
        lines.append(_warn("Title", f"Too short ({len(t)} chars): \"{t}\""))
    elif len(t) > 60:
        lines.append(_warn("Title", f"Too long ({len(t)} chars): \"{t}\""))
    else:
        lines.append(_check("Title", True, f"({len(t)} chars) \"{t}\""))

    # Meta description
    d = parser.meta_description
    if not d:
        lines.append(_check("Meta Description", False, "Missing meta description"))
    elif len(d) < 70:
        lines.append(_warn("Meta Description", f"Too short ({len(d)} chars)"))
    elif len(d) > 155:
        lines.append(_warn("Meta Description", f"Too long ({len(d)} chars)"))
    else:
        lines.append(_check("Meta Description", True, f"({len(d)} chars)"))

    # OG tags
    for tag in ["og:title", "og:description", "og:image"]:
        val = parser.og_tags.get(tag)
        if val:
            lines.append(_check(tag, True, f"\"{val[:80]}\""))
        else:
            lines.append(_check(tag, False, "Missing"))

    # Canonical
    if parser.canonical:
        lines.append(_check("Canonical URL", True, parser.canonical))
    else:
        lines.append(_warn("Canonical URL", "Not set"))

    # Viewport
    if parser.viewport:
        lines.append(_check("Viewport", True, parser.viewport))
    else:
        lines.append(_check("Viewport", False, "Missing — page may not be mobile-friendly"))

    # Headings
    h1_count = len(parser.headings["h1"])
    if h1_count == 0:
        lines.append(_check("H1", False, "No H1 tag found"))
    elif h1_count == 1:
        lines.append(_check("H1", True, f"\"{parser.headings['h1'][0][:80]}\""))
    else:
        lines.append(_warn("H1", f"Multiple H1 tags found ({h1_count})"))

    # Heading hierarchy
    prev_level = 0
    skip_found = False
    for i in range(1, 7):
        if parser.headings[f"h{i}"]:
            if prev_level and i > prev_level + 1:
                skip_found = True
                lines.append(_warn("Heading Hierarchy", f"Skipped from H{prev_level} to H{i}"))
            prev_level = i
    if not skip_found and prev_level:
        lines.append(_check("Heading Hierarchy", True, "No level skips detected"))

    # Images — use result.media if available
    media = getattr(result, "media", None)
    if media and isinstance(media, dict):
        images = media.get("images", [])
        if images:
            missing_alt = sum(1 for img in images if not img.get("alt"))
            total = len(images)
            if missing_alt:
                lines.append(_warn("Image Alt Text", f"{missing_alt}/{total} images missing alt text"))
            else:
                lines.append(_check("Image Alt Text", True, f"All {total} images have alt text"))
        else:
            lines.append(_check("Images", True, "No images found (or none detected)"))
    else:
        lines.append(_warn("Images", "Could not analyze images"))

    # Links — use result.links if available
    links = getattr(result, "links", None)
    if links and isinstance(links, dict):
        internal = len(links.get("internal", []))
        external = len(links.get("external", []))
        lines.append(_check("Links", True, f"{internal} internal, {external} external"))
    elif links and isinstance(links, list):
        lines.append(_check("Links", True, f"{len(links)} links found"))
    else:
        lines.append(_warn("Links", "Could not analyze links"))

    # Content word count
    content = _extract_markdown(result)
    word_count = len(content.split())
    if word_count < 300:
        lines.append(_warn("Content Length", f"{word_count} words — consider adding more content"))
    else:
        lines.append(_check("Content Length", True, f"{word_count} words"))

    # --- Schema.org / JSON-LD ---
    lines.append("")
    lines.append("## Structured Data (Schema.org)")
    if parser.schema_types:
        types_str = ", ".join(_flatten_schema_types(parser.schema_types))
        lines.append(_check("Schema.org", True, f"Found types: {types_str}"))
    else:
        lines.append(_warn("Schema.org", "No JSON-LD structured data found — add schema markup for rich results"))

    # --- Core Web Vitals ---
    lines.append("")
    lines.append("## Core Web Vitals (Mobile)")
    if cwv is not None:
        perf = cwv.get("performance")
        if perf is not None:
            perf_pct = int(perf * 100)
            tag = "[OK]" if perf_pct >= 90 else ("[CRITICAL]" if perf_pct < 50 else "[WARNING]")
            lines.append(f"{tag} Performance Score: {perf_pct}/100")
        else:
            lines.append(_warn("Performance Score", "Not available"))

        lcp = cwv.get("lcp")
        if lcp is not None:
            tag = _cwv_status(lcp, 2500, 4000)
            lines.append(f"{tag} LCP (Largest Contentful Paint): {lcp:.0f}ms")
        else:
            lines.append(_warn("LCP", "Not available"))

        cls_val = cwv.get("cls")
        if cls_val is not None:
            tag = _cwv_status(cls_val, 0.1, 0.25)
            lines.append(f"{tag} CLS (Cumulative Layout Shift): {cls_val:.3f}")
        else:
            lines.append(_warn("CLS", "Not available"))

        tbt = cwv.get("tbt")
        if tbt is not None:
            tag = _cwv_status(tbt, 200, 600)
            lines.append(f"{tag} TBT (Total Blocking Time): {tbt:.0f}ms")
        else:
            lines.append(_warn("TBT", "Not available"))
    else:
        lines.append(_warn("Core Web Vitals", "Could not fetch PageSpeed data — check network or set PAGESPEED_API_KEY"))

    # --- robots.txt & sitemap.xml ---
    lines.append("")
    lines.append("## Crawlability")
    if robots_sitemap is not None:
        if robots_sitemap["has_robots"]:
            lines.append(_check("robots.txt", True, "Found"))
            if robots_sitemap["robots_disallow_all"]:
                lines.append(_check("robots.txt Disallow", False, "Disallow: / blocks all crawlers"))
        else:
            lines.append(_warn("robots.txt", "Not found — search engines may crawl all pages without guidance"))

        if robots_sitemap["has_sitemap"]:
            count = robots_sitemap["sitemap_loc_count"]
            lines.append(_check("sitemap.xml", True, f"Found ({count} URLs)"))
        else:
            lines.append(_warn("sitemap.xml", "Not found — submit a sitemap to improve crawl efficiency"))

        if robots_sitemap["sitemap_in_robots"]:
            lines.append(_check("Sitemap in robots.txt", True, robots_sitemap["sitemap_in_robots"]))
        elif robots_sitemap["has_robots"]:
            lines.append(_warn("Sitemap in robots.txt", "No Sitemap directive in robots.txt"))
    else:
        lines.append(_warn("Crawlability", "Could not check robots.txt / sitemap.xml"))

    return "\n".join(lines)


@function_tool
async def audit_page_seo(url: str) -> str:
    """Audit a single web page for SEO issues.

    Checks title, meta description, OG tags, canonical URL, viewport, headings,
    image alt text, links, content length, Schema.org structured data,
    Core Web Vitals (via Google PageSpeed Insights), and robots.txt/sitemap.xml.
    Each item is marked as [OK], [WARNING], or [CRITICAL].

    Args:
        url: The URL of the page to audit.
    """
    try:
        async def _crawl():
            async with AsyncWebCrawler() as crawler:
                return await crawler.arun(url=url)

        result = await asyncio.wait_for(_crawl(), timeout=90)
        parser = _SEOParser()
        html = getattr(result, "html", "") or ""
        parser.feed(html)

        # Fetch external data (failures are non-blocking)
        cwv = await _fetch_core_web_vitals(url)
        robots_sitemap = await _check_robots_and_sitemap(url)

        report = _build_report(parser, result, url, cwv=cwv, robots_sitemap=robots_sitemap)

        # Compute multi-dimensional health score
        seo_health_score = _compute_seo_health_score(
            parser, cwv=cwv, robots_sitemap=robots_sitemap
        )

        # Persist to storage (best-effort)
        try:
            from opencmo import storage

            parsed = urlparse(url)
            domain = parsed.netloc.removeprefix("www.")
            project_id = await storage.ensure_project(domain, url, "")
            await storage.save_seo_scan(
                project_id,
                url,
                report,
                score_performance=cwv.get("performance") if cwv else None,
                score_lcp=cwv.get("lcp") if cwv else None,
                score_cls=cwv.get("cls") if cwv else None,
                score_tbt=cwv.get("tbt") if cwv else None,
                has_robots_txt=robots_sitemap.get("has_robots") if robots_sitemap else None,
                has_sitemap=robots_sitemap.get("has_sitemap") if robots_sitemap else None,
                has_schema_org=bool(parser.schema_types),
                seo_health_score=seo_health_score,
            )
        except Exception:
            pass  # Storage failure should not block the audit

        return report
    except Exception as e:
        return f"Failed to audit {url}: {e}"
