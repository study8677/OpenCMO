# Unified Background Task Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace OpenCMO's split background-job mechanisms with one persistent task runtime for scan, report, and graph expansion jobs, while preserving current product behavior through compatibility endpoints.

**Architecture:** Add a new `opencmo.background` package with persistent task and event storage, a runtime service, an in-process worker, and three executors. Migrate producers first, then consumers, and finally remove legacy in-memory runtime state.

**Tech Stack:** Python 3.10+, FastAPI, aiosqlite/SQLite, asyncio, pytest

---

## File Structure

### New files

- `src/opencmo/background/__init__.py`
  - Re-export background service entrypoints used by routers and startup wiring.
- `src/opencmo/background/types.py`
  - Canonical task kinds, task statuses, event shapes, worker identity helpers, and typed payload helpers.
- `src/opencmo/background/storage.py`
  - CRUD for `background_tasks` and `background_task_events`.
- `src/opencmo/background/service.py`
  - High-level enqueue, dedupe, cancellation, recovery, detail lookup, and event append APIs.
- `src/opencmo/background/worker.py`
  - In-process polling worker with claim, heartbeat, executor dispatch, and stale recovery loops.
- `src/opencmo/background/executors/__init__.py`
  - Executor registry.
- `src/opencmo/background/executors/scan.py`
  - Adapter from unified task runtime into `run_monitoring_workflow`.
- `src/opencmo/background/executors/report.py`
  - Adapter from unified task runtime into `service.regenerate_project_report`.
- `src/opencmo/background/executors/graph_expansion.py`
  - Adapter from unified task runtime into `run_expansion`.
- `tests/test_background_storage.py`
  - Storage and state-transition unit tests.
- `tests/test_background_service.py`
  - Enqueue, dedupe, cancel, and recovery tests.
- `tests/test_background_worker.py`
  - Worker claim, heartbeat, and executor dispatch tests.

### Modified files

- `src/opencmo/storage/_db.py`
  - Add new runtime tables and indexes.
- `src/opencmo/storage/__init__.py`
  - Re-export background runtime helpers if needed by current import style.
- `src/opencmo/web/app.py`
  - Start and stop the background worker; remove expansion runtime globals.
- `src/opencmo/web/routers/monitors.py`
  - Enqueue scan tasks through background service.
- `src/opencmo/web/routers/report.py`
  - Replace `report_tasks`-specific runtime flow with unified tasks.
- `src/opencmo/web/routers/graph.py`
  - Enqueue graph expansion through background service and read progress via unified events.
- `src/opencmo/web/routers/events.py`
  - Stream persisted unified task events rather than in-memory scan records.
- `src/opencmo/web/routers/tasks.py`
  - Read unified task records instead of `task_registry`.
- `src/opencmo/storage/graph.py`
  - Keep graph domain state but remove runtime ownership assumptions where necessary.
- `tests/test_web.py`
  - Update router/API expectations.
- `tests/test_scheduler.py`
  - Add or update any task-related integration expectations if affected.

### Deleted files

- `src/opencmo/web/task_registry.py`
  - Remove after all routes and SSE consumers move to the unified runtime.

---

### Task 1: Add Persistent Background Task Tables And Typed Runtime Primitives

**Files:**
- Create: `src/opencmo/background/__init__.py`
- Create: `src/opencmo/background/types.py`
- Modify: `src/opencmo/storage/_db.py`
- Test: `tests/test_background_storage.py`

- [ ] **Step 1: Write the failing storage tests**

```python
import pytest

from opencmo.background import storage as bg_storage


@pytest.mark.asyncio
async def test_insert_and_fetch_background_task(tmp_path, monkeypatch):
    from opencmo import storage

    db_path = tmp_path / "test.db"
    monkeypatch.setattr(storage, "_DB_PATH", db_path, raising=False)
    await storage.ensure_db()

    await bg_storage.insert_task(
        task_id="task-1",
        kind="scan",
        project_id=1,
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

    await bg_storage.insert_task(
        task_id="task-2",
        kind="report",
        project_id=2,
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_background_storage.py -q`
Expected: FAIL with `ModuleNotFoundError` for `opencmo.background` or missing storage functions.

