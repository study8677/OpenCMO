"""Tests for web dashboard routes (legacy + API v1)."""

import asyncio
import json
import os
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
        yield TestClient(app)


@pytest.fixture
def auth_client(tmp_path):
    """Client with OPENCMO_WEB_TOKEN set."""
    db_path = tmp_path / "test.db"
    with patch.object(storage, "_DB_PATH", db_path), \
         patch.dict(os.environ, {"OPENCMO_WEB_TOKEN": "secret123"}):
        asyncio.run(chat_sessions.clear_all())
        task_registry.clear_all()
        yield TestClient(app)


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
# Auth
# ---------------------------------------------------------------------------


def test_api_v1_auth_required(auth_client):
    resp = auth_client.get("/api/v1/projects")
    assert resp.status_code == 401


def test_api_v1_auth_with_bearer(auth_client):
    resp = auth_client.get("/api/v1/projects", headers={"Authorization": "Bearer secret123"})
    assert resp.status_code == 200


def test_api_v1_auth_bypass_without_token(client):
    """Without OPENCMO_WEB_TOKEN set, all routes are accessible."""
    resp = client.get("/api/v1/projects")
    assert resp.status_code == 200


def test_api_v1_auth_covers_old_routes(auth_client):
    """Token mode protects /project/* and /api/project/* too."""
    resp = auth_client.get("/project/1")
    assert resp.status_code == 401

    resp = auth_client.get("/api/project/1/seo-data")
    assert resp.status_code == 401


def test_api_v1_auth_login(auth_client):
    # Wrong token
    resp = auth_client.post("/api/v1/auth/login", json={"token": "wrong"})
    assert resp.status_code == 401

    # Correct token
    resp = auth_client.post("/api/v1/auth/login", json={"token": "secret123"})
    assert resp.status_code == 200
    assert "opencmo_token" in resp.cookies


def test_api_v1_auth_cookie(auth_client):
    """After login, cookie should grant access."""
    auth_client.post("/api/v1/auth/login", json={"token": "secret123"})
    resp = auth_client.get("/api/v1/projects")
    assert resp.status_code == 200


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

    # 404
    resp = client.get("/api/v1/projects/9999")
    assert resp.status_code == 404


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


# ---------------------------------------------------------------------------
# Tasks API
# ---------------------------------------------------------------------------


def test_api_v1_task_status(client):
    resp = client.post("/api/v1/monitors", json={
        "brand": "T", "url": "https://t.com", "category": "dev"
    })
    mid = resp.json()["monitor_id"]

    with patch("opencmo.scheduler.run_scheduled_scan", new_callable=AsyncMock):
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


# ---------------------------------------------------------------------------
# Chat API
# ---------------------------------------------------------------------------


def test_api_v1_chat_session_lifecycle(client):
    # Create session
    resp = client.post("/api/v1/chat/sessions")
    assert resp.status_code == 201
    session_id = resp.json()["session_id"]
    assert len(session_id) == 12


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
