"""AI crawler robots.txt detection and llms.txt check.

Inspired by geo-seo-claude (https://github.com/zubair-trabzada/geo-seo-claude).
Checks whether a site's robots.txt blocks 14 major AI crawlers and whether
an llms.txt file exists.
"""

from __future__ import annotations

import json
import logging
import re
from urllib.parse import urlparse

import httpx
from agents import function_tool

logger = logging.getLogger(__name__)

# 14 AI crawlers to check — ordered by importance
AI_CRAWLERS = (
    "GPTBot",
    "OAI-SearchBot",
    "ChatGPT-User",
    "ClaudeBot",
    "claudebot",
    "PerplexityBot",
    "Google-Extended",
    "Bytespider",
    "Amazonbot",
    "Applebot-Extended",
    "CCBot",
    "FacebookBot",
    "cohere-ai",
    "anthropic-ai",
)

# Human-readable labels
_CRAWLER_LABELS = {
    "GPTBot": "OpenAI GPTBot",
    "OAI-SearchBot": "OpenAI SearchBot",
    "ChatGPT-User": "ChatGPT User",
    "ClaudeBot": "Anthropic Claude",
    "claudebot": "Anthropic Claude (lowercase)",
    "PerplexityBot": "Perplexity AI",
    "Google-Extended": "Google Gemini",
    "Bytespider": "ByteDance",
    "Amazonbot": "Amazon",
    "Applebot-Extended": "Apple Intelligence",
    "CCBot": "Common Crawl",
    "FacebookBot": "Meta / Facebook",
    "cohere-ai": "Cohere AI",
    "anthropic-ai": "Anthropic AI",
}


def _parse_robots_for_crawlers(robots_text: str) -> dict[str, dict]:
    """Parse robots.txt and return per-crawler status."""
    results: dict[str, dict] = {}
    lines = robots_text.splitlines()

    # Build user-agent blocks
    blocks: dict[str, list[str]] = {}
    current_agents: list[str] = []

    for line in lines:
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.lower().startswith("user-agent:"):
            agent = line.split(":", 1)[1].strip()
            current_agents.append(agent)
        elif current_agents:
            for agent in current_agents:
                blocks.setdefault(agent, []).append(line)
        else:
            # Directive before any user-agent — skip
            pass
        # Reset agents on non-user-agent, non-directive lines
        if not line.lower().startswith("user-agent:") and not line.lower().startswith(("allow:", "disallow:", "sitemap:", "crawl-delay:")):
            current_agents = []

    # Re-parse: simpler approach — split by user-agent blocks
    blocks = {}
    current_agents = []
    for line in lines:
        stripped = line.split("#", 1)[0].strip()
        if not stripped:
            current_agents = []
            continue
        if stripped.lower().startswith("user-agent:"):
            agent = stripped.split(":", 1)[1].strip()
            if not current_agents:
                current_agents = [agent]
            else:
                current_agents.append(agent)
        else:
            for agent in current_agents:
                blocks.setdefault(agent, []).append(stripped)

    # Check wildcard rules
    wildcard_rules = blocks.get("*", [])
    wildcard_blocked = any(
        r.lower().startswith("disallow:") and r.split(":", 1)[1].strip() == "/"
        for r in wildcard_rules
    )

    for crawler in AI_CRAWLERS:
        label = _CRAWLER_LABELS.get(crawler, crawler)
        # Find matching block (case-insensitive)
        matched_block = None
        for agent_name, directives in blocks.items():
            if agent_name.lower() == crawler.lower():
                matched_block = directives
                break

        if matched_block is not None:
            has_disallow_all = any(
                d.lower().startswith("disallow:") and d.split(":", 1)[1].strip() == "/"
                for d in matched_block
            )
            has_allow = any(
                d.lower().startswith("allow:")
                for d in matched_block
            )
            has_partial_disallow = any(
                d.lower().startswith("disallow:") and d.split(":", 1)[1].strip() not in ("", "/")
                for d in matched_block
            )

            if has_disallow_all and not has_allow:
                status = "BLOCKED"
                directive = "Disallow: /"
            elif has_disallow_all and has_allow:
                status = "PARTIALLY_BLOCKED"
                directive = "; ".join(matched_block[:3])
            elif has_partial_disallow:
                status = "PARTIALLY_BLOCKED"
                directive = "; ".join(matched_block[:3])
            else:
                status = "ALLOWED"
                directive = "; ".join(matched_block[:2]) if matched_block else "Allow: /"
        elif wildcard_blocked:
            status = "BLOCKED_BY_WILDCARD"
            directive = "Blocked by User-agent: * Disallow: /"
        else:
            status = "NOT_MENTIONED"
            directive = "No specific rules"

        results[crawler] = {
            "label": label,
            "status": status,
            "directive": directive,
        }

    return results