- [ ] **Step 3: Add schema and typed runtime primitives**

```python
# src/opencmo/background/types.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
import socket
import uuid

TASK_KINDS = {"scan", "report", "graph_expansion"}
ACTIVE_STATUSES = {"queued", "claimed", "running", "cancel_requested"}
TERMINAL_STATUSES = {"completed", "failed", "cancelled"}


def make_worker_id() -> str:
    return f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"


@dataclass(frozen=True)
class TaskEventInput:
    event_type: str
    phase: str = ""
    status: str = ""
    summary: str = ""
    payload: dict | None = None
```

```python
# src/opencmo/storage/_db.py
CREATE TABLE IF NOT EXISTS background_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL,
    project_id INTEGER REFERENCES projects(id),
    status TEXT NOT NULL DEFAULT 'queued',
    payload_json TEXT NOT NULL DEFAULT '{}',
    result_json TEXT NOT NULL DEFAULT '{}',
    error_json TEXT NOT NULL DEFAULT '{}',
    dedupe_key TEXT,
    priority INTEGER NOT NULL DEFAULT 50,
    run_after TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    worker_id TEXT,
    claimed_at TEXT,
    heartbeat_at TEXT,
    started_at TEXT,
    completed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS background_task_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL REFERENCES background_tasks(task_id),
    event_type TEXT NOT NULL,
    phase TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_background_tasks_status_priority
ON background_tasks(status, priority, run_after, created_at);

CREATE INDEX IF NOT EXISTS idx_background_tasks_project_created
ON background_tasks(project_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_background_task_events_task_id
ON background_task_events(task_id, id);
```

- [ ] **Step 4: Implement minimal storage helpers**

```python
# src/opencmo/background/storage.py
from __future__ import annotations

import json

from opencmo.storage._db import get_db


def _task_row_to_dict(row) -> dict:
    return {
        "id": row[0],
        "task_id": row[1],
        "kind": row[2],
        "project_id": row[3],
        "status": row[4],
        "payload": json.loads(row[5] or "{}"),
        "result": json.loads(row[6] or "{}"),
        "error": json.loads(row[7] or "{}"),
        "dedupe_key": row[8],
        "priority": row[9],
        "run_after": row[10],
        "attempt_count": row[11],
        "max_attempts": row[12],
        "worker_id": row[13],
        "claimed_at": row[14],
        "heartbeat_at": row[15],
        "started_at": row[16],
        "completed_at": row[17],
        "created_at": row[18],
        "updated_at": row[19],
    }


async def insert_task(*, task_id: str, kind: str, project_id: int | None, payload: dict, dedupe_key: str | None, priority: int, max_attempts: int) -> None:
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO background_tasks
               (task_id, kind, project_id, payload_json, dedupe_key, priority, max_attempts)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (task_id, kind, project_id, json.dumps(payload), dedupe_key, priority, max_attempts),
        )
        await db.commit()
    finally:
        await db.close()


async def get_task(task_id: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, task_id, kind, project_id, status, payload_json, result_json,
                      error_json, dedupe_key, priority, run_after, attempt_count,
                      max_attempts, worker_id, claimed_at, heartbeat_at, started_at,
                      completed_at, created_at, updated_at
               FROM background_tasks WHERE task_id = ?""",
            (task_id,),
        )
        row = await cursor.fetchone()
        return _task_row_to_dict(row) if row else None
    finally:
        await db.close()


async def append_task_event(task_id: str, *, event_type: str, phase: str = "", status: str = "", summary: str = "", payload: dict | None = None) -> int:
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO background_task_events
               (task_id, event_type, phase, status, summary, payload_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (task_id, event_type, phase, status, summary, json.dumps(payload or {})),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_background_storage.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/opencmo/background/__init__.py src/opencmo/background/types.py src/opencmo/background/storage.py src/opencmo/storage/_db.py tests/test_background_storage.py
git commit -m "feat: add persistent background task storage"
```

### Task 2: Implement Runtime Service For Enqueue, Dedupe, Cancel, And Recovery

