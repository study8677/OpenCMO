"""Storage helpers for unified background tasks and events."""

from __future__ import annotations

import contextlib
import json
from datetime import datetime, timedelta, timezone

from opencmo.background.types import ACTIVE_STATUSES
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


def _event_row_to_dict(row) -> dict:
    return {
        "id": row[0],
        "task_id": row[1],
        "event_type": row[2],
        "phase": row[3],
        "status": row[4],
        "summary": row[5],
        "payload": json.loads(row[6] or "{}"),
        "created_at": row[7],
    }


async def insert_task(
    *,
    task_id: str,
    kind: str,
    project_id: int | None,
    payload: dict,
    dedupe_key: str | None,
    priority: int,
    max_attempts: int,
    run_after: str | None = None,
) -> None:
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO background_tasks
               (task_id, kind, project_id, payload_json, dedupe_key, priority, max_attempts, run_after)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (task_id, kind, project_id, json.dumps(payload), dedupe_key, priority, max_attempts, run_after),
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


async def list_tasks(*, kind: str | None = None, limit: int = 100) -> list[dict]:
    db = await get_db()
    try:
        if kind:
            cursor = await db.execute(
                """SELECT id, task_id, kind, project_id, status, payload_json, result_json,
                          error_json, dedupe_key, priority, run_after, attempt_count,
                          max_attempts, worker_id, claimed_at, heartbeat_at, started_at,
                          completed_at, created_at, updated_at
                   FROM background_tasks
                   WHERE kind = ?
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (kind, limit),
            )
        else:
            cursor = await db.execute(
                """SELECT id, task_id, kind, project_id, status, payload_json, result_json,
                          error_json, dedupe_key, priority, run_after, attempt_count,
                          max_attempts, worker_id, claimed_at, heartbeat_at, started_at,
                          completed_at, created_at, updated_at
                   FROM background_tasks
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (limit,),
            )
        rows = await cursor.fetchall()
        return [_task_row_to_dict(row) for row in rows]
    finally:
        await db.close()


async def append_task_event(
    task_id: str,
    *,
    event_type: str,
    phase: str = "",
    status: str = "",
    summary: str = "",
    payload: dict | None = None,
) -> int:
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


async def list_task_events(task_id: str) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, task_id, event_type, phase, status, summary, payload_json, created_at
               FROM background_task_events
               WHERE task_id = ?
               ORDER BY id ASC""",
            (task_id,),
        )
        rows = await cursor.fetchall()
        return [_event_row_to_dict(row) for row in rows]
    finally:
        await db.close()


async def find_active_task_by_dedupe_key(dedupe_key: str) -> dict | None:
    placeholders = ", ".join("?" for _ in ACTIVE_STATUSES)
    db = await get_db()
    try:
        cursor = await db.execute(
            f"""SELECT id, task_id, kind, project_id, status, payload_json, result_json,
                       error_json, dedupe_key, priority, run_after, attempt_count,
                       max_attempts, worker_id, claimed_at, heartbeat_at, started_at,
                       completed_at, created_at, updated_at
                FROM background_tasks
                WHERE dedupe_key = ? AND status IN ({placeholders})
                ORDER BY created_at DESC
                LIMIT 1""",
            (dedupe_key, *ACTIVE_STATUSES),
        )
        row = await cursor.fetchone()
        return _task_row_to_dict(row) if row else None
    finally:
        await db.close()


async def update_task_status(task_id: str, status: str) -> None:
    db = await get_db()
    try:
        await db.execute(
            "UPDATE background_tasks SET status = ?, updated_at = datetime('now') WHERE task_id = ?",
            (status, task_id),
        )
        await db.commit()
    finally:
        await db.close()


async def complete_task(task_id: str, *, result: dict) -> None:
    db = await get_db()
    try:
        await db.execute(
            """UPDATE background_tasks
               SET status = 'completed',
                   result_json = ?,
                   completed_at = datetime('now'),
                   updated_at = datetime('now')
               WHERE task_id = ?""",
            (json.dumps(result), task_id),
        )
        await db.commit()
    finally:
        await db.close()


async def fail_task(task_id: str, *, error: dict) -> None:
    db = await get_db()
    try:
        await db.execute(
            """UPDATE background_tasks
               SET status = 'failed',
                   error_json = ?,
                   completed_at = datetime('now'),
                   updated_at = datetime('now')
               WHERE task_id = ?""",
            (json.dumps(error), task_id),
        )
        await db.commit()
    finally:
        await db.close()


async def requeue_task(task_id: str) -> None:
    db = await get_db()
    try:
        await db.execute(
            """UPDATE background_tasks
               SET status = 'queued',
                   worker_id = NULL,
                   claimed_at = NULL,
                   heartbeat_at = NULL,
                   started_at = NULL,
                   attempt_count = attempt_count + 1,
                   updated_at = datetime('now')
               WHERE task_id = ?""",
            (task_id,),
        )
        await db.commit()
    finally:
        await db.close()


async def list_stale_tasks(*, stale_after_seconds: int) -> list[dict]:
    cutoff = (
        datetime.now(timezone.utc) - timedelta(seconds=stale_after_seconds)
    ).strftime("%Y-%m-%d %H:%M:%S")
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, task_id, kind, project_id, status, payload_json, result_json,
                      error_json, dedupe_key, priority, run_after, attempt_count,
                      max_attempts, worker_id, claimed_at, heartbeat_at, started_at,
                      completed_at, created_at, updated_at
               FROM background_tasks
               WHERE status IN ('claimed', 'running')
                 AND heartbeat_at IS NOT NULL
                 AND heartbeat_at < ?""",
            (cutoff,),
        )
        rows = await cursor.fetchall()
        return [_task_row_to_dict(row) for row in rows]
    finally:
        await db.close()


