"""Quick Actions API router — one-click content generation from insights."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from opencmo import storage

router = APIRouter(prefix="/api/v1")


@router.get("/projects/{project_id}/action-feed")
async def api_v1_action_feed(project_id: int):
    """Return a prioritized feed of actionable items for this project.

    Combines: unread insights + pending approvals + latest findings.
    Each item has a CTA type so the frontend knows what button to render.
    """
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)

    feed: list[dict] = []

    # 1. Unread insights → "view_data" or "generate_content" CTA
    insights = await storage.list_insights(project_id=project_id, unread_only=True)
    for ins in insights[:5]:
        action_params = ins.get("action_params")
        if isinstance(action_params, str):
            import json
            try:
                action_params = json.loads(action_params)
            except Exception:
                action_params = {}
        cta = "generate_content" if ins.get("action_type") == "api_call" else "view_data"
        feed.append({
            "type": "insight",
            "id": ins["id"],
            "severity": ins.get("severity", "info"),
            "title": ins.get("title", ""),
            "summary": ins.get("summary", ""),
            "cta": cta,
            "action_route": action_params.get("route") if isinstance(action_params, dict) else None,
            "insight_id": ins["id"],
            "created_at": ins.get("created_at", ""),
        })

    # 2. Pending autopilot approvals → "review_approval" CTA
    all_approvals = await storage.list_approvals(status="pending", limit=20)
    project_approvals = [a for a in all_approvals if a.get("project_id") == project_id]
    for appr in project_approvals[:3]:
        feed.append({
            "type": "approval",
            "id": appr["id"],
            "severity": "warning",
            "title": appr.get("title", "Pending approval"),
            "summary": f"{appr.get('channel', '?')} · {appr.get('approval_type', '?')} — ready for review",
            "cta": "review_approval",
            "approval_id": appr["id"],
            "created_at": appr.get("created_at", ""),
        })

    # 3. Recent findings → "view_data" CTA
    try:
        findings = await storage.get_task_findings_by_project(project_id, limit=3)
    except Exception:
        findings = []
    for f in findings:
        feed.append({
            "type": "finding",
            "id": f.get("id", 0),
            "severity": f.get("severity", "info"),
            "title": f.get("title", ""),
            "summary": f.get("summary", ""),
            "cta": "view_data",
            "created_at": f.get("created_at", ""),
        })

    # Sort by severity priority
    sev_order = {"critical": 0, "warning": 1, "info": 2}
    feed.sort(key=lambda x: sev_order.get(x.get("severity", "info"), 99))

    return JSONResponse(feed[:8])


@router.post("/projects/{project_id}/quick-generate")
async def api_v1_quick_generate(project_id: int, request: Request):
    """One-click: generate content from an insight and push to approval queue."""
    body = await request.json()
    insight_id = body.get("insight_id")
    if not insight_id:
        return JSONResponse({"error": "insight_id is required"}, status_code=400)

    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Project not found"}, status_code=404)

    from opencmo.autopilot import execute_autopilot

    # Force-execute autopilot for this project (it already filters for actionable insights)
    results = await execute_autopilot(project_id)

    return JSONResponse({
        "ok": True,
        "generated": len(results),
        "approvals": results,
    })
