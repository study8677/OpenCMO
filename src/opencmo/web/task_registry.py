"""In-memory task registry for tracking async scan jobs.

Pure memory state — intentionally not persisted.
"""

from __future__ import annotations

import asyncio
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime

MAX_TASKS = 100


@dataclass
class TaskRecord:
    task_id: str
    monitor_id: int
    project_id: int
    job_type: str
    status: str = "pending"  # pending | running | completed | failed
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str | None = None
    error: str | None = None
    progress: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "monitor_id": self.monitor_id,
            "project_id": self.project_id,
            "job_type": self.job_type,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "progress": self.progress,
        }


_tasks: OrderedDict[str, TaskRecord] = OrderedDict()
_active_monitors: dict[int, str] = {}  # monitor_id → task_id


async def _run_and_update(
    record: TaskRecord, project_id: int, job_type: str, monitor_id: int, job_id: int,
    *, analyze_url: str | None = None,
) -> None:
    record.status = "running"
    try:
        # If URL provided, run AI analysis first to enrich project metadata + keywords
        if analyze_url:
            from opencmo.service import analyze_and_enrich_project

            def on_progress(role: str, content: str, round_num: int):
                record.progress.append({
                    "role": role,
                    "content": content,
                    "round": round_num,
                })

            await analyze_and_enrich_project(project_id, analyze_url, on_progress=on_progress)

        from opencmo.scheduler import run_scheduled_scan

        await run_scheduled_scan(project_id, job_type, job_id, triggered_by="manual")
        record.status = "completed"
    except Exception as e:
        record.status = "failed"
        record.error = str(e)
    finally:
        record.completed_at = datetime.now().isoformat()
        _active_monitors.pop(monitor_id, None)


def submit_scan(
    monitor_id: int, project_id: int, job_type: str, job_id: int,
    *, analyze_url: str | None = None,
) -> TaskRecord | None:
    """Submit an async scan task. Returns None if monitor already running (409).

    If analyze_url is provided, AI analysis runs first to extract brand/category/keywords
    before the scan begins.
    """
    if monitor_id in _active_monitors:
        return None

    task_id = uuid.uuid4().hex[:8]
    record = TaskRecord(
        task_id=task_id,
        monitor_id=monitor_id,
        project_id=project_id,
        job_type=job_type,
    )
    _tasks[task_id] = record
    _active_monitors[monitor_id] = task_id

    # LRU eviction
    while len(_tasks) > MAX_TASKS:
        _tasks.popitem(last=False)

    asyncio.get_event_loop().create_task(
        _run_and_update(
            record, project_id, job_type, monitor_id, job_id,
            analyze_url=analyze_url,
        )
    )
    return record


def get_task(task_id: str) -> TaskRecord | None:
    return _tasks.get(task_id)


def list_tasks() -> list[TaskRecord]:
    return list(reversed(_tasks.values()))


def is_monitor_active(monitor_id: int) -> bool:
    return monitor_id in _active_monitors


def clear_all() -> None:
    """Clear all tasks (for testing)."""
    _tasks.clear()
    _active_monitors.clear()