async def claim_next_queued_task(*, worker_id: str) -> dict | None:
    db = await get_db()
    try:
        # Use BEGIN IMMEDIATE for atomic SELECT+UPDATE — prevents concurrent
        # workers from claiming the same task (SQLite serialises IMMEDIATE txns).
        await db.execute("BEGIN IMMEDIATE")
        cursor = await db.execute(
            """SELECT id, task_id, kind, project_id, status, payload_json, result_json,
                      error_json, dedupe_key, priority, run_after, attempt_count,
                      max_attempts, worker_id, claimed_at, heartbeat_at, started_at,
                      completed_at, created_at, updated_at
               FROM background_tasks
               WHERE status = 'queued'
                 AND (run_after IS NULL OR run_after <= datetime('now'))
               ORDER BY priority DESC, created_at ASC
               LIMIT 1""",
        )
        row = await cursor.fetchone()
        if row is None:
            await db.execute("COMMIT")
            return None

        task = _task_row_to_dict(row)
        await db.execute(
            """UPDATE background_tasks
               SET status = 'claimed',
                   worker_id = ?,
                   claimed_at = datetime('now'),
                   heartbeat_at = datetime('now'),
                   updated_at = datetime('now')
               WHERE task_id = ?""",
            (worker_id, task["task_id"]),
        )
        await db.execute("COMMIT")
        return await get_task(task["task_id"])
    except Exception:
        with contextlib.suppress(Exception):
            await db.execute("ROLLBACK")
        raise
    finally:
        await db.close()


async def mark_task_running(task_id: str, *, worker_id: str) -> None:
    db = await get_db()
    try:
        await db.execute(
            """UPDATE background_tasks
               SET status = 'running',
                   worker_id = ?,
                   started_at = COALESCE(started_at, datetime('now')),
                   heartbeat_at = datetime('now'),
                   updated_at = datetime('now')
               WHERE task_id = ?""",
            (worker_id, task_id),
        )
        await db.commit()
    finally:
        await db.close()


async def heartbeat(task_id: str, *, worker_id: str) -> None:
    db = await get_db()
    try:
        await db.execute(
            """UPDATE background_tasks
               SET heartbeat_at = datetime('now'),
                   worker_id = ?,
                   updated_at = datetime('now')
               WHERE task_id = ?""",
            (worker_id, task_id),
        )
        await db.commit()
    finally:
        await db.close()
