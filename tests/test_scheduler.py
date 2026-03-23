"""Tests for scheduler module."""

from unittest.mock import patch

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
