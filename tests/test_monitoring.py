"""Tests for monitoring orchestration."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from opencmo import storage
from opencmo.monitoring import run_monitoring_workflow


@pytest.fixture(autouse=True)
def _db(tmp_path):
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        yield


def run(coro):
    return asyncio.run(coro)


def test_run_monitoring_workflow_persists_artifacts():
    project_id = run(storage.ensure_project("Acme", "https://acme.test", "saas"))
    run(storage.add_tracked_keyword(project_id, "acme ai"))
    competitor_id = run(storage.add_competitor(project_id, "CompetitorX", url="https://comp.test"))
    run(storage.add_competitor_keyword(competitor_id, "acme ai"))

    run(storage.save_seo_scan(
        project_id,
        "https://acme.test",
        "{}",
        score_performance=0.42,
        score_lcp=4200,
        score_cls=0.18,
        score_tbt=700,
        has_robots_txt=False,
        has_sitemap=False,
        has_schema_org=False,
    ))
    run(storage.save_geo_scan(
        project_id,
        18,
        visibility_score=10,
        position_score=5,
        sentiment_score=3,
        platform_results_json='{"perplexity": {"mentioned": false}}',
    ))
    run(storage.save_community_scan(project_id, 0, '{"hits": []}'))

    with patch("opencmo.scheduler.run_scheduled_scan", new_callable=AsyncMock), \
         patch("opencmo.monitoring._collect_signals", new_callable=AsyncMock):
        result = run(run_monitoring_workflow(
            "task_monitor_1",
            project_id,
            monitor_id=1,
            job_type="full",
            job_id=1,
        ))

    assert result["status"] == "completed"
    assert result["findings"]
    assert result["recommendations"]

    findings = run(storage.get_task_findings("task_monitor_1"))
    recommendations = run(storage.get_task_recommendations("task_monitor_1"))
    latest = run(storage.get_latest_monitoring_summary(project_id))

    assert findings
    assert recommendations
    assert latest is not None
    assert latest["findings_count"] == len(findings)
    assert latest["recommendations_count"] == len(recommendations)
    assert findings[0]["metadata"]["status"] in {"confirmed", "likely", "hypothesis", "environment_limitation"}
    assert "dedupe_key" in findings[0]["metadata"]
    assert isinstance(recommendations[0]["metadata"], dict)