**Files:**
- Create: `src/opencmo/background/service.py`
- Modify: `src/opencmo/background/storage.py`
- Modify: `src/opencmo/background/__init__.py`
- Test: `tests/test_background_service.py`

- [ ] **Step 1: Write the failing service tests**

```python
import pytest

from opencmo.background import service as bg_service


@pytest.mark.asyncio
async def test_enqueue_returns_existing_active_task_for_same_dedupe_key(tmp_path, monkeypatch):
    from opencmo import storage

    db_path = tmp_path / "test.db"
    monkeypatch.setattr(storage, "_DB_PATH", db_path, raising=False)
    await storage.ensure_db()

    first = await bg_service.enqueue_task(
        kind="report",
        project_id=7,
        payload={"report_kind": "periodic"},
        dedupe_key="report:project:7:periodic",
    )
    second = await bg_service.enqueue_task(
        kind="report",
        project_id=7,
        payload={"report_kind": "periodic"},
        dedupe_key="report:project:7:periodic",
    )

    assert second["task_id"] == first["task_id"]
    assert second["status"] == "queued"


@pytest.mark.asyncio
async def test_request_cancel_marks_active_task(tmp_path, monkeypatch):
    from opencmo import storage

    db_path = tmp_path / "test.db"
    monkeypatch.setattr(storage, "_DB_PATH", db_path, raising=False)
    await storage.ensure_db()

    task = await bg_service.enqueue_task(
        kind="graph_expansion",
        project_id=4,
        payload={"project_id": 4, "resume": True},
        dedupe_key="graph:project:4",
    )
    ok = await bg_service.request_cancel(task["task_id"])
    updated = await bg_service.get_task(task["task_id"])

    assert ok is True
    assert updated["status"] == "cancel_requested"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_background_service.py -q`
Expected: FAIL because `enqueue_task` and `request_cancel` do not exist yet.

- [ ] **Step 3: Add service-layer enqueue, dedupe, and cancellation**

```python
# src/opencmo/background/service.py
from __future__ import annotations

import uuid

from opencmo.background import storage as bg_storage
from opencmo.background.types import ACTIVE_STATUSES


async def enqueue_task(*, kind: str, project_id: int | None, payload: dict, dedupe_key: str | None, priority: int = 50, max_attempts: int = 3) -> dict:
    if dedupe_key:
        existing = await bg_storage.find_active_task_by_dedupe_key(dedupe_key)
        if existing is not None:
            return existing

    task_id = str(uuid.uuid4())
    await bg_storage.insert_task(
        task_id=task_id,
        kind=kind,
        project_id=project_id,
        payload=payload,
        dedupe_key=dedupe_key,
        priority=priority,
        max_attempts=max_attempts,
    )
    await bg_storage.append_task_event(
        task_id,
        event_type="state_change",
        status="queued",
        summary=f"{kind} task queued",
        payload={"kind": kind},
    )
    return await bg_storage.get_task(task_id)


async def get_task(task_id: str) -> dict | None:
    return await bg_storage.get_task(task_id)


async def request_cancel(task_id: str) -> bool:
    task = await bg_storage.get_task(task_id)
    if task is None:
        return False
    if task["status"] in {"completed", "failed", "cancelled"}:
        return False
    await bg_storage.update_task_status(task_id, "cancel_requested")
    await bg_storage.append_task_event(
        task_id,
        event_type="state_change",
        status="cancel_requested",
        summary="Cancellation requested",
    )
    return True
```

- [ ] **Step 4: Add stale recovery helpers**

```python
# src/opencmo/background/service.py
async def recover_stale_tasks(*, stale_after_seconds: int) -> int:
    stale_tasks = await bg_storage.list_stale_tasks(stale_after_seconds=stale_after_seconds)
    fixed = 0
    for task in stale_tasks:
        if task["attempt_count"] < task["max_attempts"]:
            await bg_storage.requeue_task(task["task_id"])
            await bg_storage.append_task_event(
                task["task_id"],
                event_type="state_change",
                status="queued",
                summary="Task requeued after stale heartbeat",
            )
        else:
            await bg_storage.fail_task(
                task["task_id"],
                error={"message": "Task exceeded max attempts after stale heartbeat"},
            )
        fixed += 1
    return fixed
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_background_service.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/opencmo/background/__init__.py src/opencmo/background/storage.py src/opencmo/background/service.py tests/test_background_service.py
git commit -m "feat: add background task service lifecycle"
```

