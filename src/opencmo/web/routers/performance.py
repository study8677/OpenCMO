"""Performance API router."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from opencmo import storage
from opencmo.tools.performance_tracker import (
    add_manual_tracking,
    collect_approval_metrics,
    delete_manual_tracking,
    get_project_performance,
    list_manual_tracking,
)

router = APIRouter(prefix="/api/v1")


@router.get("/projects/{project_id}/performance")
async def api_v1_performance(project_id: int):
    """Get all published content performance for a project."""
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)

    approvals = await get_project_performance(project_id)
    manual = await list_manual_tracking(project_id)

    # Compute summary stats
    total_likes = 0
    total_comments = 0
    total_retweets = 0
    for item in approvals:
        m = item.get("post_metrics") or {}
        total_likes += m.get("score", 0) + m.get("like_count", 0)
        total_comments += m.get("num_comments", 0) + m.get("reply_count", 0)
        total_retweets += m.get("retweet_count", 0)

    return JSONResponse({
        "summary": {
            "total_published": len(approvals),
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_retweets": total_retweets,
        },
        "approvals": approvals,
        "manual": manual,
    })


@router.post("/approvals/{approval_id}/refresh-metrics")
async def api_v1_refresh_metrics(approval_id: int):
    """Manually trigger metrics refresh for a published approval."""
    metrics = await collect_approval_metrics(approval_id)
    if metrics is None:
        return JSONResponse({"error": "Could not fetch metrics"}, status_code=400)
    return JSONResponse({"ok": True, "metrics": metrics})


@router.post("/projects/{project_id}/manual-tracking")
async def api_v1_add_manual_tracking(project_id: int, request: Request):
    """Add a manually tracked external URL."""
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Project not found"}, status_code=404)
    body = await request.json()
    url = str(body.get("url", "")).strip()
    if not url:
        return JSONResponse({"error": "url is required"}, status_code=400)
    tracking_id = await add_manual_tracking(
        project_id,
        platform=str(body.get("platform", "other")).strip(),
        url=url,
        title=str(body.get("title", "")).strip(),
        notes=str(body.get("notes", "")).strip(),
    )
    return JSONResponse({"ok": True, "id": tracking_id}, status_code=201)


@router.delete("/manual-tracking/{tracking_id}")
async def api_v1_delete_manual_tracking(tracking_id: int):
    """Delete a manually tracked item."""
    ok = await delete_manual_tracking(tracking_id)
    if not ok:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse({"ok": True})
