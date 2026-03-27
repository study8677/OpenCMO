"""Proactive Insight Engine — rule-based detectors that surface actionable changes.

Zero LLM cost. All detectors are pure Python comparing current vs previous scan data.
Insights are persisted to SQLite and surfaced via API to the frontend NotificationBell
and InsightBanner components.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from opencmo import storage

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Insight:
    project_id: int
    insight_type: str      # serp_drop, geo_decline, community_buzz, seo_regress, competitor_gap
    severity: str          # critical, warning, info
    title: str
    summary: str
    action_type: str       # navigate, chat, api_call
    action_params: str     # JSON string with route/prompt/endpoint


# ---------------------------------------------------------------------------
# Detectors
# ---------------------------------------------------------------------------


async def _detect_serp_drops(project_id: int) -> list[Insight]:
    """Detect keywords where SERP position dropped >= 5 positions."""
    insights: list[Insight] = []
    db = await storage.get_db()
    try:
        # Get latest 2 snapshots per keyword
        cursor = await db.execute(
            """SELECT keyword, position, checked_at,
                      ROW_NUMBER() OVER (PARTITION BY keyword ORDER BY checked_at DESC) AS rn
               FROM serp_snapshots
               WHERE project_id = ? AND error IS NULL AND position IS NOT NULL
               ORDER BY keyword, checked_at DESC""",
            (project_id,),
        )
        rows = await cursor.fetchall()

        # Group by keyword: {keyword: [(position, checked_at), ...]}
        kw_data: dict[str, list[tuple[int, str]]] = {}
        for r in rows:
            keyword, position, checked_at, rn = r[0], r[1], r[2], r[3]
            if rn <= 2:
                kw_data.setdefault(keyword, []).append((position, checked_at))

        for kw, snapshots in kw_data.items():
            if len(snapshots) < 2:
                continue
            current_pos, prev_pos = snapshots[0][0], snapshots[1][0]
            drop = current_pos - prev_pos  # positive = rank got worse
            if drop >= 5:
                severity = "critical" if drop >= 10 else "warning"
                insights.append(Insight(
                    project_id=project_id,
                    insight_type="serp_drop",
                    severity=severity,
                    title=f"Keyword '{kw}' dropped {drop} positions",
                    summary=f"'{kw}' moved from #{prev_pos} to #{current_pos}.",
                    action_type="navigate",
                    action_params=f'{{"route": "/projects/{project_id}/serp"}}',
                ))
    finally:
        await db.close()
    return insights


async def _detect_geo_decline(project_id: int) -> list[Insight]:
    """Detect GEO score decline >= 10 points."""
    latest = await storage.get_latest_scans(project_id)
    prev = await storage.get_previous_scans(project_id)

    if not latest.get("geo") or not prev or not prev.get("geo"):
        return []

    current_score = latest["geo"]["score"]
    prev_score = prev["geo"]["score"]
    if current_score is None or prev_score is None:
        return []

    drop = prev_score - current_score
    if drop >= 10:
        severity = "critical" if drop >= 20 else "warning"
        return [Insight(
            project_id=project_id,
            insight_type="geo_decline",
            severity=severity,
            title=f"GEO score dropped {drop} points",
            summary=f"AI visibility score fell from {prev_score} to {current_score}/100.",
            action_type="navigate",
            action_params=f'{{"route": "/projects/{project_id}/geo"}}',
        )]
    return []


async def _detect_community_buzz(project_id: int) -> list[Insight]:
    """Detect high-engagement community discussions (engagement > 50)."""
    insights: list[Insight] = []
    discussions = await storage.get_tracked_discussions(project_id)
    for d in discussions:
        score = d.get("engagement_score") or 0
        if score > 50:
            title_short = d["title"][:60]
            insights.append(Insight(
                project_id=project_id,
                insight_type="community_buzz",
                severity="warning" if score > 80 else "info",
                title=f"High-engagement discussion on {d['platform']}",
                summary=f'"{title_short}" — engagement {score}, {d.get("comments_count", 0)} comments.',
                action_type="navigate",
                action_params=f'{{"route": "/projects/{project_id}/community", "url": "{d["url"]}"}}',
            ))
    return insights[:3]  # Top 3 only


async def _detect_seo_regress(project_id: int) -> list[Insight]:
    """Detect SEO performance score regression > 0.1."""
    latest = await storage.get_latest_scans(project_id)
    prev = await storage.get_previous_scans(project_id)

    if not latest.get("seo") or not prev or not prev.get("seo"):
        return []

    current_score = latest["seo"]["score"]
    prev_score = prev["seo"]["score"]
    if current_score is None or prev_score is None:
        return []

    drop = prev_score - current_score
    if drop > 0.1:
        severity = "critical" if drop > 0.3 else "warning"
        return [Insight(
            project_id=project_id,
            insight_type="seo_regress",
            severity=severity,
            title=f"SEO performance dropped {drop:.0%}",
            summary=f"Performance score fell from {prev_score:.0%} to {current_score:.0%}.",
            action_type="navigate",
            action_params=f'{{"route": "/projects/{project_id}/seo"}}',
        )]
    return []


async def _detect_competitor_gaps(project_id: int) -> list[Insight]:
    """Detect competitor keywords that the brand doesn't track."""
    insights: list[Insight] = []
    db = await storage.get_db()
    try:
        cursor = await db.execute(
            """SELECT ck.keyword, COUNT(DISTINCT c.id) AS comp_count
               FROM competitor_keywords ck
               JOIN competitors c ON c.id = ck.competitor_id
               WHERE c.project_id = ?
                 AND LOWER(ck.keyword) NOT IN (
                     SELECT LOWER(keyword) FROM tracked_keywords WHERE project_id = ?
                 )
               GROUP BY LOWER(ck.keyword)
               ORDER BY comp_count DESC
               LIMIT 5""",
            (project_id, project_id),
        )
        rows = await cursor.fetchall()
        if rows and len(rows) >= 3:
            keywords = [r[0] for r in rows]
            insights.append(Insight(
                project_id=project_id,
                insight_type="competitor_gap",
                severity="warning",
                title=f"{len(rows)} keyword gaps found",
                summary=f"Competitors rank for keywords you don't track: {', '.join(keywords[:3])}.",
                action_type="navigate",
                action_params=f'{{"route": "/projects/{project_id}/graph"}}',
            ))
    finally:
        await db.close()
    return insights


