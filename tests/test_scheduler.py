"""Tests for scheduler module."""

from unittest.mock import patch, AsyncMock

import pytest

from opencmo import storage
import opencmo.scheduler as scheduler_module
from opencmo.scheduler import run_scheduled_scan


class _FakeCronTrigger:
    @classmethod
    def from_crontab(cls, expr):
        return {"expr": expr}


class _FakeScheduler:
    def __init__(self):
        self.running = False
        self.jobs = {}

    def add_job(self, func, trigger, args, id, replace_existing):
        self.jobs[id] = {
            "func": func,
            "trigger": trigger,
            "args": args,
            "replace_existing": replace_existing,
        }

    def get_job(self, job_id):
        return self.jobs.get(job_id)

    def get_jobs(self):
        return list(self.jobs.values())

    def remove_job(self, job_id):
        self.jobs.pop(job_id, None)

    def remove_all_jobs(self):
        self.jobs.clear()

    def start(self):
        self.running = True

    def shutdown(self, wait=False):
        self.running = False


@pytest.mark.asyncio
async def test_scheduled_scan_missing_project(tmp_path):
    """Scan for non-existent project should not raise."""
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        # Ensure tables exist
        db = await storage.get_db()
        await db.close()
        await run_scheduled_scan(99999, "full")  # should just log and return


@pytest.mark.asyncio
async def test_job_crud(tmp_path):
    """Test add/list/remove scheduled jobs."""
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        pid = await storage.ensure_project("TestBrand", "https://test.com", "testing")

        job_id = await storage.add_scheduled_job(pid, "seo", "0 9 * * *")
        assert job_id > 0

        jobs = await storage.list_scheduled_jobs()
        assert len(jobs) == 1
        assert jobs[0]["brand_name"] == "TestBrand"
        assert jobs[0]["job_type"] == "seo"

        ok = await storage.remove_scheduled_job(job_id)
        assert ok is True

        jobs = await storage.list_scheduled_jobs()
        assert len(jobs) == 0


@pytest.mark.asyncio
async def test_load_jobs_from_db_only_schedules_enabled_jobs(tmp_path):
    db_path = tmp_path / "test.db"
    fake_scheduler = _FakeScheduler()

    with patch.object(storage, "_DB_PATH", db_path), \
         patch.object(scheduler_module, "_HAS_APSCHEDULER", True), \
         patch.object(scheduler_module, "_scheduler", fake_scheduler), \
         patch.object(scheduler_module, "CronTrigger", _FakeCronTrigger, create=True):
        pid = await storage.ensure_project("Sched", "https://sched.com", "testing")
        enabled_id = await storage.add_scheduled_job(pid, "full", "0 9 * * *")
        disabled_id = await storage.add_scheduled_job(pid, "seo", "0 10 * * *")
        await storage.update_scheduled_job(disabled_id, enabled=False)

        loaded = await scheduler_module.load_jobs_from_db()

        assert loaded == 1
        assert fake_scheduler.get_job(f"opencmo_job_{enabled_id}") is not None
        assert fake_scheduler.get_job(f"opencmo_job_{disabled_id}") is None


@pytest.mark.asyncio
async def test_sync_job_record_replaces_and_removes_jobs(tmp_path):
    db_path = tmp_path / "test.db"
    fake_scheduler = _FakeScheduler()

    with patch.object(storage, "_DB_PATH", db_path), \
         patch.object(scheduler_module, "_HAS_APSCHEDULER", True), \
         patch.object(scheduler_module, "_scheduler", fake_scheduler), \
         patch.object(scheduler_module, "CronTrigger", _FakeCronTrigger, create=True):
        pid = await storage.ensure_project("Replace", "https://replace.com", "testing")
        job_id = await storage.add_scheduled_job(pid, "full", "0 9 * * *")
        job = await storage.get_scheduled_job(job_id)

        scheduler_module.sync_job_record(job)
        assert fake_scheduler.get_job(f"opencmo_job_{job_id}")["trigger"]["expr"] == "0 9 * * *"

        await storage.update_scheduled_job(job_id, cron_expr="15 8 * * *")
        scheduler_module.sync_job_record(await storage.get_scheduled_job(job_id))
        assert fake_scheduler.get_job(f"opencmo_job_{job_id}")["trigger"]["expr"] == "15 8 * * *"

        await storage.update_scheduled_job(job_id, enabled=False)
        scheduler_module.sync_job_record(await storage.get_scheduled_job(job_id))
        assert fake_scheduler.get_job(f"opencmo_job_{job_id}") is None


def test_stop_scheduler_clears_global_state():
    fake_scheduler = _FakeScheduler()
    fake_scheduler.start()

    with patch.object(scheduler_module, "_scheduler", fake_scheduler):
        scheduler_module.stop_scheduler()
        assert scheduler_module._scheduler is None


@pytest.mark.asyncio
async def test_run_scheduled_scan_generates_periodic_report_on_cron_full(tmp_path):
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        pid = await storage.ensure_project("SchedReport", "https://sched-report.com", "testing")
        await storage.add_scheduled_job(pid, "full", "0 9 * * 1")

        crawl_result = type("CrawlResult", (), {"html": "<html><title>Sched</title></html>"})()
        crawler = AsyncMock()
        crawler.__aenter__.return_value = crawler
        crawler.__aexit__.return_value = False
        crawler.arun.return_value = crawl_result

        with patch("crawl4ai.AsyncWebCrawler", return_value=crawler), \
             patch("opencmo.tools.seo_audit._fetch_core_web_vitals", new_callable=AsyncMock, return_value={"performance": 0.8, "lcp": 2200, "cls": 0.02, "tbt": 150}), \
             patch("opencmo.tools.seo_audit._check_robots_and_sitemap", new_callable=AsyncMock, return_value={"has_robots": True, "has_sitemap": True}), \
             patch("opencmo.tools.serp_tracker.track_project_keywords", new_callable=AsyncMock), \
             patch("opencmo.tools.ai_crawler_check._ai_crawler_impl", new_callable=AsyncMock, return_value={"blocked_count": 0, "total_crawlers": 14, "has_llms_txt": True, "crawler_results": []}), \
             patch("opencmo.tools.geo_providers.GEO_PROVIDER_REGISTRY", []), \
             patch("opencmo.tools.citability._citability_impl", new_callable=AsyncMock, return_value={"avg_score": 80, "top_blocks": [], "bottom_blocks": [], "grade_distribution": {}, "error": False}), \
             patch("opencmo.tools.brand_presence._brand_presence_impl", new_callable=AsyncMock, return_value={"footprint_score": 60, "platforms": []}), \
             patch("opencmo.tools.community._scan_community_impl", new_callable=AsyncMock, return_value='{"hits": []}'), \
             patch("opencmo.insights.detect_insights", new_callable=AsyncMock, return_value=[]), \
             patch("opencmo.autopilot.execute_autopilot", new_callable=AsyncMock, return_value=[]), \
             patch("opencmo.reports.generate_periodic_report_bundle", new_callable=AsyncMock) as mock_periodic:
            await run_scheduled_scan(pid, "full", triggered_by="cron")

        mock_periodic.assert_awaited_once_with(pid, source_run_id=None)
