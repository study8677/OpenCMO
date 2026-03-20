"""FastAPI web dashboard for OpenCMO — Jinja2 SSR + REST API + SPA mount."""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import StreamingResponse

from opencmo import storage

_HERE = Path(__file__).parent
_TEMPLATES = Jinja2Templates(directory=str(_HERE / "templates"))
_SPA_DIR = _HERE.parent.parent.parent / "frontend" / "dist"  # <repo>/frontend/dist

app = FastAPI(title="OpenCMO Dashboard")
app.mount("/static", StaticFiles(directory=str(_HERE / "static")), name="static")


# ---------------------------------------------------------------------------
# Auth middleware
# ---------------------------------------------------------------------------

_PUBLIC_PREFIXES = ("/static/", "/favicon", "/api/v1/auth/")

_LOGIN_HTML = """<!DOCTYPE html>
<html><head><title>OpenCMO Login</title>
<style>
body{font-family:system-ui;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;background:#f8fafc}
.card{background:#fff;padding:2rem;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.1);max-width:360px;width:100%}
h2{margin:0 0 1rem}input{width:100%;padding:.5rem;border:1px solid #d1d5db;border-radius:4px;margin:.5rem 0}
button{width:100%;padding:.5rem;background:#2563eb;color:#fff;border:none;border-radius:4px;cursor:pointer;margin-top:.5rem}
button:hover{background:#1d4ed8}.error{color:#dc2626;font-size:.875rem;margin-top:.5rem;display:none}
</style></head><body>
<div class="card"><h2>OpenCMO</h2><p>Enter your access token to continue.</p>
<form id="f"><input name="token" type="password" placeholder="Token" required>
<button type="submit">Login</button><div class="error" id="e">Invalid token</div></form></div>
<script>
document.getElementById('f').onsubmit=async e=>{
  e.preventDefault();const t=e.target.token.value;
  const r=await fetch('/api/v1/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:t})});
  if(r.ok)location.reload();else document.getElementById('e').style.display='block';
};
</script></body></html>"""


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    token = os.environ.get("OPENCMO_WEB_TOKEN")
    if token:
        path = request.url.path
        if path == "/" or any(path.startswith(p) for p in _PUBLIC_PREFIXES):
            return await call_next(request)
        # Check Authorization header or cookie
        auth = request.headers.get("Authorization", "")
        cookie_token = request.cookies.get("opencmo_token", "")
        if auth != f"Bearer {token}" and cookie_token != token:
            if path.startswith("/api/"):
                return JSONResponse({"error": "Unauthorized"}, status_code=401)
            return HTMLResponse(_LOGIN_HTML, status_code=401)
    return await call_next(request)


# ---------------------------------------------------------------------------
# Auth endpoint
# ---------------------------------------------------------------------------


@app.post("/api/v1/auth/login")
async def auth_login(request: Request):
    body = await request.json()
    expected = os.environ.get("OPENCMO_WEB_TOKEN", "")
    if not expected or body.get("token") != expected:
        return JSONResponse({"error": "Invalid token"}, status_code=401)
    resp = JSONResponse({"ok": True})
    resp.set_cookie("opencmo_token", expected, httponly=True, samesite="lax")
    return resp


# ---------------------------------------------------------------------------
# Legacy HTML routes (Jinja2 SSR)
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    projects = await storage.list_projects()
    project_data = []
    for p in projects:
        latest = await storage.get_latest_scans(p["id"])
        project_data.append({**p, "latest": latest})
    return _TEMPLATES.TemplateResponse("dashboard.html", {"request": request, "projects": project_data})


@app.get("/project/{project_id}", response_class=HTMLResponse)
async def project_overview(request: Request, project_id: int):
    project = await storage.get_project(project_id)
    if not project:
        return HTMLResponse("Project not found", status_code=404)
    latest = await storage.get_latest_scans(project_id)
    seo_history = await storage.get_seo_history(project_id, limit=10)
    geo_history = await storage.get_geo_history(project_id, limit=10)
    discussions = await storage.get_tracked_discussions(project_id)
    return _TEMPLATES.TemplateResponse("project.html", {
        "request": request,
        "project": project,
        "latest": latest,
        "seo_history": seo_history,
        "geo_history": geo_history,
        "discussions": discussions,
    })


