"""Tests for web dashboard routes (legacy + API v1)."""

import asyncio
import json
import os
import sqlite3
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from opencmo import storage

# FastAPI is an optional dependency
pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from opencmo.web import app as app_module
from opencmo.web.app import app
from opencmo.web import chat_sessions, task_registry


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        # Clear in-memory state
        asyncio.run(chat_sessions.clear_all())
        task_registry.clear_all()
        with TestClient(app) as test_client:
            yield test_client






def _seed_project(brand="Test", url="https://test.com"):
    return asyncio.run(storage.ensure_project(brand, url, "testing"))


# ---------------------------------------------------------------------------
# Legacy routes
# ---------------------------------------------------------------------------


def test_dashboard_empty(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "OpenCMO" in resp.text


def test_dashboard_with_project(tmp_path):
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        asyncio.run(storage.ensure_project("Test", "https://test.com", "testing"))
        client = TestClient(app)
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Test" in resp.text


def test_project_not_found(client):
    resp = client.get("/project/99999")
    assert resp.status_code == 404


def test_project_pages(tmp_path):
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        pid = asyncio.run(storage.ensure_project("Test", "https://test.com", "testing"))
        client = TestClient(app)
        for path in [f"/project/{pid}", f"/project/{pid}/seo", f"/project/{pid}/geo", f"/project/{pid}/community"]:
            resp = client.get(path)
            assert resp.status_code == 200, f"Failed for {path}"


def test_api_endpoints(tmp_path):
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        pid = asyncio.run(storage.ensure_project("Test", "https://test.com", "testing"))
        client = TestClient(app)
        for path in [f"/api/project/{pid}/seo-data", f"/api/project/{pid}/geo-data", f"/api/project/{pid}/community-data"]:
            resp = client.get(path)
            assert resp.status_code == 200
            data = resp.json()
            assert "labels" in data or "scan_labels" in data


# ---------------------------------------------------------------------------
# Auth — auth middleware was removed in b78c9a7, routes are now fully open.
# ---------------------------------------------------------------------------


def test_api_v1_routes_accessible_without_token(client):
    """All API routes are accessible without any auth token."""
    resp = client.get("/api/v1/projects")
    assert resp.status_code == 200


def test_api_v1_health_public(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert "scheduler" in resp.json()


# ---------------------------------------------------------------------------
# Projects API
# ---------------------------------------------------------------------------


def test_api_v1_projects_crud(client):
    # Create via monitor (projects are created through monitors)
    resp = client.post("/api/v1/monitors", json={
        "brand": "TestBrand", "url": "https://test.com", "category": "saas"
    })
    assert resp.status_code == 201
    data = resp.json()
    pid = data["project_id"]

    # List
    resp = client.get("/api/v1/projects")
    assert resp.status_code == 200
    projects = resp.json()
    assert any(p["id"] == pid for p in projects)

    # Get
    resp = client.get(f"/api/v1/projects/{pid}")
    assert resp.status_code == 200
    assert resp.json()["brand_name"] == "TestBrand"

    # Summary
    resp = client.get(f"/api/v1/projects/{pid}/summary")
    assert resp.status_code == 200
    assert "latest" in resp.json()
    assert "latest_monitoring" in resp.json()

    # 404
    resp = client.get("/api/v1/projects/9999")
    assert resp.status_code == 404


def test_api_v1_community_discussions_include_match_metadata(client):
    pid = _seed_project("Signals", "https://signals.test")

    discussion_id = asyncio.run(
        storage.upsert_tracked_discussion(
            pid,
            {
                "platform": "reddit",
                "detail_id": "abc123",
                "title": "OpenCMO review",
                "url": "https://reddit.com/r/saas/comments/abc123/opencmo_review",
            },
        )
    )
    asyncio.run(storage.save_discussion_snapshot(discussion_id, 12, 4, 18))
    asyncio.run(
        storage.save_community_scan(
            pid,
            1,
            json.dumps(
                {
                    "hits": [
                        {
                            "platform": "reddit",
                            "detail_id": "abc123",
                            "title": "OpenCMO review",
                            "url": "https://reddit.com/r/saas/comments/abc123/opencmo_review",
                            "intent_type": "direct_mention",
                            "match_reason": "Matched the exact brand in the title.",
                            "matched_query": "\"OpenCMO\"",
                            "matched_terms": ["OpenCMO"],
                            "confidence": 0.92,
                            "source_kind": "post",
                        }
                    ]
                }
            ),
        )
    )

    resp = client.get(f"/api/v1/projects/{pid}/community/discussions")
    assert resp.status_code == 200
    payload = resp.json()
    assert len(payload) == 1
    assert payload[0]["intent_type"] == "direct_mention"
    assert payload[0]["match_reason"] == "Matched the exact brand in the title."
    assert payload[0]["matched_query"] == "\"OpenCMO\""
    assert payload[0]["matched_terms"] == ["OpenCMO"]
    assert payload[0]["confidence"] == 0.92
    assert payload[0]["source_kind"] == "post"


def test_api_v1_delete_project_with_related_records(tmp_path):
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path):
        asyncio.run(chat_sessions.clear_all())
        task_registry.clear_all()

        pid = asyncio.run(storage.ensure_project("Delete Me", "https://delete-me.test", "testing"))
        run = asyncio.run(storage.create_campaign_run(pid, "Launch", ["reddit"]))
        asyncio.run(
            storage.add_campaign_artifact(
                run["id"],
                "research_brief",
                "artifact body",
                None,
                "Delete regression",
            )
        )
        asyncio.run(
            storage.save_insight(
                pid,
                "serp_drop",
                "high",
                "Visibility dropped",
                "Investigate ranking change",
                "navigate",
                "{}",
            )
        )
        session_id = asyncio.run(chat_sessions.create_session(project_id=pid))

        conn = sqlite3.connect(db_path)
        try:
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute(
                """INSERT INTO trend_briefings
                   (project_id, topic, mode, platforms_queried, time_window_days, total_hits, briefing_markdown)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (pid, "AI marketing", "summary", "[]", 30, 0, "brief"),
            )
            conn.commit()
        finally:
            conn.close()

        with TestClient(app) as client:
            resp = client.delete(f"/api/v1/projects/{pid}")
            assert resp.status_code == 200
            assert resp.json() == {"ok": True}

        assert asyncio.run(storage.get_project(pid)) is None
        session = asyncio.run(storage.get_chat_session(session_id))
        assert session is not None
        assert session["project_id"] is None

        conn = sqlite3.connect(db_path)
        try:
            assert conn.execute(
                "SELECT COUNT(*) FROM campaign_runs WHERE project_id = ?",
                (pid,),
            ).fetchone()[0] == 0
            assert conn.execute(
                "SELECT COUNT(*) FROM campaign_artifacts WHERE run_id = ?",
                (run["id"],),
            ).fetchone()[0] == 0
            assert conn.execute(
                "SELECT COUNT(*) FROM insights WHERE project_id = ?",
                (pid,),
            ).fetchone()[0] == 0
            assert conn.execute(
                "SELECT COUNT(*) FROM trend_briefings WHERE project_id = ?",
                (pid,),
            ).fetchone()[0] == 0
        finally:
            conn.close()


def test_api_v1_community_discussions_includes_latest_external_hits(client):
    pid = _seed_project("External", "https://external.test")
    asyncio.run(
        storage.save_community_scan(
            pid,
            1,
            json.dumps(
                {
                    "hits": [
                        {
                            "platform": "linkedin",
                            "detail_id": "https://linkedin.com/posts/example",
                            "title": "External mention",
                            "url": "https://linkedin.com/posts/example",
                            "raw_score": None,
                            "comments_count": None,
                            "engagement_score": None,
                            "intent_type": "opportunity",
                            "match_reason": "Matched an external fallback query.",
                            "matched_query": "\"External\" site:linkedin.com",
                            "matched_terms": ["External"],
                            "confidence": 0.61,
                            "source_kind": "external_search",
                        }
                    ]
                }
            ),
        )
    )

    resp = client.get(f"/api/v1/projects/{pid}/community/discussions")
    assert resp.status_code == 200
    payload = resp.json()
    assert len(payload) == 1
    assert payload[0]["source_kind"] == "external_search"
    assert payload[0]["engagement_score"] is None
    assert payload[0]["match_reason"] == "Matched an external fallback query."


# ---------------------------------------------------------------------------
# Monitors API
# ---------------------------------------------------------------------------


def test_api_v1_monitors_crud(client):
    # Create
    resp = client.post("/api/v1/monitors", json={
        "brand": "Mon", "url": "https://mon.com", "category": "dev",
        "keywords": ["kw1", "kw2"]
    })
    assert resp.status_code == 201
    data = resp.json()
    mid = data["monitor_id"]
    assert data["keywords_added"] == ["kw1", "kw2"]

    # List
    resp = client.get("/api/v1/monitors")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # Delete
    resp = client.delete(f"/api/v1/monitors/{mid}")
    assert resp.status_code == 200

    # Delete again → 404
    resp = client.delete(f"/api/v1/monitors/{mid}")
    assert resp.status_code == 404


def test_api_v1_monitors_create_validation(client):
    resp = client.post("/api/v1/monitors", json={"brand": "X"})
    assert resp.status_code == 400


def test_api_v1_monitors_create_url_only(client):
    """Only url is required; brand and category are auto-derived."""
    resp = client.post("/api/v1/monitors", json={"url": "https://example.com"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["project_id"] > 0
    assert data["monitor_id"] > 0


def test_web_lifecycle_starts_and_stops_scheduler(tmp_path):
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path), \
         patch("opencmo.scheduler.is_scheduler_available", return_value=True), \
         patch("opencmo.scheduler.load_jobs_from_db", new_callable=AsyncMock, return_value=0) as mock_load, \
         patch("opencmo.scheduler.start_scheduler") as mock_start, \
         patch("opencmo.scheduler.stop_scheduler") as mock_stop:
        with TestClient(app) as test_client:
            resp = test_client.get("/api/v1/health")
            assert resp.status_code == 200

        mock_load.assert_awaited_once()
        mock_start.assert_called_once()
        mock_stop.assert_called_once()


def test_api_v1_monitor_run_conflict(client):
    """Same monitor cannot run twice concurrently."""
    resp = client.post("/api/v1/monitors", json={
        "brand": "Conf", "url": "https://conf.com", "category": "dev"
    })
    mid = resp.json()["monitor_id"]

    # Simulate an active scan by directly setting the active monitor
    task_registry._active_monitors[mid] = "fake_task"

    resp = client.post(f"/api/v1/monitors/{mid}/run")
    assert resp.status_code == 409


def test_api_v1_create_monitor_syncs_scheduler(client):
    with patch("opencmo.scheduler.sync_job_record") as mock_sync:
        resp = client.post("/api/v1/monitors", json={
            "brand": "SyncMon", "url": "https://syncmon.com", "category": "dev",
        })
        assert resp.status_code == 201
        mock_sync.assert_called_once()


def test_api_v1_update_monitor_syncs_scheduler(client):
    resp = client.post("/api/v1/monitors", json={
        "brand": "PatchMon", "url": "https://patchmon.com", "category": "dev",
    })
    mid = resp.json()["monitor_id"]

    with patch("opencmo.scheduler.sync_job_record") as mock_sync:
        resp = client.patch(f"/api/v1/monitors/{mid}", json={"enabled": False})
        assert resp.status_code == 200
        mock_sync.assert_called_once()


def test_api_v1_delete_monitor_unschedules_job(client):
    resp = client.post("/api/v1/monitors", json={
        "brand": "DeleteMon", "url": "https://deletemon.com", "category": "dev",
    })
    mid = resp.json()["monitor_id"]

    with patch("opencmo.scheduler.unschedule_job") as mock_unschedule:
        resp = client.delete(f"/api/v1/monitors/{mid}")
        assert resp.status_code == 200
        mock_unschedule.assert_called_once_with(mid)


def test_api_v1_task_artifacts_endpoints(client):
    pid = _seed_project()
    run_id = asyncio.run(storage.create_scan_run("task_artifacts_1", 1, pid, "full"))
    asyncio.run(storage.replace_scan_artifacts(
        run_id,
        [{
            "domain": "seo",
            "severity": "warning",
            "title": "Weak SEO baseline",
            "summary": "No strong rankings yet.",
            "confidence": 0.8,
            "evidence_refs": [],
        }],
        [{
            "domain": "seo",
            "priority": "high",
            "owner_type": "content",
            "action_type": "build_rankable_content",
            "title": "Build comparison pages",
            "summary": "Create pages for tracked keywords.",
            "rationale": "Needed for rankings.",
            "confidence": 0.75,
            "evidence_refs": [],
        }],
    ))

    task_registry._tasks["task_artifacts_1"] = task_registry.TaskRecord(
        task_id="task_artifacts_1",
        monitor_id=1,
        project_id=pid,
        job_type="full",
        status="completed",
        run_id=run_id,
        summary="done",
        findings_count=1,
        recommendations_count=1,
    )

    resp = client.get("/api/v1/tasks/task_artifacts_1/findings")
    assert resp.status_code == 200
    assert resp.json()[0]["title"] == "Weak SEO baseline"

    resp = client.get("/api/v1/tasks/task_artifacts_1/recommendations")
    assert resp.status_code == 200
    assert resp.json()[0]["title"] == "Build comparison pages"


# ---------------------------------------------------------------------------
# Keywords API
# ---------------------------------------------------------------------------


def test_api_v1_keywords_crud(client):
    resp = client.post("/api/v1/monitors", json={
        "brand": "KW", "url": "https://kw.com", "category": "dev"
    })
    pid = resp.json()["project_id"]

    # Add
    resp = client.post(f"/api/v1/projects/{pid}/keywords", json={"keyword": "test keyword"})
    assert resp.status_code == 201
    kw_id = resp.json()["id"]

    # List
    resp = client.get(f"/api/v1/projects/{pid}/keywords")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # Delete
    resp = client.delete(f"/api/v1/keywords/{kw_id}")
    assert resp.status_code == 200

    # Delete again → 404
    resp = client.delete(f"/api/v1/keywords/{kw_id}")
    assert resp.status_code == 404


def test_api_v1_keyword_validation(client):
    resp = client.post("/api/v1/monitors", json={
        "brand": "V", "url": "https://v.com", "category": "dev"
    })
    pid = resp.json()["project_id"]
    resp = client.post(f"/api/v1/projects/{pid}/keywords", json={"keyword": ""})
    assert resp.status_code == 400


def test_api_v1_approvals_queue_and_reject(client):
    pid = _seed_project("Approval", "https://approval.com")

    resp = client.post("/api/v1/approvals", json={
        "project_id": pid,
        "approval_type": "twitter_post",
        "title": "Launch thread",
        "content": "OpenCMO turns monitoring into measurable growth loops.",
        "payload": {"text": "OpenCMO turns monitoring into measurable growth loops."},
        "agent_name": "Growth Agent",
        "target_url": "https://twitter.com/opencmo",
    })
    assert resp.status_code == 201
    approval_id = resp.json()["id"]
    assert resp.json()["status"] == "pending"

    resp = client.get("/api/v1/approvals?status=pending")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.post(f"/api/v1/approvals/{approval_id}/reject", json={"decision_note": "off-brand"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"
    assert resp.json()["decision_note"] == "off-brand"


def test_api_v1_approve_approval_uses_stored_payload(client):
    pid = _seed_project("Publish", "https://publish.com")

    create = client.post("/api/v1/approvals", json={
        "project_id": pid,
        "approval_type": "twitter_post",
        "title": "Exact payload",
        "payload": {"text": "Exact publish payload"},
        "content": "Exact publish payload",
    })
    approval_id = create.json()["id"]

    with patch.dict(os.environ, {"OPENCMO_AUTO_PUBLISH": "1"}), \
         patch("opencmo.tools.publishers.publish_tweet_impl", new_callable=AsyncMock) as mock_publish:
        mock_publish.return_value = {
            "ok": True,
            "dry_run": False,
            "tweet_id": "12345",
            "url": "https://twitter.com/i/status/12345",
        }

        resp = client.post(f"/api/v1/approvals/{approval_id}/approve")
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"
        assert resp.json()["publish_result"]["tweet_id"] == "12345"
        mock_publish.assert_awaited_once_with("Exact publish payload", dry_run=False)


# ---------------------------------------------------------------------------
# Tasks API
# ---------------------------------------------------------------------------


def test_api_v1_task_status(client):
    with patch("opencmo.monitoring.run_monitoring_workflow", new_callable=AsyncMock) as mock_workflow:
        mock_workflow.return_value = {
            "run_id": 1,
            "summary": "done",
            "findings": [],
            "recommendations": [],
        }

        resp = client.post("/api/v1/monitors", json={
            "brand": "T", "url": "https://t.com", "category": "dev"
        })
        mid = resp.json()["monitor_id"]

        # Creating a monitor auto-submits the initial analysis task.
        task_registry.clear_all()

        resp = client.post(f"/api/v1/monitors/{mid}/run")
        assert resp.status_code == 202
        task_id = resp.json()["task_id"]

        resp = client.get(f"/api/v1/tasks/{task_id}")
        assert resp.status_code == 200
        assert resp.json()["task_id"] == task_id

        resp = client.get("/api/v1/tasks")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


def test_api_v1_task_not_found(client):
    resp = client.get("/api/v1/tasks/nonexistent")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Report API
# ---------------------------------------------------------------------------


def test_api_v1_report(client):
    resp = client.post("/api/v1/monitors", json={
        "brand": "Rep", "url": "https://rep.com", "category": "dev"
    })
    pid = resp.json()["project_id"]

    with patch("opencmo.tools.email_report.send_report_impl", new_callable=AsyncMock) as mock:
        mock.return_value = {"ok": True, "recipient": "test@test.com"}
        resp = client.post(f"/api/v1/projects/{pid}/report")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True


def test_api_v1_report_not_found(client):
    resp = client.post("/api/v1/projects/9999/report")
    assert resp.status_code == 404


def test_api_v1_reports_lifecycle(client):
    resp = client.post("/api/v1/monitors", json={
        "brand": "RepV2", "url": "https://repv2.com", "category": "dev"
    })
    pid = resp.json()["project_id"]

    with patch("opencmo.reports._generate_llm_markdown", new_callable=AsyncMock) as mock_llm:
        mock_llm.side_effect = [
            "# Strategic Human",
            "# Strategic Agent",
            "# Weekly Human",
            "# Weekly Agent",
        ]

        strategic = client.post(f"/api/v1/projects/{pid}/reports/strategic/regenerate")
        assert strategic.status_code == 200
        assert strategic.json()["kind"] == "strategic"

        periodic = client.post(f"/api/v1/projects/{pid}/reports/periodic/regenerate")
        assert periodic.status_code == 200
        assert periodic.json()["kind"] == "periodic"

    latest = client.get(f"/api/v1/projects/{pid}/reports/latest")
    assert latest.status_code == 200
    latest_payload = latest.json()
    assert latest_payload["strategic"]["human"]["version"] == 1
    assert latest_payload["periodic"]["agent"]["version"] == 1

    listed = client.get(f"/api/v1/projects/{pid}/reports")
    assert listed.status_code == 200
    assert len(listed.json()) == 4

    report_id = latest_payload["strategic"]["human"]["id"]
    detail = client.get(f"/api/v1/reports/{report_id}")
    assert detail.status_code == 200
    assert detail.json()["kind"] == "strategic"

    summary = client.get(f"/api/v1/projects/{pid}/summary")
    assert summary.status_code == 200
    assert summary.json()["latest_reports"]["strategic"]["human"]["id"] == report_id


# ---------------------------------------------------------------------------
# Chat API
# ---------------------------------------------------------------------------


def test_api_v1_chat_session_lifecycle(client):
    # Create session
    resp = client.post("/api/v1/chat/sessions")
    assert resp.status_code == 201
    session_id = resp.json()["session_id"]
    assert len(session_id) == 12


def test_api_v1_chat_session_project_scope(client):
    pid = _seed_project("Scoped", "https://scoped.com")

    resp = client.post("/api/v1/chat/sessions", json={"project_id": pid})
    assert resp.status_code == 201
    assert resp.json()["project_id"] == pid

    sessions = client.get("/api/v1/chat/sessions").json()
    assert sessions[0]["project_id"] == pid
    assert sessions[0]["project_name"] == "Scoped"


def test_api_v1_chat_sse(client):
    """Mock Runner.run_streamed and verify SSE event flow."""
    resp = client.post("/api/v1/chat/sessions")
    session_id = resp.json()["session_id"]

    # Build mock streamed result
    mock_result = MagicMock()
    mock_result.last_agent.name = "CMO Agent"
    mock_result.final_output = "Hello from CMO"
    mock_result.to_input_list.return_value = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "Hello from CMO"},
    ]

    # Mock stream_events to yield a delta event
    class MockDelta:
        type = "response.output_text.delta"
        delta = "Hello"

    class MockRawEvent:
        type = "raw_response_event"
        data = MockDelta()

    async def mock_stream():
        yield MockRawEvent()

    mock_result.stream_events = mock_stream

    with patch("agents.Runner.run_streamed", return_value=mock_result):
        resp = client.post("/api/v1/chat", json={
            "session_id": session_id,
            "message": "hi",
        })
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

        # Parse SSE events
        events = []
        for line in resp.text.strip().split("\n"):
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))

        assert any(e["type"] == "delta" for e in events)
        assert any(e["type"] == "done" for e in events)

    # Verify session was updated
    session = asyncio.run(chat_sessions.get_session(session_id))
    assert session is not None
    assert len(session) == 2  # user + assistant from to_input_list


def test_api_v1_chat_uses_session_project_context(client):
    pid = _seed_project("Context", "https://context.com")
    resp = client.post("/api/v1/chat/sessions", json={"project_id": pid})
    session_id = resp.json()["session_id"]

    mock_result = MagicMock()
    mock_result.last_agent.name = "CMO Agent"
    mock_result.final_output = "Hello from CMO"
    mock_result.to_input_list.return_value = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "Hello from CMO"},
    ]

    class MockDelta:
        type = "response.output_text.delta"
        delta = "Hello"

    class MockRawEvent:
        type = "raw_response_event"
        data = MockDelta()

    async def mock_stream():
        yield MockRawEvent()

    mock_result.stream_events = mock_stream

    with patch("opencmo.context.build_project_context", new_callable=AsyncMock) as mock_context:
        mock_context.return_value = "# Context"
        with patch("agents.Runner.run_streamed", return_value=mock_result) as mock_runner:
            resp = client.post("/api/v1/chat", json={
                "session_id": session_id,
                "message": "hi",
            })

    assert resp.status_code == 200
    mock_context.assert_awaited_once_with(pid, depth="full")
    input_items = mock_runner.call_args.args[1]
    assert input_items[0]["role"] == "system"
    assert "[Project Context]" in input_items[0]["content"]
    assert "# Context" in input_items[0]["content"]


def test_api_v1_chat_invalid_session(client):
    resp = client.post("/api/v1/chat", json={
        "session_id": "nonexistent",
        "message": "hi",
    })
    assert resp.status_code == 404


def test_api_v1_chat_empty_message(client):
    resp = client.post("/api/v1/chat/sessions")
    sid = resp.json()["session_id"]
    resp = client.post("/api/v1/chat", json={"session_id": sid, "message": ""})
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# SPA catch-all
# ---------------------------------------------------------------------------


def test_spa_catchall(client, tmp_path):
    """SPA routes serve index.html when dist exists."""
    spa_dir = tmp_path / "spa_dist"
    spa_dir.mkdir()
    (spa_dir / "index.html").write_text("<html>SPA</html>")
    assets_dir = spa_dir / "assets"
    assets_dir.mkdir()
    (assets_dir / "main.js").write_text("console.log('hi')")

    with patch.object(app_module, "_SPA_DIR", spa_dir):
        resp = client.get("/app")
        assert resp.status_code == 200
        assert "SPA" in resp.text

        resp = client.get("/app/projects/1")
        assert resp.status_code == 200
        assert "SPA" in resp.text

        resp = client.get("/app/assets/main.js")
        assert resp.status_code == 200
        assert "console" in resp.text


def test_spa_catchall_no_dist(client, tmp_path):
    """SPA routes return 404 message when dist doesn't exist."""
    fake_dir = tmp_path / "nonexistent_dist"
    with patch.object(app_module, "_SPA_DIR", fake_dir):
        resp = client.get("/app")
        assert resp.status_code == 404
        assert "not built" in resp.text.lower()


def test_spa_catchall_blocks_directory_traversal(client, tmp_path):
    """Traversal paths do not escape SPA dist directory."""
    spa_dir = tmp_path / "spa_dist"
    spa_dir.mkdir()
    (spa_dir / "index.html").write_text("<html>SPA</html>")
    secret = tmp_path / "secret.txt"
    secret.write_text("TOPSECRET")

    with patch.object(app_module, "_SPA_DIR", spa_dir):
        resp = client.get("/app/../secret.txt")
        assert resp.status_code == 200
        assert "SPA" in resp.text
        assert "TOPSECRET" not in resp.text


# ---------------------------------------------------------------------------
# Scan data endpoints (v1)
# ---------------------------------------------------------------------------


def test_scan_data_endpoints(client):
    resp = client.post("/api/v1/monitors", json={
        "brand": "Data", "url": "https://data.com", "category": "dev"
    })
    pid = resp.json()["project_id"]

    endpoints = [
        f"/api/v1/projects/{pid}/seo/history",
        f"/api/v1/projects/{pid}/seo/chart",
        f"/api/v1/projects/{pid}/geo/history",
        f"/api/v1/projects/{pid}/geo/chart",
        f"/api/v1/projects/{pid}/community/history",
        f"/api/v1/projects/{pid}/community/discussions",
        f"/api/v1/projects/{pid}/community/chart",
        f"/api/v1/projects/{pid}/serp/latest",
        f"/api/v1/projects/{pid}/serp/chart",
    ]
    for ep in endpoints:
        resp = client.get(ep)
        assert resp.status_code == 200, f"Failed for {ep}"