### Task 3: Build Worker Loop And Executor Registry

**Files:**
- Create: `src/opencmo/background/worker.py`
- Create: `src/opencmo/background/executors/__init__.py`
- Create: `tests/test_background_worker.py`
- Modify: `src/opencmo/background/storage.py`
- Modify: `src/opencmo/background/service.py`

- [ ] **Step 1: Write the failing worker tests**

```python
import asyncio

import pytest

from opencmo.background import service as bg_service
from opencmo.background.worker import BackgroundWorker


@pytest.mark.asyncio
async def test_worker_claims_and_completes_executor_task(tmp_path, monkeypatch):
    from opencmo import storage

    db_path = tmp_path / "test.db"
    monkeypatch.setattr(storage, "_DB_PATH", db_path, raising=False)
    await storage.ensure_db()

    task = await bg_service.enqueue_task(
        kind="scan",
        project_id=5,
        payload={"project_id": 5},
        dedupe_key="scan:monitor:5",
    )

    worker = BackgroundWorker(poll_interval=0.01, stale_after_seconds=60)
    worker.register_executor("scan", lambda ctx: ctx.complete({"ok": True}))

    await worker.start()
    await asyncio.sleep(0.05)
    await worker.stop()

    updated = await bg_service.get_task(task["task_id"])
    assert updated["status"] == "completed"
    assert updated["result"]["ok"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_background_worker.py -q`
Expected: FAIL because `BackgroundWorker` does not exist.

- [ ] **Step 3: Implement worker lifecycle and claim flow**

```python
# src/opencmo/background/worker.py
from __future__ import annotations

import asyncio

from opencmo.background import service as bg_service
from opencmo.background.types import make_worker_id


class ExecutorContext:
    def __init__(self, task: dict):
        self.task = task

    async def emit(self, *, event_type: str = "progress", phase: str = "", status: str = "", summary: str = "", payload: dict | None = None):
        await bg_service.append_event(
            self.task["task_id"],
            event_type=event_type,
            phase=phase,
            status=status,
            summary=summary,
            payload=payload or {},
        )

    async def complete(self, result: dict):
        await bg_service.complete_task(self.task["task_id"], result=result)

    async def fail(self, error: dict):
        await bg_service.fail_task(self.task["task_id"], error=error)


class BackgroundWorker:
    def __init__(self, *, poll_interval: float = 0.5, stale_after_seconds: int = 90):
        self.poll_interval = poll_interval
        self.stale_after_seconds = stale_after_seconds
        self.worker_id = make_worker_id()
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self._executors: dict[str, object] = {}

    def register_executor(self, kind: str, executor):
        self._executors[kind] = executor

    async def start(self):
        if self._task is not None:
            return
        self._stop.clear()
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self):
        if self._task is None:
            return
        self._stop.set()
        await self._task
        self._task = None

    async def _run_loop(self):
        while not self._stop.is_set():
            await bg_service.recover_stale_tasks(stale_after_seconds=self.stale_after_seconds)
            task = await bg_service.claim_next_task(worker_id=self.worker_id)
            if task is None:
                await asyncio.sleep(self.poll_interval)
                continue
            asyncio.create_task(self._run_claimed_task(task))

    async def _run_claimed_task(self, task: dict):
        executor = self._executors[task["kind"]]
        await bg_service.mark_task_running(task["task_id"], worker_id=self.worker_id)
        ctx = ExecutorContext(task)
        await executor(ctx)
```

- [ ] **Step 4: Add heartbeat and cancellation support**