@app.get("/project/{project_id}/seo", response_class=HTMLResponse)
async def project_seo(request: Request, project_id: int):
    project = await storage.get_project(project_id)
    if not project:
        return HTMLResponse("Project not found", status_code=404)
    history = await storage.get_seo_history(project_id, limit=20)
    return _TEMPLATES.TemplateResponse("seo.html", {
        "request": request, "project": project, "history": history,
    })


@app.get("/project/{project_id}/geo", response_class=HTMLResponse)
async def project_geo(request: Request, project_id: int):
    project = await storage.get_project(project_id)
    if not project:
        return HTMLResponse("Project not found", status_code=404)
    history = await storage.get_geo_history(project_id, limit=20)
    return _TEMPLATES.TemplateResponse("geo.html", {
        "request": request, "project": project, "history": history,
    })


@app.get("/project/{project_id}/serp", response_class=HTMLResponse)
async def project_serp(request: Request, project_id: int):
    project = await storage.get_project(project_id)
    if not project:
        return HTMLResponse("Project not found", status_code=404)
    serp_latest = await storage.get_all_serp_latest(project_id)
    keywords = await storage.list_tracked_keywords(project_id)
    serp_map = {s["keyword"]: s for s in serp_latest}
    kw_data = []
    for kw in keywords:
        s = serp_map.get(kw["keyword"], {})
        kw_data.append({
            "keyword": kw["keyword"],
            "position": s.get("position"),
            "url_found": s.get("url_found"),
            "provider": s.get("provider"),
            "error": s.get("error"),
            "checked_at": s.get("checked_at"),
        })
    serp_history = serp_latest
    return _TEMPLATES.TemplateResponse("serp.html", {
        "request": request,
        "project": project,
        "keywords": kw_data,
        "serp_history": serp_history,
    })


@app.get("/project/{project_id}/community", response_class=HTMLResponse)
async def project_community(request: Request, project_id: int):
    project = await storage.get_project(project_id)
    if not project:
        return HTMLResponse("Project not found", status_code=404)
    discussions = await storage.get_tracked_discussions(project_id)
    community_history = await storage.get_community_history(project_id, limit=10)
    return _TEMPLATES.TemplateResponse("community.html", {
        "request": request, "project": project,
        "discussions": discussions, "community_history": community_history,
    })


# ---------------------------------------------------------------------------
# Legacy JSON API routes (Chart.js data sources)
# ---------------------------------------------------------------------------


@app.get("/api/project/{project_id}/seo-data")
async def api_seo_data(project_id: int):
    history = await storage.get_seo_history(project_id, limit=30)
    history.reverse()
    return JSONResponse({
        "labels": [s["scanned_at"][:10] for s in history],
        "performance": [s["score_performance"] for s in history],
        "lcp": [s["score_lcp"] for s in history],
        "cls": [s["score_cls"] for s in history],
        "tbt": [s["score_tbt"] for s in history],
    })


@app.get("/api/project/{project_id}/geo-data")
async def api_geo_data(project_id: int):
    history = await storage.get_geo_history(project_id, limit=30)
    history.reverse()
    return JSONResponse({
        "labels": [s["scanned_at"][:10] for s in history],
        "geo_score": [s["geo_score"] for s in history],
        "visibility": [s["visibility_score"] for s in history],
        "position": [s["position_score"] for s in history],
        "sentiment": [s["sentiment_score"] for s in history],
    })


