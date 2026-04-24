"""Blog generation API router."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from opencmo import storage
from opencmo.background import service as bg_service

router = APIRouter(prefix="/api/v1")


@router.post("/projects/{project_id}/blog/generate")
async def api_v1_generate_blog(project_id: int, request: Request):
    """Start a promotional blog generation task for a project."""
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)

    body = await request.json()
    style = body.get("style", "launch")
    bilingual = body.get("bilingual", False)

    valid_styles = {"launch", "case_study", "comparison", "thought_leadership"}
    if style not in valid_styles:
        return JSONResponse(
            {"error": f"Invalid style. Must be one of: {', '.join(sorted(valid_styles))}"},
            status_code=400,
        )

    # Capture BYOK keys from the current request context
    from opencmo import llm
    payload: dict = {
        "project_id": project_id,
        "style": style,
        "bilingual": bilingual,
    }
    request_keys = llm.get_request_keys()
    if request_keys:
        payload["__user_keys"] = request_keys

    # Check for existing active task (same project + style)
    dedupe_key = f"blog_generation:project:{project_id}:{style}"
    existing = await bg_service.find_active_task_by_dedupe_key(dedupe_key)
    if existing is not None:
        return JSONResponse({
            "task_id": existing["task_id"],
            "project_id": project_id,
            "style": style,
            "status": "already_running",
        }, status_code=409)

    task = await bg_service.enqueue_task(
        kind="blog_generation",
        project_id=project_id,
        payload=payload,
        dedupe_key=dedupe_key,
        max_attempts=2,
    )

    return JSONResponse({
        "task_id": task["task_id"],
        "project_id": project_id,
        "style": style,
        "status": "pending",
    }, status_code=202)


@router.get("/projects/{project_id}/blog/drafts")
async def api_v1_blog_drafts(project_id: int):
    """List blog drafts for a project."""
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)

    drafts = await storage.list_blog_drafts(project_id)
    # Strip full content from list view for performance
    for d in drafts:
        if d.get("content") and len(d["content"]) > 500:
            d["content_preview"] = d["content"][:500] + "..."
            del d["content"]
    return JSONResponse(drafts)


@router.get("/blog/drafts/{draft_id}")
async def api_v1_blog_draft_detail(draft_id: int):
    """Get a single blog draft with full content and quality scores."""
    draft = await storage.get_blog_draft(draft_id)
    if not draft:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse(draft)