```python
# src/opencmo/background/worker.py
async def _run_claimed_task(self, task: dict):
    heartbeat_task = asyncio.create_task(self._heartbeat_loop(task["task_id"]))
    try:
        executor = self._executors[task["kind"]]
        await bg_service.mark_task_running(task["task_id"], worker_id=self.worker_id)
        fresh = await bg_service.get_task(task["task_id"])
        ctx = ExecutorContext(fresh)
        await executor(ctx)
    except Exception as exc:
        await bg_service.fail_task(task["task_id"], error={"message": str(exc)})
    finally:
        heartbeat_task.cancel()

async def _heartbeat_loop(self, task_id: str):
    while True:
        await asyncio.sleep(5)
        await bg_service.heartbeat(task_id, worker_id=self.worker_id)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_background_worker.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/opencmo/background/worker.py src/opencmo/background/executors/__init__.py src/opencmo/background/storage.py src/opencmo/background/service.py tests/test_background_worker.py
git commit -m "feat: add unified background worker runtime"
```

### Task 4: Migrate Scan Tasks To The Unified Runtime

**Files:**
- Create: `src/opencmo/background/executors/scan.py`
- Modify: `src/opencmo/web/routers/monitors.py`
- Modify: `src/opencmo/web/routers/tasks.py`
- Modify: `src/opencmo/web/routers/events.py`
- Modify: `tests/test_web.py`

- [ ] **Step 1: Write the failing API tests for unified scan task creation**

```python
def test_api_v1_run_monitor_returns_unified_task_shape(client):
    pid = _seed_project("Tasked", "https://tasked.test")
    monitor_id = asyncio.run(storage.add_scheduled_job(pid, "full", "0 9 * * *"))

    resp = client.post(f"/api/v1/monitors/{monitor_id}/run")
    assert resp.status_code == 202

    payload = resp.json()
    assert payload["kind"] == "scan"
    assert payload["status"] == "queued"
    assert payload["project_id"] == pid
    assert "task_id" in payload
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_web.py::test_api_v1_run_monitor_returns_unified_task_shape -q`
Expected: FAIL because the monitor route still returns `task_registry` data.

- [ ] **Step 3: Implement the scan executor**

```python
# src/opencmo/background/executors/scan.py
from __future__ import annotations

import asyncio

from opencmo import storage
from opencmo.monitoring import run_monitoring_workflow


async def run_scan_executor(ctx):
    payload = ctx.task["payload"]

    await ctx.emit(
        phase="queue",
        status="running",
        summary="Starting monitoring workflow",
        payload={"kind": "scan"},
    )

    def on_progress(event: dict):
        asyncio.create_task(
            ctx.emit(
                event_type="progress",
                phase=event.get("stage", ""),
                status=event.get("status", ""),
                summary=event.get("summary", ""),
                payload=event,
            )
        )

    result = await run_monitoring_workflow(
        ctx.task["task_id"],
        payload["project_id"],
        payload["monitor_id"],
        payload["job_type"],
        payload["job_id"],
        analyze_url=payload.get("analyze_url"),
        locale=payload.get("locale", "en"),
        on_progress=on_progress,
    )
    await ctx.complete(result)
```

- [ ] **Step 4: Replace scan task creation and scan event reading**

```python
# src/opencmo/web/routers/monitors.py
from opencmo.background import service as bg_service

task = await bg_service.enqueue_task(
    kind="scan",
    project_id=result["project_id"],
    payload={
        "monitor_id": result["monitor_id"],
        "project_id": result["project_id"],
        "job_type": job_type,
        "job_id": result["monitor_id"],
        "analyze_url": url,
        "locale": locale,
    },
    dedupe_key=f"scan:monitor:{result['monitor_id']}",
)
result["task_id"] = task["task_id"]
```

```python
# src/opencmo/web/routers/events.py
events = await bg_service.list_events(task_id, after_event_id=cursor)
for event in events:
    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_web.py::test_api_v1_run_monitor_returns_unified_task_shape -q`
Expected: PASS

Run: `pytest tests/test_web.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/opencmo/background/executors/scan.py src/opencmo/web/routers/monitors.py src/opencmo/web/routers/tasks.py src/opencmo/web/routers/events.py tests/test_web.py
git commit -m "feat: migrate scan tasks to unified runtime"
```

### Task 5: Migrate Report Tasks To The Unified Runtime

**Files:**
- Create: `src/opencmo/background/executors/report.py`
- Modify: `src/opencmo/web/routers/report.py`
- Modify: `frontend/src/components/project/PipelineProgress.tsx`
- Modify: `tests/test_web.py`

