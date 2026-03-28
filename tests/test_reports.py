"""Tests for the AI CMO report system."""

import asyncio
from types import SimpleNamespace
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


async def _seed_project():
    project_id = await storage.ensure_project("Acme", "https://acme.test", "saas")
    await storage.add_tracked_keyword(project_id, "acme ai")
    competitor_id = await storage.add_competitor(project_id, "CompetitorX", url="https://comp.test")
    await storage.add_competitor_keyword(competitor_id, "competitor keyword")
    await storage.save_seo_scan(
        project_id,
        "https://acme.test",
        "{}",
        score_performance=0.82,
        score_lcp=2100,
        score_cls=0.03,
        score_tbt=180,
        has_robots_txt=True,
        has_sitemap=True,
        has_schema_org=True,
    )
    await storage.save_geo_scan(
        project_id,
        74,
        visibility_score=28,
        position_score=31,
        sentiment_score=15,
        platform_results_json='{"chatgpt": {"mentioned": true}}',
    )
    await storage.save_community_scan(project_id, 4, '{"hits": []}')
    await storage.save_serp_snapshot(project_id, "acme ai", 5, "https://acme.test", "mock", None)
    return project_id


@pytest.mark.asyncio
async def test_report_version_history_tracks_latest_per_kind_and_audience():
    project_id = await _seed_project()

    first = await storage.create_report_bundle(
        project_id=project_id,
        kind="strategic",
        source_run_id=None,
        window_start=None,
        window_end=None,
        records={
            "human": {
                "generation_status": "completed",
                "content": "human v1",
                "content_html": "<p>human v1</p>",
                "meta": {"sample_count": 1},
            },
            "agent": {
                "generation_status": "completed",
                "content": "agent v1",
                "content_html": "<p>agent v1</p>",
                "meta": {"sample_count": 1},
            },
        },
    )
    second = await storage.create_report_bundle(
        project_id=project_id,
        kind="strategic",
        source_run_id=None,
        window_start=None,
        window_end=None,
        records={
            "human": {
                "generation_status": "completed",
                "content": "human v2",
                "content_html": "<p>human v2</p>",
                "meta": {"sample_count": 2},
            },
            "agent": {
                "generation_status": "completed",
                "content": "agent v2",
                "content_html": "<p>agent v2</p>",
                "meta": {"sample_count": 2},
            },
        },
    )

    assert all(item["version"] == 1 for item in first)
    assert all(item["version"] == 2 for item in second)

    latest = await storage.get_latest_reports(project_id)
    assert latest["strategic"]["human"]["content"] == "human v2"
    assert latest["strategic"]["agent"]["content"] == "agent v2"

    history = await storage.list_reports(project_id, kind="strategic", audience="human")
    assert [item["version"] for item in history] == [2, 1]
    assert history[0]["is_latest"] is True
    assert history[1]["is_latest"] is False


@pytest.mark.asyncio
async def test_generate_strategic_report_bundle_creates_human_and_agent_versions():
    project_id = await _seed_project()

    # Human now goes through the pipeline; agent uses single-call
    with patch("opencmo.report_pipeline.run_deep_report_pipeline", new_callable=AsyncMock) as mock_pipeline, \
         patch("opencmo.reports._generate_llm_markdown", new_callable=AsyncMock) as mock_llm:
        mock_pipeline.side_effect = [
            "# Strategic Human\n\n## 当前优势\n- 好",
            "# Strategic Human v2\n\n## 最近变化摘要\n- GEO up",
        ]
        mock_llm.side_effect = [
            "# Strategic Agent\n\n- objective: expand visibility",
            "# Strategic Agent v2\n\n- objective: defend gains",
        ]

        first = await service.regenerate_project_report(project_id, "strategic")
        second = await service.regenerate_project_report(project_id, "strategic")

    assert first["kind"] == "strategic"
    assert first["human"]["version"] == 1
    assert first["agent"]["version"] == 1
    assert "当前优势" in first["human"]["content"]
    assert first["human"]["meta"]["used_pipeline"] is True

    assert second["human"]["version"] == 2
    assert second["agent"]["version"] == 2
    assert "最近变化摘要" in second["human"]["content"]


