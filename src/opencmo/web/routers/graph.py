"""Graph, competitors, and expansion API router."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from opencmo import storage
from opencmo.background import service as bg_service

router = APIRouter(prefix="/api/v1")


@router.get("/projects/{project_id}/graph")
async def api_v1_graph(project_id: int):
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)
    data = await storage.get_graph_data(project_id)
    return JSONResponse(data)


@router.post("/projects/{project_id}/discover-competitors")
async def api_v1_discover_competitors(project_id: int):
    """Use AI to discover and save competitors for a project."""
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)
    from opencmo.service import discover_competitors
    result = await discover_competitors(project_id)
    return JSONResponse({"competitors": result})


# --- Competitors CRUD ---


@router.get("/projects/{project_id}/competitors")
async def api_v1_competitors(project_id: int):
    return JSONResponse(await storage.list_competitors(project_id))


@router.post("/projects/{project_id}/competitors")
async def api_v1_add_competitor(project_id: int, request: Request):
    body = await request.json()
    name = body.get("name", "").strip()
    if not name:
        return JSONResponse({"error": "name is required"}, status_code=400)
    comp_id = await storage.add_competitor(
        project_id, name, url=body.get("url"), category=body.get("category"),
    )
    if comp_id:
        await storage.seed_node_if_expansion_exists(project_id, "competitor", comp_id, priority=90)
    # If keywords provided, add them too
    keywords = body.get("keywords", [])
    for kw in keywords:
        kw = kw.strip() if isinstance(kw, str) else ""
        if kw:
            ckw_id = await storage.add_competitor_keyword(comp_id, kw)
            if ckw_id:
                await storage.seed_node_if_expansion_exists(project_id, "competitor_keyword", ckw_id, priority=60)
    return JSONResponse({"id": comp_id, "name": name}, status_code=201)


@router.delete("/competitors/{competitor_id}")
async def api_v1_delete_competitor(competitor_id: int):
    ok = await storage.remove_competitor(competitor_id)
    if not ok:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse({"ok": True})


@router.get("/competitors/{competitor_id}/keywords")
async def api_v1_competitor_keywords(competitor_id: int):
    return JSONResponse(await storage.list_competitor_keywords(competitor_id))


@router.post("/competitors/{competitor_id}/keywords")
async def api_v1_add_competitor_keyword(competitor_id: int, request: Request):
    body = await request.json()
    keyword = body.get("keyword", "").strip()
    if not keyword:
        return JSONResponse({"error": "keyword is required"}, status_code=400)
    kw_id = await storage.add_competitor_keyword(competitor_id, keyword)
    # Seed into graph expansion — need project_id from competitor
    if kw_id:
        comp = await storage.get_competitor(competitor_id)
        if comp:
            await storage.seed_node_if_expansion_exists(comp["project_id"], "competitor_keyword", kw_id, priority=60)
    return JSONResponse({"id": kw_id, "keyword": keyword}, status_code=201)


# --- Graph Expansion ---


@router.get("/projects/{project_id}/expansion")
async def api_v1_expansion_status(project_id: int):
    """Get current expansion state."""
    expansion = await storage.get_expansion(project_id)
    if not expansion:
        return JSONResponse({
            "desired_state": "idle", "runtime_state": "idle",
            "current_wave": 0, "nodes_discovered": 0, "nodes_explored": 0,
        })
    return JSONResponse({
        "desired_state": expansion["desired_state"],
        "runtime_state": expansion["runtime_state"],
        "current_wave": expansion["current_wave"],
        "nodes_discovered": expansion["nodes_discovered"],
        "nodes_explored": expansion["nodes_explored"],
    })


@router.post("/projects/{project_id}/expansion/start")
async def api_v1_expansion_start(project_id: int):
    """Start or resume graph expansion."""

    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)

    expansion = await storage.get_or_create_expansion(project_id)
    active_task = await bg_service.find_active_task_by_dedupe_key(f"graph:project:{project_id}")
    if active_task is not None:
        return JSONResponse({"error": "Expansion already running"}, status_code=409)

    # If running with fresh heartbeat, reject
    if expansion["runtime_state"] == "running" and expansion.get("heartbeat_at"):
        from datetime import datetime, timezone
        try:
            hb = datetime.fromisoformat(expansion["heartbeat_at"])
            if (datetime.now(timezone.utc) - hb.replace(tzinfo=timezone.utc)).total_seconds() < 60:
                return JSONResponse({"error": "Expansion already running"}, status_code=409)
        except (ValueError, TypeError):
            pass
        # Stale heartbeat — mark interrupted, allow restart
        await storage.update_expansion(project_id, runtime_state="interrupted")

    # Seed frontier on first start
    if expansion["current_wave"] == 0:
        await storage.seed_expansion_nodes(project_id)

    # Set desired state
    await storage.update_expansion(project_id, desired_state="running")

    task = await bg_service.enqueue_task(
        kind="graph_expansion",
        project_id=project_id,
        payload={"project_id": project_id},
        dedupe_key=f"graph:project:{project_id}",
    )
    return JSONResponse({"status": "running", "task_id": task["task_id"]}, status_code=202)


@router.post("/projects/{project_id}/expansion/pause")
async def api_v1_expansion_pause(project_id: int):
    """Pause the running expansion. Loop will stop after current op."""
    expansion = await storage.get_expansion(project_id)
    if not expansion or expansion["desired_state"] != "running":
        return JSONResponse({"error": "Not running"}, status_code=400)
    await storage.update_expansion(project_id, desired_state="paused")
    return JSONResponse({"ok": True, "status": "pausing"})


@router.post("/projects/{project_id}/expansion/reset")
async def api_v1_expansion_reset(project_id: int):
    """Reset expansion state. Must not be running."""
    active_task = await bg_service.find_active_task_by_dedupe_key(f"graph:project:{project_id}")
    expansion = await storage.get_expansion(project_id)
    if active_task is not None or (expansion and expansion["runtime_state"] == "running"):
        return JSONResponse({"error": "Cannot reset while running"}, status_code=400)
    await storage.reset_expansion(project_id)
    return JSONResponse({"ok": True})


@router.get("/projects/{project_id}/expansion/progress")
async def api_v1_expansion_progress(project_id: int):
    """Get live expansion progress events."""
    tasks = await bg_service.list_tasks(kind="graph_expansion", limit=200)
    latest = next((task for task in tasks if task["project_id"] == project_id), None)
    if latest is None:
        return JSONResponse({"progress": []})

    events = await bg_service.list_task_events(latest["task_id"])
    progress = []
    for event in events:
        if event["event_type"] != "progress":
            continue
        payload = event["payload"] or {
            "stage": event["phase"],
            "status": event["status"],
            "summary": event["summary"],
        }
        progress.append(payload)
    return JSONResponse({"progress": progress})