async def _detect_citability_regression(project_id: int) -> list[Insight]:
    """Detect citability score regression (>10 point drop)."""
    insights: list[Insight] = []
    history = await storage.get_citability_history(project_id, limit=2)
    if len(history) >= 2:
        current = history[0]["avg_score"]
        previous = history[1]["avg_score"]
        drop = previous - current
        if drop > 10:
            insights.append(Insight(
                project_id=project_id,
                insight_type="citability_regression",
                severity="warning",
                title=f"Citability score dropped {drop:.0f} points",
                summary=f"AI citation readiness fell from {previous:.0f} to {current:.0f}. Content may be less likely to be cited by AI search engines.",
                action_type="chat",
                action_params=f'{{"message": "My citability score dropped from {previous:.0f} to {current:.0f}. How can I improve my content for AI citations?"}}',
            ))
    return insights


async def _detect_ai_crawler_blocks(project_id: int) -> list[Insight]:
    """Detect if >50% of AI crawlers are blocked."""
    insights: list[Insight] = []
    history = await storage.get_ai_crawler_history(project_id, limit=1)
    if history:
        latest = history[0]
        blocked = latest["blocked_count"]
        total = latest["total_crawlers"]
        if blocked > total * 0.5:
            insights.append(Insight(
                project_id=project_id,
                insight_type="ai_crawlers_blocked",
                severity="critical",
                title=f"{blocked}/{total} AI crawlers blocked",
                summary=f"More than half of AI crawlers are blocked by robots.txt. This severely limits your AI search visibility.",
                action_type="chat",
                action_params=f'{{"message": "My robots.txt is blocking {blocked} out of {total} AI crawlers. Help me fix this."}}',
            ))
    return insights


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_DETECTORS = [
    _detect_serp_drops,
    _detect_geo_decline,
    _detect_community_buzz,
    _detect_seo_regress,
    _detect_competitor_gaps,
    _detect_citability_regression,
    _detect_ai_crawler_blocks,
]


async def detect_insights(project_id: int) -> list[Insight]:
    """Run all detectors for a project. Deduplicates against recent insights (24h).

    Returns list of newly created insights.
    """
    all_insights: list[Insight] = []

    for detector in _DETECTORS:
        try:
            results = await detector(project_id)
            all_insights.extend(results)
        except Exception:
            logger.exception("Insight detector %s failed for project %d", detector.__name__, project_id)

    # Deduplicate: check existing insights from last 24h
    saved: list[Insight] = []
    for insight in all_insights:
        is_dup = await storage.is_insight_duplicate(
            project_id, insight.insight_type, insight.title,
        )
        if not is_dup:
            await storage.save_insight(
                project_id=insight.project_id,
                insight_type=insight.insight_type,
                severity=insight.severity,
                title=insight.title,
                summary=insight.summary,
                action_type=insight.action_type,
                action_params=insight.action_params,
            )
            saved.append(insight)

    if saved:
        logger.info("Generated %d new insights for project %d", len(saved), project_id)

    return saved