@pytest.mark.asyncio
async def test_generate_periodic_report_bundle_marks_sparse_samples():
    project_id = await storage.ensure_project("Sparse", "https://sparse.test", "saas")
    await storage.save_geo_scan(
        project_id,
        33,
        visibility_score=10,
        position_score=12,
        sentiment_score=11,
        platform_results_json='{}',
    )

    with patch("opencmo.report_pipeline.run_deep_report_pipeline", new_callable=AsyncMock) as mock_pipeline, \
         patch("opencmo.reports._generate_llm_markdown", new_callable=AsyncMock) as mock_llm:
        mock_pipeline.return_value = "# Weekly Human\n\n样本稀疏"
        mock_llm.return_value = "# Weekly Agent\n\nsample_count: 1"
        report = await service.regenerate_project_report(project_id, "periodic")

    assert report["kind"] == "periodic"
    assert report["human"]["version"] == 1
    assert report["human"]["meta"]["sample_count"] == 1
    assert report["human"]["meta"]["low_sample"] is True
    assert "样本稀疏" in report["human"]["content"]
    assert mock_pipeline.await_count == 1  # human via pipeline
    assert mock_llm.await_count == 1       # agent via single-call


@pytest.mark.asyncio
async def test_send_project_report_reuses_latest_periodic_human_report(monkeypatch):
    project_id = await _seed_project()
    monkeypatch.setenv("OPENCMO_SMTP_HOST", "smtp.test.com")
    monkeypatch.setenv("OPENCMO_SMTP_PORT", "587")
    monkeypatch.setenv("OPENCMO_SMTP_USER", "user@test.com")
    monkeypatch.setenv("OPENCMO_SMTP_PASS", "pass")
    monkeypatch.setenv("OPENCMO_REPORT_EMAIL", "report@test.com")

    with patch("opencmo.report_pipeline.run_deep_report_pipeline", new_callable=AsyncMock) as mock_pipeline, \
         patch("opencmo.reports._generate_llm_markdown", new_callable=AsyncMock) as mock_llm:
        mock_pipeline.return_value = "# Weekly Human\n\n重要变化"
        mock_llm.return_value = "# Weekly Agent\n\nbrief"
        await service.regenerate_project_report(project_id, "periodic")

    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
        result = await service.send_project_report(project_id)

    assert result["ok"] is True
    sent_message = mock_server.send_message.call_args[0][0]
    assert "Weekly Human" in sent_message.as_string()


@pytest.mark.asyncio
async def test_generate_report_uses_persisted_llm_settings(monkeypatch):
    project_id = await _seed_project()
    await storage.set_setting("OPENAI_API_KEY", "persisted-key")
    await storage.set_setting("OPENAI_BASE_URL", "https://example.test/v1")
    await storage.set_setting("OPENCMO_MODEL_DEFAULT", "provider-model")

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENCMO_MODEL_DEFAULT", raising=False)

    def fake_response(text: str):
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=text))]
        )

    fake_create = AsyncMock(
        side_effect=[
            # Pipeline internally calls _generate_llm_markdown multiple times,
            # but we mock the pipeline itself for the human report.
            fake_response("# Agent brief"),
        ]
    )
    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=fake_create),
        )
    )

    with patch("opencmo.report_pipeline.run_deep_report_pipeline", new_callable=AsyncMock) as mock_pipeline, \
         patch("openai.AsyncOpenAI", return_value=fake_client) as mock_client:
        mock_pipeline.return_value = "# Human report via pipeline"
        report = await service.regenerate_project_report(project_id, "strategic")

    assert report["human"]["meta"]["used_fallback"] is False
    assert report["human"]["meta"]["used_pipeline"] is True
    assert report["human"]["meta"]["model"] == "provider-model"
    # Agent brief uses _generate_llm_markdown → openai client
    assert mock_client.call_count == 1
    for call in mock_client.call_args_list:
        assert call.kwargs == {
            "api_key": "persisted-key",
            "base_url": "https://example.test/v1",
        }
    assert fake_create.await_count == 1
    assert all(call.kwargs["model"] == "provider-model" for call in fake_create.await_args_list)
