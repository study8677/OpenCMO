"""Keyword suggestion with DR-aware difficulty filtering.

Estimates domain authority from available signals (SEO health score, sitemap
page count, brand presence score) and applies keyword difficulty thresholds
so that suggestions are realistic for the site's current strength.

DR estimation rules (heuristic, not a substitute for Ahrefs/Moz):
  - SEO health score contributes 40% (proxy for technical maturity)
  - Sitemap page count contributes 30% (proxy for content volume)
  - Brand presence score contributes 30% (proxy for off-site authority)

KD threshold mapping (aligned with industry guidelines):
  DR < 15  → only KD < 10 (very easy, long-tail)
  DR < 25  → only KD < 20 (easy)
  DR < 40  → only KD < 35 (moderate)
  DR < 60  → only KD < 50 (medium)
  DR 60+   → no filter
"""

from __future__ import annotations

import json
import logging

from agents import function_tool

from opencmo import llm, storage

logger = logging.getLogger(__name__)

# KD ceiling for each DR band
_KD_THRESHOLDS = [
    (15, 10),
    (25, 20),
    (40, 35),
    (60, 50),
]


def _estimate_dr(
    seo_health_score: float | None,
    sitemap_page_count: int | None,
    brand_presence_score: int | None,
) -> float:
    """Estimate domain rating from available signals. Returns 0-100."""
    score = 0.0
    weight = 0.0

    if seo_health_score is not None:
        # SEO health 0-100 maps roughly to DR 0-100 (generous floor)
        score += seo_health_score * 0.4
        weight += 0.4

    if sitemap_page_count is not None:
        # Pages: 1-10 → ~5 DR, 10-50 → ~15, 50-200 → ~30, 200-1000 → ~50, 1000+ → ~70
        if sitemap_page_count >= 1000:
            page_dr = 70
        elif sitemap_page_count >= 200:
            page_dr = 50
        elif sitemap_page_count >= 50:
            page_dr = 30
        elif sitemap_page_count >= 10:
            page_dr = 15
        else:
            page_dr = 5
        score += page_dr * 0.3
        weight += 0.3

    if brand_presence_score is not None:
        score += brand_presence_score * 0.3
        weight += 0.3

    if weight == 0:
        return 10.0  # conservative default for unknown sites

    return round(score / weight, 1)


def _kd_ceiling(estimated_dr: float) -> int | None:
    """Return the max keyword difficulty for the given DR. None = no limit."""
    for dr_limit, kd_limit in _KD_THRESHOLDS:
        if estimated_dr < dr_limit:
            return kd_limit
    return None


async def _gather_dr_signals(project_id: int) -> dict:
    """Collect signals needed for DR estimation from existing scan data."""
    signals: dict = {"seo_health_score": None, "sitemap_page_count": None, "brand_presence_score": None}

    try:
        seo_history = await storage.get_seo_history(project_id, limit=1)
        if seo_history:
            signals["seo_health_score"] = seo_history[0].get("seo_health_score")
    except Exception:
        pass

    # Sitemap page count from the latest SEO scan report (encoded in robots_sitemap check)
    try:
        db = await storage.get_db()
        try:
            cursor = await db.execute(
                "SELECT report_json FROM seo_scans WHERE project_id = ? ORDER BY scanned_at DESC LIMIT 1",
                (project_id,),
            )
            row = await cursor.fetchone()
            if row and row[0]:
                report_text = row[0]
                # Extract sitemap URL count from report text like "Found (42 URLs)"
                import re
                match = re.search(r"sitemap\.xml.*?(\d+)\s*URLs?\)", report_text)
                if match:
                    signals["sitemap_page_count"] = int(match.group(1))
        finally:
            await db.close()
    except Exception:
        pass

    try:
        bp_history = await storage.get_brand_presence_history(project_id, limit=1)
        if bp_history:
            signals["brand_presence_score"] = bp_history[0].get("footprint_score")
    except Exception:
        pass

    return signals


