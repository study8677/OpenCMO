"""Report API router."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from opencmo import storage
from opencmo.background import service as bg_service
from opencmo.background.types import ACTIVE_STATUSES
from opencmo.web.routers.tasks import serialize_background_task

router = APIRouter(prefix="/api/v1")


def _compat_status(status: str) -> str:
    if status in {"queued", "claimed"}:
        return "pending"
    if status == "cancel_requested":
        return "running"
    if status == "cancelled":
        return "failed"
    return status


def _progress_from_events(events: list[dict]) -> list[dict]:
    progress: list[dict] = []
    for event in events:
        if event["event_type"] != "progress":
            continue
        payload = event["payload"] or {}
        if payload:
            progress.append(payload)
            continue
        progress.append(
            {
                "phase": event["phase"],
                "status": event["status"],
                "summary": event["summary"],
            }
        )
    return progress


async def _wait_for_project_report_tasks(project_id: int, timeout_seconds: float = 30.0) -> None:
    deadline = asyncio.get_event_loop().time() + timeout_seconds
    while True:
        tasks = await bg_service.list_tasks(kind="report", limit=200)
        active = [
            task for task in tasks
            if task["project_id"] == project_id and task["status"] in ACTIVE_STATUSES
        ]
        if not active or asyncio.get_event_loop().time() >= deadline:
            return
        await asyncio.sleep(0.1)


@router.get("/projects/{project_id}/reports")
async def api_v1_reports(project_id: int, kind: str | None = None, audience: str | None = None):
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse(await storage.list_reports(project_id, kind=kind, audience=audience))


@router.get("/projects/{project_id}/reports/latest")
async def api_v1_latest_reports(project_id: int):
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)
    await _wait_for_project_report_tasks(project_id)
    return JSONResponse(await storage.get_latest_reports(project_id))


@router.get("/reports/{report_id}")
async def api_v1_report_detail(report_id: int):
    report = await storage.get_report(report_id)
    if not report:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse(report)


@router.post("/projects/{project_id}/reports/{kind}/regenerate")
async def api_v1_regenerate_report(project_id: int, kind: str):
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)

    task = await bg_service.enqueue_task(
        kind="report",
        project_id=project_id,
        payload={"project_id": project_id, "kind": kind},
        dedupe_key=f"report:project:{project_id}:{kind}",
    )

    return JSONResponse({
        "task_id": task["task_id"],
        "project_id": project_id,
        "kind": kind,
        "status": "pending",
    })


@router.get("/reports/tasks/{task_id}")
async def api_v1_report_task(task_id: str):
    """Get the status and progress of a report generation task."""
    task = await bg_service.get_task(task_id)
    if task and task["kind"] == "report":
        detail = await serialize_background_task(task)
        return JSONResponse(
            {
                "task_id": detail["task_id"],
                "project_id": detail["project_id"],
                "kind": detail["report_kind"],
                "status": detail["status"],
                "progress": detail["progress"],
                "error": detail["error"],
                "created_at": detail["created_at"],
                "completed_at": detail["completed_at"],
            }
        )
    if not task:
        return JSONResponse({"error": "Task not found"}, status_code=404)
    return JSONResponse({"error": "Task not found"}, status_code=404)


@router.post("/projects/{project_id}/report")
async def api_v1_report(project_id: int):
    from opencmo import service
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)
    result = await service.send_project_report(project_id)
    if result["ok"]:
        return JSONResponse(result)
    return JSONResponse(result, status_code=500)
