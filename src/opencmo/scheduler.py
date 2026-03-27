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


def is_scheduler_available() -> bool:
    """Return whether APScheduler is installed in this environment."""
    return _HAS_APSCHEDULER


def _job_key(job_id: int) -> str:
    return f"opencmo_job_{job_id}"


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

        # AI crawler access check (independent)
        try:
            import json as _json
            from opencmo.tools.ai_crawler_check import _ai_crawler_impl

            data = await _ai_crawler_impl(url)
            await storage.save_ai_crawler_scan(
                project_id, url, data["blocked_count"],
                total_crawlers=data["total_crawlers"],
                has_llms_txt=data["has_llms_txt"],
                results_json=_json.dumps(data["crawler_results"]),
            )
            logger.info("AI crawler scan saved for project %d", project_id)
        except Exception:
            logger.exception("AI crawler scan failed for project %d", project_id)

    if job_type in ("geo", "full"):
        try:
            import json
            from opencmo.tools.geo_providers import GEO_PROVIDER_REGISTRY

            enabled = [p for p in GEO_PROVIDER_REGISTRY if p.is_enabled]
            results = {}
            for provider in enabled:
                try:
                    agg = await provider.check_visibility_multi(brand, category)
                    results[provider.name] = agg
                except Exception:
                    pass

            platforms_mentioned = sum(1 for r in results.values() if r.mentioned)
            visibility_score = int(platforms_mentioned / len(enabled) * 40) if enabled else 0
            position_scores = [30 * (1 - r.best_position_pct / 100) for r in results.values() if r.best_position_pct is not None]
            position_score = int(sum(position_scores) / len(position_scores)) if position_scores else 0
            sentiment_score = 15 if platforms_mentioned > 0 else 0
            geo_score = visibility_score + position_score + sentiment_score

            platform_json = json.dumps({
                name: {"mentioned": r.mentioned, "mention_count": r.total_mention_count, "position_pct": r.best_position_pct}
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

        # Citability scan (independent)
        try:
            import json as _json
            from opencmo.tools.citability import _citability_impl

            data = await _citability_impl(url)
            if not data.get("error"):
                await storage.save_citability_scan(
                    project_id, url, data["avg_score"],
                    top_blocks_json=_json.dumps(data["top_blocks"]),
                    bottom_blocks_json=_json.dumps(data["bottom_blocks"]),
                    grade_distribution_json=_json.dumps(data["grade_distribution"]),
                    report_json=_json.dumps(data),
                )
                logger.info("Citability scan saved for project %d", project_id)
        except Exception:
            logger.exception("Citability scan failed for project %d", project_id)

        # Brand presence scan (independent)
        try:
            import json as _json
            from opencmo.tools.brand_presence import _brand_presence_impl

            data = await _brand_presence_impl(brand, url)
            await storage.save_brand_presence_scan(
                project_id, brand, data["footprint_score"],
                platforms_json=_json.dumps(data["platforms"], default=str),
            )
            logger.info("Brand presence scan saved for project %d", project_id)
        except Exception:
            logger.exception("Brand presence scan failed for project %d", project_id)

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

    # Detect insights (rule-based, zero LLM cost)
    try:
        from opencmo.insights import detect_insights
        await detect_insights(project_id)
    except Exception:
        logger.exception("Insight detection failed for project %d", project_id)

    # Autopilot: turn insights into content → approval queue
    try:
        from opencmo.autopilot import execute_autopilot
        results = await execute_autopilot(project_id)
        if results:
            logger.info("Autopilot generated %d approvals for project %d", len(results), project_id)
    except Exception:
        logger.exception("Autopilot execution failed for project %d", project_id)

    # Email report (only for cron + full)
    await _maybe_send_email_report(project_id, job_type, triggered_by)


def get_scheduler() -> "AsyncIOScheduler":
    """Get or create the global scheduler instance."""
    _require_apscheduler()
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


def scheduler_status() -> dict:
    """Return scheduler runtime state for health checks."""
    if not _HAS_APSCHEDULER:
        return {"installed": False, "running": False, "job_count": 0}

    if _scheduler is None:
        return {"installed": True, "running": False, "job_count": 0}

    return {
        "installed": True,
        "running": _scheduler.running,
        "job_count": len(_scheduler.get_jobs()),
    }


def sync_job_record(job: dict) -> bool:
    """Reconcile one scheduled job into APScheduler memory state."""
    if not _HAS_APSCHEDULER:
        return False

    scheduler = get_scheduler()
    job_key = _job_key(job["id"])
    if not job["enabled"]:
        if scheduler.get_job(job_key) is not None:
            scheduler.remove_job(job_key)
        return True

    trigger = CronTrigger.from_crontab(job["cron_expr"])
    scheduler.add_job(
        run_scheduled_scan,
        trigger=trigger,
        args=[job["project_id"], job["job_type"], job["id"]],
        id=job_key,
        replace_existing=True,
    )
    return True


def unschedule_job(job_id: int) -> bool:
    """Remove one scheduled job from APScheduler memory state."""
    if not _HAS_APSCHEDULER or _scheduler is None:
        return False

    job_key = _job_key(job_id)
    if _scheduler.get_job(job_key) is None:
        return False

    _scheduler.remove_job(job_key)
    return True


async def load_jobs_from_db():
    """Load all enabled scheduled jobs from DB and add them to the scheduler."""
    _require_apscheduler()
    scheduler = get_scheduler()
    scheduler.remove_all_jobs()
    jobs = await storage.list_scheduled_jobs()
    enabled_jobs = 0
    for job in jobs:
        if not job["enabled"]:
            continue
        sync_job_record(job)
        enabled_jobs += 1
    return enabled_jobs


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
