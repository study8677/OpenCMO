"""Tests for the service layer."""

import asyncio
from unittest.mock import patch, AsyncMock

import pytest

from opencmo import storage, service


@pytest.fixture(autouse=True)
def _db(tmp_path):
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        yield


def run(coro):
    return asyncio.run(coro)


def test_create_monitor():
    result = run(service.create_monitor("Brand", "https://brand.com", "saas", keywords=["kw1", "kw2"]))
    assert result["project_id"] >= 1
    assert result["monitor_id"] >= 1
    assert result["keywords_added"] == ["kw1", "kw2"]


def test_create_monitor_no_keywords():
    result = run(service.create_monitor("Brand2", "https://brand2.com", "saas"))
    assert result["keywords_added"] == []


def test_list_monitors():
    run(service.create_monitor("A", "https://a.com", "cat"))
    run(service.create_monitor("B", "https://b.com", "cat"))
    jobs = run(service.list_monitors())
    assert len(jobs) == 2


def test_remove_monitor():
    result = run(service.create_monitor("X", "https://x.com", "cat"))
    ok = run(service.remove_monitor(result["monitor_id"]))
    assert ok is True
    ok2 = run(service.remove_monitor(9999))
    assert ok2 is False


def test_get_monitor():
    result = run(service.create_monitor("G", "https://g.com", "cat"))
    job = run(service.get_monitor(result["monitor_id"]))
    assert job is not None
    assert job["brand_name"] == "G"
    assert run(service.get_monitor(9999)) is None


def test_run_monitor():
    with patch("opencmo.scheduler.run_scheduled_scan", new_callable=AsyncMock) as mock_scan:
        result = run(service.create_monitor("R", "https://r.com", "cat"))
        run_result = run(service.run_monitor(result["monitor_id"]))
        assert run_result["ok"] is True
        mock_scan.assert_called_once()

    # Not found
    bad = run(service.run_monitor(9999))
    assert bad["ok"] is False


def test_resolve_project_by_id():
    result = run(service.create_monitor("Res", "https://res.com", "cat"))
    pid, err = run(service.resolve_project(str(result["project_id"])))
    assert pid == result["project_id"]
    assert err == ""


def test_resolve_project_by_brand():
    run(service.create_monitor("MyBrand", "https://mybrand.com", "cat"))
    pid, err = run(service.resolve_project("MyBrand"))
    assert pid is not None
    assert err == ""


def test_resolve_project_not_found():
    pid, err = run(service.resolve_project("NonExistent"))
    assert pid is None
    assert "not found" in err.lower() or "No project" in err


def test_manage_keywords():
    result = run(service.create_monitor("KW", "https://kw.com", "cat"))
    pid = result["project_id"]

    # add
    add_result = run(service.manage_keywords(pid, "add", keyword="test keyword"))
    assert add_result["keyword"] == "test keyword"

    # list
    list_result = run(service.manage_keywords(pid, "list"))
    assert len(list_result["keywords"]) == 1

    # rm
    kw_id = list_result["keywords"][0]["id"]
    rm_result = run(service.manage_keywords(pid, "rm", keyword_id=kw_id))
    assert rm_result["removed"] is True


def test_get_status_summary():
    run(service.create_monitor("S1", "https://s1.com", "cat"))
    run(service.create_monitor("S2", "https://s2.com", "cat"))
    summary = run(service.get_status_summary())
    assert len(summary) == 2
    assert "latest" in summary[0]


def test_create_monitor_syncs_runtime_job():
    with patch("opencmo.scheduler.sync_job_record") as mock_sync:
        result = run(service.create_monitor("Sync", "https://sync.com", "saas"))
        assert result["monitor_id"] >= 1
        mock_sync.assert_called_once()
        assert mock_sync.call_args[0][0]["id"] == result["monitor_id"]


def test_update_monitor_syncs_runtime_job():
    result = run(service.create_monitor("Upd", "https://upd.com", "saas"))

    with patch("opencmo.scheduler.sync_job_record") as mock_sync:
        ok = run(service.update_monitor(result["monitor_id"], cron_expr="15 8 * * *", enabled=False))
        assert ok is True
        mock_sync.assert_called_once()
        assert mock_sync.call_args[0][0]["enabled"] is False


def test_remove_monitor_unschedules_runtime_job():
    result = run(service.create_monitor("Rm", "https://rm.com", "saas"))

    with patch("opencmo.scheduler.unschedule_job") as mock_unschedule:
        ok = run(service.remove_monitor(result["monitor_id"]))
        assert ok is True
        mock_unschedule.assert_called_once_with(result["monitor_id"])
