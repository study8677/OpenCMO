from html.parser import HTMLParser

from agents import function_tool
from crawl4ai import AsyncWebCrawler

from opencmo.tools.crawl import _extract_markdown


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

        if tag in self.headings:
            self.headings[tag].append("")  # placeholder for text

    def handle_data(self, data: str):
        if self._capture_title:
            self.title += data.strip()
        if self._tag_stack and self._tag_stack[-1] in self.headings:
            tag = self._tag_stack[-1]
            if self.headings[tag]:
                self.headings[tag][-1] += data.strip()

    def handle_endtag(self, tag: str):
        if tag == "title":
            self._capture_title = False
        if self._tag_stack and self._tag_stack[-1] == tag:
            self._tag_stack.pop()


def _check(label: str, ok: bool, detail: str) -> str:
    tag = "[OK]" if ok else "[CRITICAL]"
    return f"{tag} {label}: {detail}"


def _warn(label: str, detail: str) -> str:
    return f"[WARNING] {label}: {detail}"


def _build_report(parser: _SEOParser, result, url: str) -> str:
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

    return "\n".join(lines)


@function_tool
async def audit_page_seo(url: str) -> str:
    """Audit a single web page for SEO issues.

    Checks title, meta description, OG tags, canonical URL, viewport, headings,
    image alt text, links, and content length. Each item is marked as
    [OK], [WARNING], or [CRITICAL].

    Args:
        url: The URL of the page to audit.
    """
    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)

        parser = _SEOParser()
        html = getattr(result, "html", "") or ""
        parser.feed(html)

        return _build_report(parser, result, url)
    except Exception as e:
        return f"Failed to audit {url}: {e}"
