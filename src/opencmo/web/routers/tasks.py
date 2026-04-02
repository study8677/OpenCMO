"""Tasks and scan runs API router."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from opencmo import storage
from opencmo.background import service as bg_service

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
                "stage": event["phase"],
                "status": event["status"],
                "summary": event["summary"],
            }
        )
    return progress


async def _serialize_scan_task(task: dict) -> dict:
    events = await bg_service.list_task_events(task["task_id"])
    payload = task["payload"]
    result = task["result"] or {}
    error = task["error"] or {}
    return {
        "task_id": task["task_id"],
        "task_kind": "scan",
        "monitor_id": payload["monitor_id"],
        "project_id": task["project_id"],
        "job_type": payload["job_type"],
        "status": _compat_status(task["status"]),
        "created_at": task["created_at"],
        "completed_at": task["completed_at"],
        "error": error.get("message"),
        "progress": _progress_from_events(events),
        "run_id": result.get("run_id"),
        "summary": result.get("summary") or error.get("message") or "",
        "findings_count": result.get("findings_count", 0),
        "recommendations_count": result.get("recommendations_count", 0),
    }


async def _serialize_report_task(task: dict) -> dict:
    events = await bg_service.list_task_events(task["task_id"])
    payload = task["payload"]
    result = task["result"] or {}
    error = task["error"] or {}
    return {
        "task_id": task["task_id"],
        "task_kind": "report",
        "report_kind": payload["kind"],
        "project_id": task["project_id"],
        "status": _compat_status(task["status"]),
        "created_at": task["created_at"],
        "completed_at": task["completed_at"],
        "error": error.get("message"),
        "progress": _progress_from_events(events),
        "summary": result.get("summary") or error.get("message") or "",
    }


async def _serialize_graph_task(task: dict) -> dict:
    events = await bg_service.list_task_events(task["task_id"])
    payload = task["payload"]
    result = task["result"] or {}
    error = task["error"] or {}
    return {
        "task_id": task["task_id"],
        "task_kind": "graph_expansion",
        "project_id": task["project_id"],
        "status": _compat_status(task["status"]),
        "created_at": task["created_at"],
        "completed_at": task["completed_at"],
        "error": error.get("message"),
        "progress": _progress_from_events(events),
        "summary": result.get("summary") or error.get("message") or "",
        "runtime_state": result.get("runtime_state"),
        "current_wave": result.get("current_wave"),
        "nodes_discovered": result.get("nodes_discovered"),
        "nodes_explored": result.get("nodes_explored"),
        "graph_project_id": payload["project_id"],
    }


async def serialize_background_task(task: dict) -> dict:
    kind = task["kind"]
    if kind == "scan":
        return await _serialize_scan_task(task)
    if kind == "report":
        return await _serialize_report_task(task)
    if kind == "graph_expansion":
        return await _serialize_graph_task(task)
    raise ValueError(f"Unsupported background task kind: {kind}")


@router.get("/tasks")
async def api_v1_tasks():
    tasks = await bg_service.list_tasks(limit=200)
    return JSONResponse([await serialize_background_task(task) for task in tasks])


@router.get("/tasks/{task_id}")
async def api_v1_task(task_id: str):
    record = await bg_service.get_task(task_id)
    if record is None:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse(await serialize_background_task(record))


@router.get("/tasks/{task_id}/findings")
async def api_v1_task_findings(task_id: str):
    return JSONResponse(await storage.get_task_findings(task_id))


@router.get("/tasks/{task_id}/recommendations")
async def api_v1_task_recommendations(task_id: str):
    return JSONResponse(await storage.get_task_recommendations(task_id))


@router.get("/monitors/{monitor_id}/runs")
async def api_v1_monitor_runs(monitor_id: int):
    return JSONResponse(await storage.list_scan_runs_by_monitor(monitor_id))