async def suggest_keywords_impl(project_id: int, url: str) -> dict:
    """Generate keyword suggestions with DR-aware difficulty filtering.

    Returns dict with estimated_dr, kd_ceiling, and filtered keyword list.
    """
    project = await storage.get_project(project_id)
    if not project:
        return {"error": "Project not found"}

    brand = project["brand_name"]
    category = project["category"]

    # Gather DR signals
    signals = await _gather_dr_signals(project_id)
    estimated_dr = _estimate_dr(
        signals["seo_health_score"],
        signals["sitemap_page_count"],
        signals["brand_presence_score"],
    )
    kd_max = _kd_ceiling(estimated_dr)

    kd_instruction = ""
    if kd_max is not None:
        kd_instruction = (
            f"\n\nIMPORTANT — DIFFICULTY FILTER:\n"
            f"This site's estimated Domain Rating is ~{estimated_dr:.0f} (low authority).\n"
            f"Only suggest keywords with estimated Keyword Difficulty (KD) ≤ {kd_max}.\n"
            f"This means: long-tail phrases, niche queries, question-based keywords.\n"
            f"Do NOT suggest high-competition head terms that this site cannot realistically rank for.\n"
            f"For each keyword, estimate KD as 'low' (0-20), 'medium' (20-40), or 'high' (40+)."
        )

    system_prompt = (
        "You are an SEO keyword strategist. Generate keyword suggestions for a website.\n"
        "Return ONLY valid JSON with this structure:\n"
        '{"keywords": [{"keyword": "...", "intent": "problem|tool|comparison|brand|informational", '
        '"estimated_kd": "low|medium|high", "rationale": "..."}]}\n'
        "Generate 8-12 keywords across these intent types:\n"
        "- problem: queries describing a pain point (e.g. 'how to monitor brand mentions')\n"
        "- tool: queries looking for a specific type of tool (e.g. 'open source SEO tool')\n"
        "- comparison: vs/alternative queries (e.g. 'ahrefs alternative free')\n"
        "- informational: educational queries in the domain (e.g. 'what is GEO optimization')\n"
        f"{kd_instruction}\n"
        "No markdown fences. Just the JSON object."
    )

    user_prompt = (
        f"Brand: {brand}\n"
        f"URL: {url}\n"
        f"Category: {category}\n"
        f"Estimated DR: {estimated_dr:.0f}/100\n"
    )

    try:
        raw = await llm.chat(system_prompt, user_prompt)
        # Parse JSON from response
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
        data = json.loads(text)

        # Post-filter: remove any 'high' KD keywords if site DR is low
        keywords = data.get("keywords", [])
        if kd_max is not None and kd_max <= 20:
            keywords = [kw for kw in keywords if kw.get("estimated_kd") != "high"]

        return {
            "estimated_dr": estimated_dr,
            "kd_ceiling": kd_max,
            "dr_signals": signals,
            "keywords": keywords,
        }
    except Exception as exc:
        logger.exception("Keyword suggestion failed for project %d", project_id)
        return {
            "estimated_dr": estimated_dr,
            "kd_ceiling": kd_max,
            "dr_signals": signals,
            "keywords": [],
            "error": str(exc),
        }


@function_tool
async def suggest_keywords(url: str) -> str:
    """Generate keyword suggestions filtered by the site's estimated Domain Rating. Low-DR sites get only low-difficulty keywords they can realistically rank for. Covers problem, tool, comparison, and informational intent types.

    Args:
        url: The website URL to generate keyword suggestions for.
    """
    from urllib.parse import urlparse as _urlparse

    parsed = _urlparse(url)
    domain = parsed.netloc.removeprefix("www.")

    project_id = await storage.ensure_project(domain, url, "")
    data = await suggest_keywords_impl(project_id, url)

    if data.get("error") and not data.get("keywords"):
        return f"Keyword suggestion failed: {data['error']}"

    lines = [f"# Keyword Suggestions for {domain}\n"]
    lines.append(f"**Estimated Domain Rating: {data['estimated_dr']:.0f}/100**")
    if data["kd_ceiling"] is not None:
        lines.append(f"**Keyword Difficulty ceiling: KD ≤ {data['kd_ceiling']}** (only realistic targets)\n")
    else:
        lines.append("**No difficulty filter** — site has enough authority for competitive keywords.\n")

    lines.append("| Keyword | Intent | Est. KD | Rationale |")
    lines.append("|---------|--------|---------|-----------|")
    for kw in data.get("keywords", []):
        lines.append(f"| {kw['keyword']} | {kw['intent']} | {kw.get('estimated_kd', '?')} | {kw.get('rationale', '')} |")

    return "\n".join(lines)