- [ ] **Step 1: Write the failing report task API test**

```python
def test_api_v1_regenerate_report_returns_unified_task(client):
    pid = _seed_project("Reportable", "https://reportable.test")

    resp = client.post(f"/api/v1/projects/{pid}/reports/strategic/regenerate")
    assert resp.status_code == 200
    payload = resp.json()

    assert payload["kind"] == "report"
    assert payload["status"] == "queued"
    assert payload["project_id"] == pid
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_web.py::test_api_v1_regenerate_report_returns_unified_task -q`
Expected: FAIL because the route still uses `report_tasks`.

- [ ] **Step 3: Implement the report executor**

```python
# src/opencmo/background/executors/report.py
from __future__ import annotations

import asyncio

from opencmo import service


async def run_report_executor(ctx):
    payload = ctx.task["payload"]

    def on_progress(event: dict):
        asyncio.create_task(
            ctx.emit(
                event_type="progress",
                phase=event.get("phase", ""),
                status=event.get("status", ""),
                summary=event.get("message", ""),
                payload=event,
            )
        )

    result = await service.regenerate_project_report(
        payload["project_id"],
        payload["report_kind"],
        on_progress=on_progress,
    )
    await ctx.complete(
        {
            "project_id": payload["project_id"],
            "report_kind": payload["report_kind"],
            "human_generation_status": result["human"]["generation_status"],
            "agent_generation_status": result["agent"]["generation_status"],
        }
    )
```

- [ ] **Step 4: Replace `report_tasks` runtime usage**

```python
# src/opencmo/web/routers/report.py
from opencmo.background import service as bg_service

task = await bg_service.enqueue_task(
    kind="report",
    project_id=project_id,
    payload={"project_id": project_id, "report_kind": kind},
    dedupe_key=f"report:project:{project_id}:{kind}",
)

return JSONResponse({
    "task_id": task["task_id"],
    "project_id": project_id,
    "kind": "report",
    "status": task["status"],
})
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_web.py::test_api_v1_regenerate_report_returns_unified_task -q`
Expected: PASS

Run: `pytest tests/test_report_pipeline.py tests/test_reports.py tests/test_web.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/opencmo/background/executors/report.py src/opencmo/web/routers/report.py frontend/src/components/project/PipelineProgress.tsx tests/test_web.py
git commit -m "feat: migrate report tasks to unified runtime"
```

### Task 6: Migrate Graph Expansion To The Unified Runtime

**Files:**
- Create: `src/opencmo/background/executors/graph_expansion.py`
- Modify: `src/opencmo/web/routers/graph.py`
- Modify: `src/opencmo/web/app.py`
- Modify: `src/opencmo/storage/graph.py`
- Modify: `tests/test_web.py`

- [ ] **Step 1: Write the failing graph expansion task test**

```python
def test_api_v1_expansion_start_returns_task_id(client):
    pid = _seed_project("Graphy", "https://graphy.test")

    resp = client.post(f"/api/v1/projects/{pid}/expansion/start")
    assert resp.status_code == 202
    payload = resp.json()

    assert payload["kind"] == "graph_expansion"
    assert payload["project_id"] == pid
    assert payload["status"] == "queued"
    assert "task_id" in payload
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_web.py::test_api_v1_expansion_start_returns_task_id -q`
Expected: FAIL because the graph router still creates in-memory tasks.

- [ ] **Step 3: Implement the graph expansion executor**

```python
# src/opencmo/background/executors/graph_expansion.py
from __future__ import annotations

import asyncio

from opencmo import storage
from opencmo.graph_expansion import run_expansion


async def run_graph_expansion_executor(ctx):
    payload = ctx.task["payload"]
    project_id = payload["project_id"]

    def on_progress(event: dict):
        asyncio.create_task(
            ctx.emit(
                event_type="progress",
                phase=event.get("stage", ""),
                status=event.get("status", ""),
                summary=event.get("summary", ""),
                payload=event,
            )
        )

    await storage.update_expansion(project_id, desired_state="running")
    await run_expansion(project_id, on_progress=on_progress)
    expansion = await storage.get_expansion(project_id)
    await ctx.complete(
        {
            "project_id": project_id,
            "current_wave": expansion["current_wave"],
            "nodes_discovered": expansion["nodes_discovered"],
            "nodes_explored": expansion["nodes_explored"],
            "runtime_state": expansion["runtime_state"],
        }
    )
```

