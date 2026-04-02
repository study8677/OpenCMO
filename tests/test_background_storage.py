from __future__ import annotations

import pytest

from opencmo.background import storage as bg_storage


@pytest.mark.asyncio
async def test_insert_and_fetch_background_task(tmp_path, monkeypatch):
    from opencmo import storage

    db_path = tmp_path / "test.db"
    monkeypatch.setattr(storage, "_DB_PATH", db_path, raising=False)
    await storage.ensure_db()
    project_id = await storage.ensure_project("Tasked", "https://tasked.test", "saas")

    await bg_storage.insert_task(
        task_id="task-1",
        kind="scan",
        project_id=project_id,
        payload={"monitor_id": 12},
        dedupe_key="scan:monitor:12",
        priority=50,
        max_attempts=3,
    )
    task = await bg_storage.get_task("task-1")

    assert task is not None
    assert task["task_id"] == "task-1"
    assert task["kind"] == "scan"
    assert task["status"] == "queued"
    assert task["payload"]["monitor_id"] == 12


@pytest.mark.asyncio
async def test_append_task_event_and_list_events(tmp_path, monkeypatch):
    from opencmo import storage

    db_path = tmp_path / "test.db"
    monkeypatch.setattr(storage, "_DB_PATH", db_path, raising=False)
    await storage.ensure_db()
    project_id = await storage.ensure_project("Reported", "https://reported.test", "saas")

    await bg_storage.insert_task(
        task_id="task-2",
        kind="report",
        project_id=project_id,
        payload={"report_kind": "strategic"},
        dedupe_key="report:project:2:strategic",
        priority=60,
        max_attempts=3,
    )
    await bg_storage.append_task_event(
        "task-2",
        event_type="progress",
        phase="reflect",
        status="running",
        summary="Starting reflect phase",
        payload={"step": 1},
    )
    events = await bg_storage.list_task_events("task-2")

    assert len(events) == 1
    assert events[0]["event_type"] == "progress"
    assert events[0]["phase"] == "reflect"
    assert events[0]["payload"]["step"] == 1
