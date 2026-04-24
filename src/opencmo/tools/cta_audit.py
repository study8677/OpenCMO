"""Landing page CTA (Call-to-Action) audit.

Uses LLM analysis to evaluate CTA presence, prominence, and quality
on key landing pages. Checks for clear action-oriented CTAs, multiple
contact methods, and mobile-friendly form elements.
"""

from __future__ import annotations

import asyncio
import json
import logging
from html.parser import HTMLParser
from urllib.parse import urlparse

from agents import function_tool

from opencmo import llm
from opencmo.tools.browser_pool import browser_slot
from opencmo.tools.crawl import _extract_markdown

logger = logging.getLogger(__name__)


class _CTAParser(HTMLParser):
    """Extract CTA-relevant elements from HTML."""

    def __init__(self):
        super().__init__()
        self.buttons: list[str] = []
        self.forms: list[dict] = []
        self.links_with_cta: list[str] = []
        self.contact_methods: list[dict] = []
        self._current_form: dict | None = None
        self._capture: str | None = None
        self._capture_buf = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        attr_dict = {k: (v or "") for k, v in attrs}

        if tag == "button":
            self._capture = "button"
            self._capture_buf = ""

        if tag == "input":
            input_type = attr_dict.get("type", "").lower()
            if input_type == "submit":
                self.buttons.append(attr_dict.get("value", "Submit"))
            if input_type == "email":
                self.contact_methods.append({"type": "email_field", "context": "form"})
            if input_type == "tel":
                self.contact_methods.append({"type": "phone_field", "context": "form"})

        if tag == "form":
            self._current_form = {"action": attr_dict.get("action", ""), "method": attr_dict.get("method", "")}

        if tag == "a":
            href = attr_dict.get("href", "")
            if href.startswith("mailto:"):
                self.contact_methods.append({"type": "email", "value": href[7:].split("?")[0]})
            elif href.startswith("tel:"):
                self.contact_methods.append({"type": "phone", "value": href[4:]})
            elif any(chat in href.lower() for chat in ("whatsapp", "wa.me", "t.me", "intercom", "crisp", "drift", "calendly", "typeform")):
                self.contact_methods.append({"type": "chat/scheduling", "value": href[:80]})

        # Detect CTA-like links: links with action verbs in class/text
        if tag == "a":
            cls = attr_dict.get("class", "").lower()
            if any(kw in cls for kw in ("cta", "btn", "button", "primary", "action")):
                self._capture = "cta_link"
                self._capture_buf = ""

    def handle_data(self, data: str):
        if self._capture:
            self._capture_buf += data.strip()

    def handle_endtag(self, tag: str):
        if tag == "button" and self._capture == "button":
            if self._capture_buf:
                self.buttons.append(self._capture_buf)
            self._capture = None
        if tag == "a" and self._capture == "cta_link":
            if self._capture_buf:
                self.links_with_cta.append(self._capture_buf)
            self._capture = None
        if tag == "form" and self._current_form:
            self.forms.append(self._current_form)
            self._current_form = None


async def _audit_cta_impl(url: str) -> dict:
    """Audit a page for CTA elements and quality."""
    try:
        from crawl4ai import AsyncWebCrawler

        async with browser_slot():
            async with AsyncWebCrawler() as crawler:
                result = await asyncio.wait_for(crawler.arun(url=url), timeout=60)

        html = getattr(result, "html", "") or ""
        content = _extract_markdown(result)

        # Parse HTML for structural CTA signals
        parser = _CTAParser()
        parser.feed(html)

        structural = {
            "buttons": parser.buttons[:10],
            "forms": parser.forms[:5],
            "cta_links": parser.links_with_cta[:10],
            "contact_methods": parser.contact_methods[:10],
        }

        # Use LLM for qualitative CTA assessment
        assessment = await _llm_cta_assessment(url, content[:3000], structural)

        return {
            "url": url,
            "structural_signals": structural,
            "assessment": assessment,
        }
    except Exception as exc:
        logger.exception("CTA audit failed for %s", url)
        return {"url": url, "error": str(exc)}


