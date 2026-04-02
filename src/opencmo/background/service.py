"""High-level lifecycle service for unified background tasks."""

from __future__ import annotations

import uuid

from opencmo.background import storage as bg_storage


async def enqueue_task(
    *,
    kind: str,
    project_id: int | None,
    payload: dict,
    dedupe_key: str | None,
    priority: int = 50,
    max_attempts: int = 3,
    run_after: str | None = None,
) -> dict:
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
        run_after=run_after,
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


async def list_tasks(*, kind: str | None = None, limit: int = 100) -> list[dict]:
    return await bg_storage.list_tasks(kind=kind, limit=limit)


async def list_task_events(task_id: str) -> list[dict]:
    return await bg_storage.list_task_events(task_id)


async def find_active_task_by_dedupe_key(dedupe_key: str) -> dict | None:
    return await bg_storage.find_active_task_by_dedupe_key(dedupe_key)


async def claim_next_task(*, worker_id: str) -> dict | None:
    return await bg_storage.claim_next_queued_task(worker_id=worker_id)


async def mark_task_running(task_id: str, *, worker_id: str) -> None:
    await bg_storage.mark_task_running(task_id, worker_id=worker_id)
    await bg_storage.append_task_event(
        task_id,
        event_type="state_change",
        status="running",
        summary="Task started",
    )


async def heartbeat(task_id: str, *, worker_id: str) -> None:
    await bg_storage.heartbeat(task_id, worker_id=worker_id)


async def append_event(
    task_id: str,
    *,
    event_type: str,
    phase: str = "",
    status: str = "",
    summary: str = "",
    payload: dict | None = None,
) -> int:
    return await bg_storage.append_task_event(
        task_id,
        event_type=event_type,
        phase=phase,
        status=status,
        summary=summary,
        payload=payload,
    )


async def request_cancel(task_id: str) -> bool:
    task = await bg_storage.get_task(task_id)
    if task is None or task["status"] in {"completed", "failed", "cancelled"}:
        return False

    await bg_storage.update_task_status(task_id, "cancel_requested")
    await bg_storage.append_task_event(
        task_id,
        event_type="state_change",
        status="cancel_requested",
        summary="Cancellation requested",
    )
    return True


async def complete_task(task_id: str, *, result: dict | None = None) -> None:
    await bg_storage.complete_task(task_id, result=result or {})
    await bg_storage.append_task_event(
        task_id,
        event_type="state_change",
        status="completed",
        summary="Task completed",
        payload=result or {},
    )


async def fail_task(task_id: str, *, error: dict) -> None:
    await bg_storage.fail_task(task_id, error=error)
    await bg_storage.append_task_event(
        task_id,
        event_type="state_change",
        status="failed",
        summary=error.get("message", "Task failed"),
        payload=error,
    )


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
            await fail_task(
                task["task_id"],
                error={"message": "Task exceeded max attempts after stale heartbeat"},
            )
        fixed += 1
    return fixed