async def _ai_crawler_impl(url: str) -> dict:
    """Core implementation — returns structured dict for storage and formatting."""
    origin = f"{urlparse(url).scheme or 'https'}://{urlparse(url).netloc}"
    robots_url = f"{origin}/robots.txt"
    llms_url = f"{origin}/llms.txt"

    crawler_results: dict = {}
    robots_found = False
    llms_found: bool | None = None
    llms_content = ""

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        # Fetch robots.txt
        try:
            resp = await client.get(robots_url)
            if resp.status_code == 200 and resp.text.strip():
                robots_found = True
                crawler_results = _parse_robots_for_crawlers(resp.text)
            else:
                robots_found = False
                # No robots.txt = all crawlers allowed by default
                for crawler in AI_CRAWLERS:
                    crawler_results[crawler] = {
                        "label": _CRAWLER_LABELS.get(crawler, crawler),
                        "status": "ALLOWED_BY_DEFAULT",
                        "directive": "No robots.txt found",
                    }
        except Exception as exc:
            logger.warning("Failed to fetch robots.txt for %s: %s", url, exc)
            for crawler in AI_CRAWLERS:
                crawler_results[crawler] = {
                    "label": _CRAWLER_LABELS.get(crawler, crawler),
                    "status": "UNKNOWN",
                    "directive": f"Error: {exc}",
                }

        # Fetch llms.txt
        try:
            resp = await client.get(llms_url)
            llms_found = resp.status_code == 200 and len(resp.text.strip()) > 10
            if llms_found:
                llms_content = resp.text[:2000]
        except Exception:
            llms_found = None

    blocked = sum(1 for v in crawler_results.values() if v["status"] in ("BLOCKED", "BLOCKED_BY_WILDCARD"))
    partial = sum(1 for v in crawler_results.values() if v["status"] == "PARTIALLY_BLOCKED")

    return {
        "url": url,
        "robots_found": robots_found,
        "crawler_results": crawler_results,
        "blocked_count": blocked,
        "partial_count": partial,
        "total_crawlers": len(AI_CRAWLERS),
        "has_llms_txt": llms_found,
        "llms_content": llms_content,
    }


def _format_report(data: dict) -> str:
    """Format the crawler check result as markdown."""
    lines = [f"## AI Crawler Access Report — {data['url']}\n"]

    blocked = data["blocked_count"]
    partial = data["partial_count"]
    total = data["total_crawlers"]
    allowed = total - blocked - partial

    if blocked == 0:
        lines.append(f"**All {total} AI crawlers can access this site.** Great for AI visibility.\n")
    elif blocked >= total * 0.5:
        lines.append(f"**WARNING: {blocked}/{total} AI crawlers are BLOCKED.** This severely limits AI search visibility.\n")
    else:
        lines.append(f"**{blocked}/{total} blocked, {partial} partially blocked, {allowed} allowed.**\n")

    # Table
    lines.append("| Crawler | Status | Details |")
    lines.append("|---------|--------|---------|")
    status_icons = {
        "ALLOWED": "✅ Allowed",
        "ALLOWED_BY_DEFAULT": "✅ Allowed (no robots.txt)",
        "BLOCKED": "🚫 Blocked",
        "BLOCKED_BY_WILDCARD": "⚠️ Blocked (wildcard)",
        "PARTIALLY_BLOCKED": "⚠️ Partial",
        "NOT_MENTIONED": "✅ Allowed (not mentioned)",
        "UNKNOWN": "❓ Unknown",
    }
    for crawler, info in data["crawler_results"].items():
        icon = status_icons.get(info["status"], info["status"])
        lines.append(f"| {info['label']} | {icon} | {info['directive'][:60]} |")

    # llms.txt
    lines.append("")
    if data["has_llms_txt"]:
        lines.append("### llms.txt: ✅ Found\n")
        lines.append(f"```\n{data['llms_content'][:500]}\n```")
    elif data["has_llms_txt"] is False:
        lines.append("### llms.txt: ❌ Not found\n")
        lines.append("Consider creating an `/llms.txt` file to help AI crawlers understand your site structure.")
    else:
        lines.append("### llms.txt: ❓ Could not check")

    # Recommendations
    lines.append("\n### Recommendations\n")
    if blocked > 0:
        lines.append("- **Unblock critical AI crawlers** — GPTBot, ClaudeBot, and PerplexityBot should be allowed for maximum AI visibility.")
    if not data["has_llms_txt"]:
        lines.append("- **Create an llms.txt file** — This emerging standard (<5% adoption) helps AI systems understand your site. Use `generate_llmstxt` to create one.")
    if blocked == 0 and data["has_llms_txt"]:
        lines.append("- Your AI crawler configuration is excellent. No changes needed.")

    return "\n".join(lines)


@function_tool
async def check_ai_crawler_access(url: str) -> str:
    """Check a website's robots.txt for 14 AI crawlers (GPTBot, ClaudeBot, PerplexityBot, etc.) and report which are blocked or allowed. Also checks for llms.txt."""
    data = await _ai_crawler_impl(url)
    return _format_report(data)


@function_tool
async def check_llms_txt(url: str) -> str:
    """Check if a website has an /llms.txt file and return its content."""
    origin = f"{urlparse(url).scheme or 'https'}://{urlparse(url).netloc}"
    llms_url = f"{origin}/llms.txt"

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        try:
            resp = await client.get(llms_url)
            if resp.status_code == 200 and len(resp.text.strip()) > 10:
                return f"## llms.txt Found\n\n```\n{resp.text[:3000]}\n```"
            return f"## llms.txt Not Found\n\nNo llms.txt file at `{llms_url}`. Consider creating one to guide AI crawlers."
        except Exception as exc:
            return f"Error checking llms.txt: {exc}"