- [ ] **Step 4: Remove in-memory expansion runtime ownership**

```python
# src/opencmo/web/routers/graph.py
from opencmo.background import service as bg_service

task = await bg_service.enqueue_task(
    kind="graph_expansion",
    project_id=project_id,
    payload={"project_id": project_id, "resume": True},
    dedupe_key=f"graph:project:{project_id}",
)
return JSONResponse(
    {"task_id": task["task_id"], "project_id": project_id, "kind": "graph_expansion", "status": task["status"]},
    status_code=202,
)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_web.py::test_api_v1_expansion_start_returns_task_id -q`
Expected: PASS

Run: `pytest tests/test_web.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/opencmo/background/executors/graph_expansion.py src/opencmo/web/routers/graph.py src/opencmo/web/app.py src/opencmo/storage/graph.py tests/test_web.py
git commit -m "feat: migrate graph expansion to unified runtime"
```

### Task 7: Move Frontend And Compatibility Endpoints To Unified Task Reads

**Files:**
- Modify: `frontend/src/api/tasks.ts`
- Modify: `frontend/src/hooks/useTaskEvents.ts`
- Modify: `frontend/src/api/graph.ts`
- Modify: `frontend/src/components/common/TaskProgress.tsx`
- Modify: `frontend/src/components/project/PipelineProgress.tsx`
- Modify: `src/opencmo/web/routers/tasks.py`
- Modify: `src/opencmo/web/routers/events.py`

- [ ] **Step 1: Write the failing frontend-compatible API test**

```python
def test_api_v1_task_detail_reads_unified_background_task(client):
    pid = _seed_project("Front", "https://front.test")
    task = asyncio.run(
        bg_service.enqueue_task(
            kind="report",
            project_id=pid,
            payload={"project_id": pid, "report_kind": "strategic"},
            dedupe_key=f"report:project:{pid}:strategic",
        )
    )

    resp = client.get(f"/api/v1/tasks/{task['task_id']}")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["task_id"] == task["task_id"]
    assert payload["kind"] == "report"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_web.py::test_api_v1_task_detail_reads_unified_background_task -q`
Expected: FAIL because `/tasks/{task_id}` still reads `task_registry`.

- [ ] **Step 3: Switch task detail and SSE reads to unified runtime**

```python
# src/opencmo/web/routers/tasks.py
from opencmo.background import service as bg_service

task = await bg_service.get_task(task_id)
if task is None:
    return JSONResponse({"error": "Not found"}, status_code=404)
return JSONResponse(task)
```

```python
# frontend/src/hooks/useTaskEvents.ts
export interface TaskEvent {
  event_type?: "progress" | "log" | "state_change" | "result";
  type?: "progress" | "done" | "error";
  phase?: string;
  stage?: string;
  status?: string;
  summary?: string;
  payload?: Record<string, unknown>;
  error?: string | null;
}
```

- [ ] **Step 4: Keep compatibility payload mapping while migrating**

```python
# src/opencmo/web/routers/events.py
done_payload = {
    "type": "done",
    "event_type": "state_change",
    "status": task["status"],
    "summary": task["result"].get("summary", ""),
    "payload": task["result"],
    "error": task["error"].get("message") if task["error"] else None,
}
yield f"data: {json.dumps(done_payload, ensure_ascii=False)}\n\n"
```

- [ ] **Step 5: Run tests and build**

Run: `pytest tests/test_web.py -q`
Expected: PASS