@app.get("/api/project/{project_id}/serp-data")
async def api_serp_data(project_id: int):
    keywords = await storage.list_tracked_keywords(project_id)
    result = {"labels": [], "keywords": [], "positions": {}}
    if not keywords:
        return JSONResponse(result)

    all_dates: set[str] = set()
    kw_history: dict[str, list[dict]] = {}
    for kw in keywords:
        history = await storage.get_serp_history(project_id, kw["keyword"], limit=30)
        history.reverse()
        kw_history[kw["keyword"]] = history
        for h in history:
            all_dates.add(h["checked_at"][:10])

    labels = sorted(all_dates)
    result["labels"] = labels
    result["keywords"] = [kw["keyword"] for kw in keywords]

    for kw in keywords:
        history = kw_history[kw["keyword"]]
        date_map = {h["checked_at"][:10]: h["position"] for h in history if not h.get("error")}
        result["positions"][kw["keyword"]] = [date_map.get(d) for d in labels]

    return JSONResponse(result)


@app.get("/api/project/{project_id}/community-data")
async def api_community_data(project_id: int):
    history = await storage.get_community_history(project_id, limit=30)
    history.reverse()
    discussions = await storage.get_tracked_discussions(project_id)
    platforms: dict[str, int] = {}
    for d in discussions:
        platforms[d["platform"]] = platforms.get(d["platform"], 0) + 1
    return JSONResponse({
        "scan_labels": [s["scanned_at"][:10] for s in history],
        "scan_hits": [s["total_hits"] for s in history],
        "platform_labels": list(platforms.keys()),
        "platform_counts": list(platforms.values()),
    })


# ---------------------------------------------------------------------------
# REST API v1 — Projects
# ---------------------------------------------------------------------------


@app.get("/api/v1/projects")
async def api_v1_projects():
    from opencmo import service
    return JSONResponse(await service.get_status_summary())


@app.get("/api/v1/projects/{project_id}")
async def api_v1_project(project_id: int):
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse(project)


@app.get("/api/v1/projects/{project_id}/summary")
async def api_v1_project_summary(project_id: int):
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)
    latest = await storage.get_latest_scans(project_id)
    previous = await storage.get_previous_scans(project_id)
    return JSONResponse({"project": project, "latest": latest, "previous": previous})


# --- Scan data ---


@app.get("/api/v1/projects/{project_id}/seo/history")
async def api_v1_seo_history(project_id: int):
    return JSONResponse(await storage.get_seo_history(project_id))


@app.get("/api/v1/projects/{project_id}/seo/chart")
async def api_v1_seo_chart(project_id: int):
    history = await storage.get_seo_history(project_id, limit=30)
    history.reverse()
    return JSONResponse({
        "labels": [s["scanned_at"][:10] for s in history],
        "performance": [s["score_performance"] for s in history],
        "lcp": [s["score_lcp"] for s in history],
        "cls": [s["score_cls"] for s in history],
        "tbt": [s["score_tbt"] for s in history],
    })


@app.get("/api/v1/projects/{project_id}/geo/history")
async def api_v1_geo_history(project_id: int):
    return JSONResponse(await storage.get_geo_history(project_id))


@app.get("/api/v1/projects/{project_id}/geo/chart")
async def api_v1_geo_chart(project_id: int):
    history = await storage.get_geo_history(project_id, limit=30)
    history.reverse()
    return JSONResponse({
        "labels": [s["scanned_at"][:10] for s in history],
        "geo_score": [s["geo_score"] for s in history],
        "visibility": [s["visibility_score"] for s in history],
        "position": [s["position_score"] for s in history],
        "sentiment": [s["sentiment_score"] for s in history],
    })


@app.get("/api/v1/projects/{project_id}/community/history")
async def api_v1_community_history(project_id: int):
    return JSONResponse(await storage.get_community_history(project_id))


@app.get("/api/v1/projects/{project_id}/community/discussions")
async def api_v1_community_discussions(project_id: int):
    return JSONResponse(await storage.get_tracked_discussions(project_id))


