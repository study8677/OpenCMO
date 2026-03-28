"""Approvals API router."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from opencmo import storage

router = APIRouter(prefix="/api/v1")


@router.get("/approvals")
async def api_v1_approvals(status: str | None = None, limit: int = 50):
    from opencmo import service

    return JSONResponse(await service.list_approvals(status=status, limit=limit))


@router.get("/approvals/{approval_id}")
async def api_v1_approval(approval_id: int):
    from opencmo import service

    approval = await service.get_approval(approval_id)
    if not approval:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse(approval)


@router.post("/approvals")
async def api_v1_create_approval(request: Request):
    from opencmo import service

    body = await request.json()
    project_id = body.get("project_id")
    if not isinstance(project_id, int):
        return JSONResponse({"error": "project_id is required"}, status_code=400)

    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Project not found"}, status_code=404)

    payload = body.get("payload")
    if not isinstance(payload, dict):
        return JSONResponse({"error": "payload must be an object"}, status_code=400)

    approval_type = str(body.get("approval_type", "")).strip()
    if not approval_type:
        return JSONResponse({"error": "approval_type is required"}, status_code=400)

    try:
        approval = await service.create_approval(
            project_id,
            approval_type,
            payload,
            content=str(body.get("content", "")),
            title=str(body.get("title", "")),
            target_label=str(body.get("target_label", "")),
            target_url=str(body.get("target_url", "")),
            agent_name=str(body.get("agent_name", "")),
        )
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    return JSONResponse(approval, status_code=201)


@router.post("/approvals/{approval_id}/approve")
async def api_v1_approve_approval(approval_id: int, request: Request):
    from opencmo import service

    try:
        body = await request.json()
    except Exception:
        body = {}

    result = await service.approve_approval(
        approval_id,
        decision_note=str(body.get("decision_note", "")),
    )
    if not result["ok"]:
        status_code = 404 if "not found" in result["error"].lower() else 400
        return JSONResponse({
            "error": result["error"],
            "error_code": result.get("error_code"),
            "approval": result.get("approval"),
        }, status_code=status_code)
    return JSONResponse(result["approval"])


@router.post("/approvals/{approval_id}/reject")
async def api_v1_reject_approval(approval_id: int, request: Request):
    from opencmo import service

    try:
        body = await request.json()
    except Exception:
        body = {}

    result = await service.reject_approval(
        approval_id,
        decision_note=str(body.get("decision_note", "")),
    )
    if not result["ok"]:
        status_code = 404 if "not found" in result["error"].lower() else 400
        return JSONResponse({"error": result["error"]}, status_code=status_code)
    return JSONResponse(result["approval"])
