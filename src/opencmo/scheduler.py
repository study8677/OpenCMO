"""Scheduler module — runs periodic scans using APScheduler."""

from __future__ import annotations

import asyncio
import logging

from opencmo import storage

logger = logging.getLogger(__name__)

# APScheduler is an optional dependency
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger

    _HAS_APSCHEDULER = True
except ImportError:
    _HAS_APSCHEDULER = False

_scheduler: "AsyncIOScheduler | None" = None


def _require_apscheduler():
    if not _HAS_APSCHEDULER:
        raise RuntimeError(
            "APScheduler is required for scheduling. Install with: pip install opencmo[scheduler]"
        )


async def _maybe_send_email_report(project_id: int, job_type: str, triggered_by: str):
    """Send email report only for (full, cron) runs."""
    if job_type != "full" or triggered_by != "cron":
        return
    try:
        from opencmo.tools.email_report import _get_smtp_config, send_report_impl

        if _get_smtp_config() is None:
            return
        await send_report_impl(project_id)
    except Exception:
        logger.exception("Email report failed for project %d", project_id)


async def run_scheduled_scan(
    project_id: int, job_type: str, job_id: int | None = None, triggered_by: str = "cron"
):
    """Execute a scan directly (no LLM), save results to DB.

    Args:
        project_id: The project to scan.
        job_type: One of 'seo', 'geo', 'community', 'full'.
        job_id: Optional scheduled_jobs.id to update last_run_at.
        triggered_by: "cron" (scheduled) or "manual" (CLI).
    """
    project = await storage.get_project(project_id)
    if not project:
        logger.error("Project %d not found, skipping scan", project_id)
        return

    brand = project["brand_name"]
    url = project["url"]
    category = project["category"]

    if job_type in ("seo", "full"):
        try:
            from opencmo.tools.seo_audit import (
                _SEOParser,
                _build_report,
                _check_robots_and_sitemap,
                _fetch_core_web_vitals,
            )
            from crawl4ai import AsyncWebCrawler

            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)
            parser = _SEOParser()
            html = getattr(result, "html", "") or ""
            parser.feed(html)
            cwv = await _fetch_core_web_vitals(url)
            robots_sitemap = await _check_robots_and_sitemap(url)
            report = _build_report(parser, result, url, cwv=cwv, robots_sitemap=robots_sitemap)
            await storage.save_seo_scan(
                project_id, url, report,
                score_performance=cwv.get("performance") if cwv else None,
                score_lcp=cwv.get("lcp") if cwv else None,
                score_cls=cwv.get("cls") if cwv else None,
                score_tbt=cwv.get("tbt") if cwv else None,
                has_robots_txt=robots_sitemap.get("has_robots") if robots_sitemap else None,
                has_sitemap=robots_sitemap.get("has_sitemap") if robots_sitemap else None,
                has_schema_org=bool(parser.schema_types),
            )
            logger.info("SEO scan saved for project %d", project_id)
        except Exception:
            logger.exception("SEO scan failed for project %d", project_id)

        # SERP tracking (independent — runs even if SEO audit fails)
        try:
            from opencmo.tools.serp_tracker import track_project_keywords

            await track_project_keywords(project_id)
            logger.info("SERP tracking done for project %d", project_id)
        except Exception:
            logger.exception("SERP tracking failed for project %d", project_id)

    if job_type in ("geo", "full"):
        try:
            import json
            from opencmo.tools.geo_providers import GEO_PROVIDER_REGISTRY

            enabled = [p for p in GEO_PROVIDER_REGISTRY if p.is_enabled]
            results = {}
            for provider in enabled:
                try:
                    r = await provider.check_visibility(brand, category)
                    results[provider.name] = r
                except Exception:
                    pass

            platforms_mentioned = sum(1 for r in results.values() if r.mentioned)
            visibility_score = int(platforms_mentioned / len(enabled) * 40) if enabled else 0
            position_scores = [30 * (1 - r.position_pct / 100) for r in results.values() if r.position_pct is not None]
            position_score = int(sum(position_scores) / len(position_scores)) if position_scores else 0
            sentiment_score = 15 if platforms_mentioned > 0 else 0
            geo_score = visibility_score + position_score + sentiment_score

            platform_json = json.dumps({
                name: {"mentioned": r.mentioned, "mention_count": r.mention_count, "position_pct": r.position_pct}
                for name, r in results.items()
            })
            await storage.save_geo_scan(
                project_id, geo_score,
                visibility_score=visibility_score,
                position_score=position_score,
                sentiment_score=sentiment_score,
                platform_results_json=platform_json,
            )
            logger.info("GEO scan saved for project %d", project_id)
        except Exception:
            logger.exception("GEO scan failed for project %d", project_id)

    if job_type in ("community", "full"):
        try:
            import json
            from opencmo.tools.community import _scan_community_impl

            raw = await _scan_community_impl(brand, category)
            data = json.loads(raw)
            total_hits = len(data.get("hits", []))
            await storage.save_community_scan(project_id, total_hits, raw)

            # Track discussions + snapshots
            for hit in data.get("hits", []):
                try:
                    disc_id = await storage.upsert_tracked_discussion(project_id, hit)
                    await storage.save_discussion_snapshot(
                        disc_id, hit.get("raw_score", 0),
                        hit.get("comments_count", 0),
                        hit.get("engagement_score", 0),
                    )
                except Exception:
                    pass

            logger.info("Community scan saved for project %d", project_id)
        except Exception:
            logger.exception("Community scan failed for project %d", project_id)

    # Update job last_run_at
    if job_id is not None:
        try:
            await storage.update_job_last_run(job_id)
        except Exception:
            pass

    # Email report (only for cron + full)
    await _maybe_send_email_report(project_id, job_type, triggered_by)


def get_scheduler() -> "AsyncIOScheduler":
    """Get or create the global scheduler instance."""
    _require_apscheduler()
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


async def load_jobs_from_db():
    """Load all enabled scheduled jobs from DB and add them to the scheduler."""
    _require_apscheduler()
    scheduler = get_scheduler()
    jobs = await storage.list_scheduled_jobs()
    for job in jobs:
        if not job["enabled"]:
            continue
        trigger = CronTrigger.from_crontab(job["cron_expr"])
        scheduler.add_job(
            run_scheduled_scan,
            trigger=trigger,
            args=[job["project_id"], job["job_type"], job["id"]],
            id=f"opencmo_job_{job['id']}",
            replace_existing=True,
        )
    return len(jobs)


def start_scheduler():
    """Start the scheduler (call after load_jobs_from_db)."""
    _require_apscheduler()
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()


def stop_scheduler():
    """Stop the scheduler if running."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        _scheduler = None