@app.get("/api/v1/projects/{project_id}/community/chart")
async def api_v1_community_chart(project_id: int):
    history = await storage.get_community_history(project_id, limit=30)
    history.reverse()
    discussions = await storage.get_tracked_discussions(project_id)
    platforms: dict[str, int] = {}
    for d in discussions:
        platforms[d["platform"]] = platforms.get(d["platform"], 0) + 1
    return JSONResponse({
        "scan_labels": [s["scanned_at"][:10] for s in history],
        "scan_hits": [s["total_hits"] for s in history],
        "platform_labels": list(platforms.keys()),
        "platform_counts": list(platforms.values()),
    })


@app.get("/api/v1/projects/{project_id}/serp/latest")
async def api_v1_serp_latest(project_id: int):
    return JSONResponse(await storage.get_all_serp_latest(project_id))


@app.get("/api/v1/projects/{project_id}/serp/chart")
async def api_v1_serp_chart(project_id: int):
    keywords = await storage.list_tracked_keywords(project_id)
    result: dict = {"labels": [], "keywords": [], "positions": {}}
    if not keywords:
        return JSONResponse(result)
    all_dates: set[str] = set()
    kw_history: dict[str, list[dict]] = {}
    for kw in keywords:
        history = await storage.get_serp_history(project_id, kw["keyword"], limit=30)
        history.reverse()
        kw_history[kw["keyword"]] = history
        for h in history:
            all_dates.add(h["checked_at"][:10])
    labels = sorted(all_dates)
    result["labels"] = labels
    result["keywords"] = [kw["keyword"] for kw in keywords]
    for kw in keywords:
        history = kw_history[kw["keyword"]]
        date_map = {h["checked_at"][:10]: h["position"] for h in history if not h.get("error")}
        result["positions"][kw["keyword"]] = [date_map.get(d) for d in labels]
    return JSONResponse(result)


# ---------------------------------------------------------------------------
# REST API v1 — Keywords
# ---------------------------------------------------------------------------


@app.get("/api/v1/projects/{project_id}/keywords")
async def api_v1_keywords(project_id: int):
    return JSONResponse(await storage.list_tracked_keywords(project_id))


@app.post("/api/v1/projects/{project_id}/keywords")
async def api_v1_add_keyword(project_id: int, request: Request):
    body = await request.json()
    keyword = body.get("keyword", "").strip()
    if not keyword:
        return JSONResponse({"error": "keyword is required"}, status_code=400)
    kw_id = await storage.add_tracked_keyword(project_id, keyword)
    return JSONResponse({"id": kw_id, "keyword": keyword}, status_code=201)


@app.delete("/api/v1/keywords/{keyword_id}")
async def api_v1_delete_keyword(keyword_id: int):
    ok = await storage.remove_tracked_keyword(keyword_id)
    if not ok:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse({"ok": True})


# ---------------------------------------------------------------------------
# REST API v1 — Monitors
# ---------------------------------------------------------------------------


@app.get("/api/v1/monitors")
async def api_v1_monitors():
    from opencmo import service
    return JSONResponse(await service.list_monitors())


@app.post("/api/v1/monitors")
async def api_v1_create_monitor(request: Request):
    from urllib.parse import urlparse
    from opencmo import service
    from opencmo.web import task_registry

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
    result = await service.create_monitor(
        brand, url, category,
        job_type=job_type,
        cron_expr=body.get("cron_expr", "0 9 * * *"),
        keywords=body.get("keywords"),
    )
    # Auto-trigger: AI analysis (extract brand/category/keywords) + first scan
    task = task_registry.submit_scan(
        monitor_id=result["monitor_id"],
        project_id=result["project_id"],
        job_type=job_type,
        job_id=result["monitor_id"],
        analyze_url=url,
    )
    if task:
        result["task_id"] = task.task_id
    return JSONResponse(result, status_code=201)


@app.delete("/api/v1/monitors/{monitor_id}")
async def api_v1_delete_monitor(monitor_id: int):
    from opencmo import service
    ok = await service.remove_monitor(monitor_id)
    if not ok:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse({"ok": True})


