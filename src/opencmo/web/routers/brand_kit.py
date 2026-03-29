"""Brand Kit API router."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from opencmo import storage
from opencmo.storage.brand_kit import get_brand_kit, upsert_brand_kit

router = APIRouter(prefix="/api/v1")


@router.get("/projects/{project_id}/brand-kit")
async def api_v1_brand_kit_get(project_id: int):
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Project not found"}, status_code=404)
    kit = await get_brand_kit(project_id)
    if not kit:
        return JSONResponse({
            "project_id": project_id,
            "tone_of_voice": "",
            "target_audience": "",
            "core_values": "",
            "forbidden_words": [],
            "best_examples": "",
            "custom_instructions": "",
            "updated_at": None,
        })
    return JSONResponse(kit)


@router.put("/projects/{project_id}/brand-kit")
async def api_v1_brand_kit_save(project_id: int, request: Request):
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Project not found"}, status_code=404)
    body = await request.json()
    kit = await upsert_brand_kit(
        project_id,
        tone_of_voice=str(body.get("tone_of_voice", "")).strip(),
        target_audience=str(body.get("target_audience", "")).strip(),
        core_values=str(body.get("core_values", "")).strip(),
        forbidden_words=body.get("forbidden_words", []),
        best_examples=str(body.get("best_examples", "")).strip(),
        custom_instructions=str(body.get("custom_instructions", "")).strip(),
    )
    return JSONResponse(kit)
