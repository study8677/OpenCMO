"""Tests for the service layer."""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from opencmo import service, storage


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


@pytest.mark.asyncio
async def test_analyze_url_uses_shared_fetch_helper():
    """URL analysis should go through the Tavily-first shared fetch helper."""
    fetch_mock = AsyncMock(return_value=("# Supabase\n\nBuild in a weekend.", "tavily"))
    crawl_result = MagicMock()
    crawl_result.markdown = "# Crawl fallback"
    crawl_mock = AsyncMock()
    crawl_mock.__aenter__ = AsyncMock(return_value=crawl_mock)
    crawl_mock.__aexit__ = AsyncMock(return_value=False)
    crawl_mock.arun = AsyncMock(return_value=crawl_result)
    llm_mock = AsyncMock(side_effect=[
        "Filtered product summary",
        "Product analysis",
        "SEO analysis",
        "Community analysis",
        "Product refinement",
        "SEO refinement",
        "Community refinement",
        (
            '{"brand_name": "Supabase", "category": "database", '
            '"keywords": ["supabase", "postgres backend"], "competitors": []}'
        ),
    ])

    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False), \
         patch("opencmo.tools.crawl.fetch_url_content", fetch_mock, create=True), \
         patch("crawl4ai.AsyncWebCrawler", return_value=crawl_mock), \
         patch("openai.AsyncOpenAI", return_value=MagicMock()), \
         patch("opencmo.services.intelligence_service._llm_call", llm_mock):
        result = await service.analyze_url_with_ai("https://supabase.com")

    assert result["brand_name"] == "Supabase"
    assert result["category"] == "database"
    fetch_mock.assert_awaited_once_with(
        "https://supabase.com",
        max_chars=20000,
        tavily_extract_depth="advanced",
    )


@pytest.mark.asyncio
async def test_analyze_url_helper_fallback_still_returns_result():
    """URL analysis should still complete when shared fetch falls back to crawl."""
    fetch_mock = AsyncMock(return_value=("# Crawl content", "crawl4ai"))
    llm_mock = AsyncMock(side_effect=[
        "Filtered product summary",
        "Product analysis",
        "SEO analysis",
        "Community analysis",
        "Product refinement",
        "SEO refinement",
        "Community refinement",
        (
            '{"brand_name": "Example", "category": "saas", '
            '"keywords": ["example"], "competitors": []}'
        ),
    ])

    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False), \
         patch("opencmo.tools.crawl.fetch_url_content", fetch_mock, create=True), \
         patch("openai.AsyncOpenAI", return_value=MagicMock()), \
         patch("opencmo.services.intelligence_service._llm_call", llm_mock):
        result = await service.analyze_url_with_ai("https://example.com")

    assert result["brand_name"] == "Example"
    fetch_mock.assert_awaited_once_with(
        "https://example.com",
        max_chars=20000,
        tavily_extract_depth="advanced",
    )
