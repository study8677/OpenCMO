"""Report API router."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from opencmo import storage

router = APIRouter(prefix="/api/v1")


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
    return JSONResponse(await storage.get_latest_reports(project_id))


@router.get("/reports/{report_id}")
async def api_v1_report_detail(report_id: int):
    report = await storage.get_report(report_id)
    if not report:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse(report)


@router.post("/projects/{project_id}/reports/{kind}/regenerate")
async def api_v1_regenerate_report(project_id: int, kind: str):
    from opencmo import service

    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)
    try:
        result = await service.regenerate_project_report(project_id, kind)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    return JSONResponse(result)


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