async def _llm_cta_assessment(url: str, content: str, structural: dict) -> dict:
    """Use LLM to assess CTA quality."""
    system_prompt = (
        "You are a conversion optimization expert. Analyze a landing page for CTA effectiveness.\n"
        "Return ONLY valid JSON with this structure:\n"
        "{\n"
        '  "has_clear_primary_cta": true/false,\n'
        '  "primary_cta_text": "the main CTA button text or null",\n'
        '  "cta_prominence": "high|medium|low|none",\n'
        '  "cta_count": number of distinct CTAs,\n'
        '  "contact_accessibility": "good|fair|poor",\n'
        '  "issues": ["list of specific CTA problems"],\n'
        '  "recommendations": ["list of specific improvements"]\n'
        "}\n"
        "No markdown fences. Just the JSON object."
    )
    user_prompt = (
        f"URL: {url}\n\n"
        f"Page content (truncated):\n{content}\n\n"
        f"Structural signals found:\n"
        f"Buttons: {json.dumps(structural['buttons'])}\n"
        f"Forms: {len(structural['forms'])}\n"
        f"CTA-styled links: {json.dumps(structural['cta_links'])}\n"
        f"Contact methods: {json.dumps(structural['contact_methods'])}\n"
    )

    try:
        raw = await llm.chat(system_prompt, user_prompt)
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
        return json.loads(text)
    except Exception as exc:
        logger.debug("LLM CTA assessment failed: %s", exc)
        return {
            "has_clear_primary_cta": bool(structural["buttons"] or structural["cta_links"]),
            "primary_cta_text": (structural["buttons"] or [None])[0],
            "cta_prominence": "unknown",
            "cta_count": len(structural["buttons"]) + len(structural["cta_links"]),
            "contact_accessibility": "good" if len(structural["contact_methods"]) >= 2 else "poor",
            "issues": [],
            "recommendations": ["LLM assessment unavailable — manual review recommended"],
        }


def _format_cta_report(data: dict) -> str:
    """Format CTA audit as markdown."""
    if data.get("error"):
        return f"CTA audit failed for {data['url']}: {data['error']}"

    lines = [f"# CTA Audit: {data['url']}\n"]

    a = data["assessment"]
    s = data["structural_signals"]

    # Primary CTA
    if a.get("has_clear_primary_cta"):
        cta_text = a.get("primary_cta_text", "detected")
        lines.append(f"✅ **Primary CTA found**: \"{cta_text}\"")
    else:
        lines.append("❌ **No clear primary CTA detected** — visitors may not know what action to take.")

    # Prominence
    prom = a.get("cta_prominence", "unknown")
    prom_icon = {"high": "✅", "medium": "⚠️", "low": "❌", "none": "❌"}.get(prom, "❓")
    lines.append(f"{prom_icon} **CTA prominence**: {prom}")
    lines.append(f"**Total CTAs detected**: {a.get('cta_count', 0)}")

    # Contact methods
    lines.append(f"\n## Contact Accessibility: {a.get('contact_accessibility', 'unknown').upper()}\n")
    contact = s.get("contact_methods", [])
    if contact:
        lines.append("Contact methods found:")
        seen = set()
        for c in contact:
            key = f"{c['type']}:{c.get('value', '')}"
            if key not in seen:
                seen.add(key)
                lines.append(f"- **{c['type']}**: {c.get('value', 'in-page')}")
    else:
        lines.append("⚠️ No contact methods found (email, phone, chat, or scheduling links).")
        lines.append("Multiple contact options lower the barrier for potential customers.")

    # Buttons/CTAs found
    if s.get("buttons"):
        lines.append("\n## CTA Buttons Detected\n")
        for btn in s["buttons"][:8]:
            lines.append(f"- \"{btn}\"")

    # Issues
    issues = a.get("issues", [])
    if issues:
        lines.append("\n## Issues\n")
        for issue in issues:
            lines.append(f"- ❌ {issue}")

    # Recommendations
    recs = a.get("recommendations", [])
    if recs:
        lines.append("\n## Recommendations\n")
        for i, rec in enumerate(recs, 1):
            lines.append(f"{i}. {rec}")

    return "\n".join(lines)


@function_tool
async def audit_landing_page_cta(url: str) -> str:
    """Audit a landing page for CTA effectiveness: checks for clear primary CTA, CTA prominence, contact accessibility (email/phone/chat), and provides specific improvement recommendations.

    Args:
        url: The landing page URL to audit.
    """
    data = await _audit_cta_impl(url)
    return _format_cta_report(data)
