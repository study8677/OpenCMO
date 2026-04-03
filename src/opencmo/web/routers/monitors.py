"""Monitors API router."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/v1")


async def _enqueue_scan_task(
    *,
    monitor_id: int,
    project_id: int,
    job_type: str,
    job_id: int,
    analyze_url: str | None = None,
    locale: str = "en",
) -> dict:
    from opencmo.background import service as bg_service

    payload = {
        "monitor_id": monitor_id,
        "project_id": project_id,
        "job_type": job_type,
        "job_id": job_id,
        "locale": locale,
    }
    if analyze_url:
        payload["analyze_url"] = analyze_url

    return await bg_service.enqueue_task(
        kind="scan",
        project_id=project_id,
        payload=payload,
        dedupe_key=f"scan:monitor:{monitor_id}",
    )


def _pending_scan_response(task: dict) -> dict:
    payload = task["payload"]
    return {
        "task_id": task["task_id"],
        "monitor_id": payload["monitor_id"],
        "project_id": task["project_id"],
        "job_type": payload["job_type"],
        "status": "pending",
        "created_at": task["created_at"],
        "completed_at": task["completed_at"],
        "error": None,
        "progress": [],
        "run_id": None,
        "summary": "",
        "findings_count": 0,
        "recommendations_count": 0,
    }


@router.get("/monitors")
async def api_v1_monitors():
    from opencmo import service
    return JSONResponse(await service.list_monitors())


@router.post("/monitors")
async def api_v1_create_monitor(request: Request):
    from urllib.parse import urlparse

    from opencmo import service

    body = await request.json()
    url = body.get("url", "").strip()
    if not url:
        return JSONResponse({"error": "url is required"}, status_code=400)
    # Auto-derive brand from URL domain if not provided
    brand = body.get("brand", "").strip()
    if not brand:
        domain = urlparse(url).hostname or ""
        brand = domain.removeprefix("www.").split(".")[0].capitalize() or domain
    category = body.get("category", "").strip() or "auto"
    job_type = body.get("job_type", "full")
    locale = body.get("locale", "en").strip() or "en"
    result = await service.create_monitor(
        brand, url, category,
        job_type=job_type,
        cron_expr=body.get("cron_expr", "0 9 * * *"),
        keywords=body.get("keywords"),
    )
    # Auto-trigger: AI analysis (extract brand/category/keywords) + first scan
    task = await _enqueue_scan_task(
        monitor_id=result["monitor_id"],
        project_id=result["project_id"],
        job_type=job_type,
        job_id=result["monitor_id"],
        analyze_url=url,
        locale=locale,
    )
    if task:
        result["task_id"] = task["task_id"]
    return JSONResponse(result, status_code=201)


@router.delete("/monitors/{monitor_id}")
async def api_v1_delete_monitor(monitor_id: int):
    from opencmo import service
    ok = await service.remove_monitor(monitor_id)
    if not ok:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse({"ok": True})


@router.patch("/monitors/{monitor_id}")
async def api_v1_update_monitor(monitor_id: int, request: Request):
    from opencmo import service

    body = await request.json()
    cron_expr = body.get("cron_expr")
    enabled = body.get("enabled")
    if cron_expr is None and enabled is None:
        return JSONResponse({"error": "Nothing to update"}, status_code=400)
    ok = await service.update_monitor(monitor_id, cron_expr=cron_expr, enabled=enabled)
    if not ok:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse({"ok": True})


@router.post("/monitors/{monitor_id}/run")
async def api_v1_run_monitor(monitor_id: int):
    from opencmo import service
    from opencmo.background import service as bg_service

    job = await service.get_monitor(monitor_id)
    if not job:
        return JSONResponse({"error": "Monitor not found"}, status_code=404)

    existing = await bg_service.find_active_task_by_dedupe_key(f"scan:monitor:{monitor_id}")
    if existing is not None:
        return JSONResponse({"error": "Monitor is already running"}, status_code=409)

    record = await _enqueue_scan_task(
        monitor_id=monitor_id,
        project_id=job["project_id"],
        job_type=job["job_type"],
        job_id=monitor_id,
    )
    return JSONResponse(_pending_scan_response(record), status_code=202)