Run: `cd frontend && npm run build`
Expected: Vite build succeeds

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api/tasks.ts frontend/src/hooks/useTaskEvents.ts frontend/src/api/graph.ts frontend/src/components/common/TaskProgress.tsx frontend/src/components/project/PipelineProgress.tsx src/opencmo/web/routers/tasks.py src/opencmo/web/routers/events.py tests/test_web.py
git commit -m "feat: unify frontend task progress consumption"
```

### Task 8: Remove Legacy Runtime State And Wire Startup Recovery

**Files:**
- Modify: `src/opencmo/web/app.py`
- Delete: `src/opencmo/web/task_registry.py`
- Modify: `src/opencmo/web/routers/monitors.py`
- Modify: `src/opencmo/web/routers/report.py`
- Modify: `src/opencmo/web/routers/graph.py`
- Modify: `tests/test_web.py`
- Modify: `tests/test_background_worker.py`

- [ ] **Step 1: Write the failing cleanup test**

```python
@pytest.mark.asyncio
async def test_startup_recovery_requeues_stale_claimed_task(tmp_path, monkeypatch):
    from opencmo import storage
    from opencmo.background import storage as bg_storage, service as bg_service

    db_path = tmp_path / "test.db"
    monkeypatch.setattr(storage, "_DB_PATH", db_path, raising=False)
    await storage.ensure_db()

    await bg_storage.insert_task(
        task_id="stale-task",
        kind="scan",
        project_id=1,
        payload={"monitor_id": 1},
        dedupe_key="scan:monitor:1",
        priority=50,
        max_attempts=3,
    )
    await bg_storage.force_claim_for_test("stale-task", worker_id="dead-worker", heartbeat_age_seconds=300)

    fixed = await bg_service.recover_stale_tasks(stale_after_seconds=60)
    task = await bg_service.get_task("stale-task")

    assert fixed == 1
    assert task["status"] == "queued"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_background_worker.py::test_startup_recovery_requeues_stale_claimed_task -q`
Expected: FAIL until startup recovery helpers are fully wired.

- [ ] **Step 3: Start and stop the unified worker in app lifecycle**

```python
# src/opencmo/web/app.py
from opencmo.background.worker import get_background_worker
from opencmo.background import service as bg_service

@app.on_event("startup")
async def _startup_background_runtime():
    await bg_service.recover_stale_tasks(stale_after_seconds=90)
    worker = get_background_worker()
    await worker.start()

@app.on_event("shutdown")
async def _shutdown_background_runtime():
    worker = get_background_worker()
    await worker.stop()
```

- [ ] **Step 4: Delete the legacy registry and remove direct task creation**

```bash
rm src/opencmo/web/task_registry.py
```

```python
# all routers
# remove imports of task_registry, _active_report_tasks, _expansion_tasks, _expansion_progress
# use bg_service and unified event reads instead
```

- [ ] **Step 5: Run full regression**

Run: `pytest tests/test_background_storage.py tests/test_background_service.py tests/test_background_worker.py tests/test_report_pipeline.py tests/test_reports.py tests/test_scheduler.py tests/test_web.py -q`
Expected: PASS

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/opencmo/web/app.py src/opencmo/web/routers/monitors.py src/opencmo/web/routers/report.py src/opencmo/web/routers/graph.py tests/test_background_worker.py tests/test_web.py
git rm src/opencmo/web/task_registry.py
git commit -m "refactor: remove legacy background task runtime"
```

## Self-Review

### Spec coverage

- unified task table: covered in Task 1
- unified task event table: covered in Task 1
- service lifecycle and dedupe: covered in Task 2
- worker claim, heartbeat, recovery: covered in Task 3 and Task 8
- scan executor migration: covered in Task 4
- report executor migration: covered in Task 5
- graph expansion executor migration: covered in Task 6
- unified task/event API consumption: covered in Task 7
- removal of legacy runtime globals: covered in Task 8

### Placeholder scan

- No `TODO`, `TBD`, or “implement later” placeholders remain.
- Each task includes exact file paths, test commands, and commit commands.

### Type consistency

- Unified task kinds are consistently `scan`, `report`, and `graph_expansion`.
- Status model is consistently based on `queued`, `claimed`, `running`, `cancel_requested`, `completed`, `failed`, and `cancelled`.
- Executors are consistently described as operating on the unified runtime context rather than direct router-owned state.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-02-unified-background-task-runtime.md`.

Given the instruction to proceed without pausing for another decision, execute this plan inline in the current session using the `superpowers:executing-plans` workflow, with checkpoints after each task-level commit.