@app.post("/api/v1/monitors/{monitor_id}/run")
async def api_v1_run_monitor(monitor_id: int):
    from opencmo import service
    from opencmo.web import task_registry

    job = await service.get_monitor(monitor_id)
    if not job:
        return JSONResponse({"error": "Monitor not found"}, status_code=404)

    record = task_registry.submit_scan(
        monitor_id=monitor_id,
        project_id=job["project_id"],
        job_type=job["job_type"],
        job_id=monitor_id,
    )
    if record is None:
        return JSONResponse({"error": "Monitor is already running"}, status_code=409)
    return JSONResponse(record.to_dict(), status_code=202)


# ---------------------------------------------------------------------------
# REST API v1 — Tasks
# ---------------------------------------------------------------------------


@app.get("/api/v1/tasks")
async def api_v1_tasks():
    from opencmo.web import task_registry
    return JSONResponse([t.to_dict() for t in task_registry.list_tasks()])


@app.get("/api/v1/tasks/{task_id}")
async def api_v1_task(task_id: str):
    from opencmo.web import task_registry
    record = task_registry.get_task(task_id)
    if not record:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse(record.to_dict())


# ---------------------------------------------------------------------------
# REST API v1 — Report
# ---------------------------------------------------------------------------


@app.post("/api/v1/projects/{project_id}/report")
async def api_v1_report(project_id: int):
    from opencmo import service
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)
    result = await service.send_project_report(project_id)
    if result["ok"]:
        return JSONResponse(result)
    return JSONResponse(result, status_code=500)


# ---------------------------------------------------------------------------
# REST API v1 — Chat (SSE streaming)
# ---------------------------------------------------------------------------


def _get_item_name(item) -> str:
    """Safely extract tool/handoff name from a RunItem."""
    raw = getattr(item, "raw_item", None)
    if raw is not None and hasattr(raw, "name"):
        return raw.name
    return getattr(item, "title", None) or "unknown"


@app.post("/api/v1/chat/sessions")
async def api_v1_chat_session_create():
    from opencmo.web import chat_sessions
    session_id = await chat_sessions.create_session()
    return JSONResponse({"session_id": session_id}, status_code=201)


@app.get("/api/v1/chat/sessions")
async def api_v1_chat_sessions_list():
    from opencmo.web import chat_sessions
    sessions = await chat_sessions.list_sessions()
    return JSONResponse(sessions)


@app.get("/api/v1/chat/sessions/{session_id}/messages")
async def api_v1_chat_session_messages(session_id: str):
    from opencmo.web import chat_sessions
    messages = await chat_sessions.get_session_messages(session_id)
    if messages is None:
        return JSONResponse({"error": "Session not found"}, status_code=404)
    return JSONResponse(messages)


@app.delete("/api/v1/chat/sessions/{session_id}")
async def api_v1_chat_session_delete(session_id: str):
    from opencmo.web import chat_sessions
    ok = await chat_sessions.delete_session(session_id)
    if not ok:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse({"ok": True})


