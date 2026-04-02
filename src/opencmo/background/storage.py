"""Storage helpers for unified background tasks and events."""

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
) -> None:
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