@app.post("/api/v1/chat")
async def api_v1_chat(request: Request):
    from opencmo.web import chat_sessions
    body = await request.json()
    session_id = body.get("session_id", "")
    message = body.get("message", "").strip()

    if not message:
        return JSONResponse({"error": "message is required"}, status_code=400)

    input_items = await chat_sessions.get_session(session_id)
    if input_items is None:
        return JSONResponse({"error": "Invalid session_id"}, status_code=404)

    input_items.append({"role": "user", "content": message})

    async def event_stream():
        try:
            from agents import Runner
            from opencmo.agents.cmo import cmo_agent

            result = Runner.run_streamed(cmo_agent, input_items, max_turns=15)

            async for event in result.stream_events():
                if event.type == "raw_response_event":
                    data = event.data
                    if hasattr(data, "type") and data.type == "response.output_text.delta":
                        yield f"data: {json.dumps({'type': 'delta', 'content': data.delta})}\n\n"
                elif event.type == "agent_updated_stream_event":
                    yield f"data: {json.dumps({'type': 'agent', 'name': event.new_agent.name})}\n\n"
                elif event.type == "run_item_stream_event":
                    name = event.name
                    if name == "tool_called":
                        yield f"data: {json.dumps({'type': 'tool_call', 'name': _get_item_name(event.item)})}\n\n"
                    elif name == "tool_output":
                        yield f"data: {json.dumps({'type': 'tool_done'})}\n\n"
                    elif name == "handoff_requested":
                        yield f"data: {json.dumps({'type': 'handoff', 'target': _get_item_name(event.item)})}\n\n"
                    elif name == "handoff_occured":
                        yield f"data: {json.dumps({'type': 'handoff_done'})}\n\n"
                    elif name == "tool_search_called":
                        yield f"data: {json.dumps({'type': 'tool_search'})}\n\n"
                    elif name == "tool_search_output_created":
                        yield f"data: {json.dumps({'type': 'tool_search_done'})}\n\n"
                    elif name == "message_output_created":
                        yield f"data: {json.dumps({'type': 'message_created'})}\n\n"
                    elif name == "reasoning_item_created":
                        yield f"data: {json.dumps({'type': 'reasoning'})}\n\n"

            # Stream finished — persist session state
            await chat_sessions.update_session(session_id, result.to_input_list())
            agent_name = result.last_agent.name if result.last_agent else "CMO Agent"
            yield f"data: {json.dumps({'type': 'done', 'agent_name': agent_name, 'final_output': result.final_output})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# REST API v1 — Settings (API key, model, base URL)
# ---------------------------------------------------------------------------


@app.get("/api/v1/settings")
async def api_v1_settings_get():
    from opencmo import storage, config
    api_key = await storage.get_setting("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    base_url = await storage.get_setting("OPENAI_BASE_URL") or os.environ.get("OPENAI_BASE_URL", "")
    model = await storage.get_setting("OPENCMO_MODEL_DEFAULT") or os.environ.get("OPENCMO_MODEL_DEFAULT", "")
    return JSONResponse({
        "api_key_set": bool(api_key),
        "api_key_masked": f"{api_key[:3]}...{api_key[-4:]}" if len(api_key) > 8 else ("***" if api_key else ""),
        "base_url": base_url,
        "model": model,
    })


@app.post("/api/v1/settings")
async def api_v1_settings_save(request: Request):
    from opencmo import storage, config
    body = await request.json()
    for key in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENCMO_MODEL_DEFAULT"):
        val = body.get(key)
        if val is not None:
            val = val.strip()
            if val:
                await storage.set_setting(key, val)
                os.environ[key] = val
            else:
                await storage.delete_setting(key)
                os.environ.pop(key, None)
    config.reset_client()
    return JSONResponse({"ok": True})


# ---------------------------------------------------------------------------
# SPA mount — /app/ serves React frontend
# ---------------------------------------------------------------------------


@app.get("/app")
@app.get("/app/{full_path:path}")
async def spa_catchall(request: Request, full_path: str = ""):
    index = _SPA_DIR / "index.html"
    if not index.exists():
        return HTMLResponse(
            "<h1>Frontend not built</h1><p>Run <code>cd frontend && npm run build</code> to build the SPA.</p>",
            status_code=404,
        )
    # Serve static assets from dist
    if full_path and not full_path.startswith("index.html"):
        asset = _SPA_DIR / full_path
        if asset.exists() and asset.is_file():
            import mimetypes
            ct = mimetypes.guess_type(str(asset))[0] or "application/octet-stream"
            return StreamingResponse(open(asset, "rb"), media_type=ct)
    # SPA fallback — always return index.html
    return HTMLResponse(index.read_text())


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------


def run_server(port: int = 8080):
    import uvicorn

    load_dotenv()
    host = os.environ.get("OPENCMO_WEB_HOST", "127.0.0.1")
    uvicorn.run(app, host=host, port=port)
