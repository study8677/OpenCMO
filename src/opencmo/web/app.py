"""FastAPI web dashboard for OpenCMO — Jinja2 SSR + REST API + SPA mount."""

from __future__ import annotations

import asyncio
import json
import logging
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
logger = logging.getLogger(__name__)


# In-memory expansion tracking (lightweight, no third task model)
_expansion_progress: dict[int, list[dict]] = {}   # project_id -> progress events
_expansion_tasks: dict[int, asyncio.Task] = {}     # project_id -> running asyncio.Task


@app.on_event("startup")
async def _startup_fix_stale_expansions():
    """Mark any stale 'running' expansions as interrupted (from previous process)."""
    await storage.ensure_db()
    try:
        fixed = await storage.fix_stale_expansions(timeout_seconds=60)
        if fixed:
            logger.info("Fixed %d stale expansion(s) on startup", fixed)
    except Exception:
        pass  # table may not exist yet on first run


@app.on_event("startup")
async def _startup_runtime_services():
    """Start optional runtime services after DB bootstrap."""
    from opencmo import scheduler

    if not scheduler.is_scheduler_available():
        logger.info("APScheduler not installed; scheduled monitors will remain inactive.")
        return

    loaded_jobs = await scheduler.load_jobs_from_db()
    scheduler.start_scheduler()
    logger.info("Scheduler started with %d enabled monitor job(s)", loaded_jobs)


@app.on_event("shutdown")
async def _shutdown_runtime_services():
    """Stop optional runtime services cleanly."""
    from opencmo import scheduler

    scheduler.stop_scheduler()
    logger.info("Scheduler stopped")


# ---------------------------------------------------------------------------
# Auth middleware
# ---------------------------------------------------------------------------

_PUBLIC_PREFIXES = ("/static/", "/favicon", "/api/v1/auth/", "/api/v1/health")

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


@app.get("/api/v1/health")
async def api_v1_health():
    from opencmo import scheduler

    return JSONResponse({
        "ok": True,
        "scheduler": scheduler.scheduler_status(),
    })


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


@app.delete("/api/v1/projects/{project_id}")
async def api_v1_delete_project(project_id: int):
    # Cancel running expansion if any
    await storage.update_expansion(project_id, desired_state="idle")
    old_task = _expansion_tasks.pop(project_id, None)
    if old_task and not old_task.done():
        old_task.cancel()
    _expansion_progress.pop(project_id, None)
    ok = await storage.delete_project(project_id)
    if not ok:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse({"ok": True})


@app.get("/api/v1/overview")
async def api_v1_overview():
    """Global health overview — aggregated metrics across all projects."""
    projects = await storage.list_projects()
    seo_scores: list[float] = []
    geo_scores: list[int] = []
    community_hits = 0
    total_keywords = 0
    total_competitors = 0
    recent_campaigns: list[dict] = []

    for p in projects:
        latest = await storage.get_latest_scans(p["id"])
        seo = latest.get("seo")
        if seo and seo.get("score") is not None:
            seo_scores.append(seo["score"])
        geo = latest.get("geo")
        if geo and geo.get("score") is not None:
            geo_scores.append(geo["score"])
        comm = latest.get("community")
        if comm:
            community_hits += comm.get("total_hits", 0)
        kws = await storage.list_tracked_keywords(p["id"])
        total_keywords += len(kws)
        comps = await storage.list_competitors(p["id"])
        total_competitors += len(comps)
        # Collect recent campaigns
        campaigns = await storage.list_campaign_runs(p["id"], limit=3)
        for c in campaigns:
            c["brand_name"] = p["brand_name"]
            recent_campaigns.append(c)

    # Sort campaigns by created_at descending
    recent_campaigns.sort(key=lambda c: c.get("created_at", ""), reverse=True)

    return JSONResponse({
        "project_count": len(projects),
        "avg_seo_score": round(sum(seo_scores) / len(seo_scores) * 100) if seo_scores else None,
        "avg_geo_score": round(sum(geo_scores) / len(geo_scores)) if geo_scores else None,
        "total_community_hits": community_hits,
        "total_keywords": total_keywords,
        "total_competitors": total_competitors,
        "recent_campaigns": recent_campaigns[:5],
    })


@app.get("/api/v1/projects/{project_id}/summary")
async def api_v1_project_summary(project_id: int):
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)
    latest = await storage.get_latest_scans(project_id)
    previous = await storage.get_previous_scans(project_id)
    monitoring = await storage.get_latest_monitoring_summary(project_id)
    return JSONResponse({
        "project": project,
        "latest": latest,
        "previous": previous,
        "latest_monitoring": monitoring,
    })


@app.get("/api/v1/projects/{project_id}/next-actions")
async def api_v1_next_actions(project_id: int):
    """Synthesize cross-signal next best actions from latest scan data."""
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)

    latest = await storage.get_latest_scans(project_id)
    actions: list[dict] = []

    # SEO signals
    seo = latest.get("seo")
    if not seo:
        actions.append({
            "domain": "seo", "priority": "high", "icon": "search",
            "title": "Run your first SEO audit",
            "description": "No SEO data yet. Run a scan to get performance scores, Core Web Vitals, and technical recommendations.",
        })
    elif seo.get("score") is not None and seo["score"] < 0.7:
        actions.append({
            "domain": "seo", "priority": "high", "icon": "search",
            "title": f"Improve SEO performance (score: {int(seo['score'] * 100)}%)",
            "description": "Your performance score is below 70%. Focus on Core Web Vitals (LCP, CLS, TBT) to improve search rankings.",
        })

    # GEO signals
    geo = latest.get("geo")
    if not geo:
        actions.append({
            "domain": "geo", "priority": "high", "icon": "globe",
            "title": "Check AI search visibility",
            "description": "No GEO data yet. Run a scan to see how AI platforms (ChatGPT, Perplexity, etc.) talk about your brand.",
        })
    elif geo.get("score") is not None and geo["score"] < 30:
        actions.append({
            "domain": "geo", "priority": "high", "icon": "globe",
            "title": f"Boost AI visibility (GEO score: {geo['score']}/100)",
            "description": "Your brand has low AI platform visibility. Create authoritative content that AI models can cite.",
        })
    elif geo.get("score") is not None and geo["score"] < 60:
        actions.append({
            "domain": "geo", "priority": "medium", "icon": "globe",
            "title": f"Strengthen AI positioning (GEO score: {geo['score']}/100)",
            "description": "Your brand is known to AI but not top-of-mind. Focus on being mentioned earlier and more positively.",
        })

    # Community signals
    community = latest.get("community")
    if not community:
        actions.append({
            "domain": "community", "priority": "medium", "icon": "users",
            "title": "Start community monitoring",
            "description": "No community data yet. Run a scan to discover where people discuss your brand on Reddit, HN, and Dev.to.",
        })
    elif community.get("total_hits", 0) == 0:
        actions.append({
            "domain": "community", "priority": "high", "icon": "users",
            "title": "Build community presence",
            "description": "No community discussions found. Share your product on Reddit, Hacker News, or Dev.to to get initial traction.",
        })

    # SERP signals
    serp = latest.get("serp", [])
    if not serp:
        actions.append({
            "domain": "serp", "priority": "medium", "icon": "trending-up",
            "title": "Track keyword rankings",
            "description": "No keywords tracked yet. Add keywords to monitor your search engine position over time.",
        })
    else:
        unranked = [s for s in serp if not s.get("position")]
        if unranked:
            kws = ", ".join(s["keyword"] for s in unranked[:3])
            actions.append({
                "domain": "serp", "priority": "high", "icon": "trending-up",
                "title": f"Not ranking for {len(unranked)} keyword(s)",
                "description": f"You're not appearing in search results for: {kws}. Create targeted content to rank for these terms.",
            })

    # Graph / competitors
    competitors = await storage.list_competitors(project_id)
    if not competitors:
        actions.append({
            "domain": "graph", "priority": "medium", "icon": "git-branch",
            "title": "Discover competitors",
            "description": "No competitors tracked. Use the Knowledge Graph to discover and analyze your competitive landscape.",
        })

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    actions.sort(key=lambda a: priority_order.get(a["priority"], 9))

    return JSONResponse({"actions": actions})


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
# REST API v1 — Knowledge Graph
# ---------------------------------------------------------------------------


@app.get("/api/v1/projects/{project_id}/graph")
async def api_v1_graph(project_id: int):
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)
    data = await storage.get_graph_data(project_id)
    return JSONResponse(data)


@app.post("/api/v1/projects/{project_id}/discover-competitors")
async def api_v1_discover_competitors(project_id: int):
    """Use AI to discover and save competitors for a project."""
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)
    from opencmo.service import discover_competitors
    result = await discover_competitors(project_id)
    return JSONResponse({"competitors": result})


# ---------------------------------------------------------------------------
# REST API v1 — Competitors
# ---------------------------------------------------------------------------


@app.get("/api/v1/projects/{project_id}/competitors")
async def api_v1_competitors(project_id: int):
    return JSONResponse(await storage.list_competitors(project_id))


@app.post("/api/v1/projects/{project_id}/competitors")
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


@app.delete("/api/v1/competitors/{competitor_id}")
async def api_v1_delete_competitor(competitor_id: int):
    ok = await storage.remove_competitor(competitor_id)
    if not ok:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse({"ok": True})


@app.get("/api/v1/competitors/{competitor_id}/keywords")
async def api_v1_competitor_keywords(competitor_id: int):
    return JSONResponse(await storage.list_competitor_keywords(competitor_id))


@app.post("/api/v1/competitors/{competitor_id}/keywords")
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


# ---------------------------------------------------------------------------
# REST API v1 — Graph Expansion
# ---------------------------------------------------------------------------

@app.get("/api/v1/projects/{project_id}/expansion")
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


@app.post("/api/v1/projects/{project_id}/expansion/start")
async def api_v1_expansion_start(project_id: int):
    """Start or resume graph expansion."""
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)

    expansion = await storage.get_or_create_expansion(project_id)

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

    from opencmo.graph_expansion import run_expansion

    # Seed frontier on first start
    if expansion["current_wave"] == 0:
        await storage.seed_expansion_nodes(project_id)

    # Set desired state
    await storage.update_expansion(project_id, desired_state="running")

    # Clear progress, launch task
    _expansion_progress[project_id] = []

    def on_progress(event: dict):
        events = _expansion_progress.setdefault(project_id, [])
        events.append(event)
        # Keep last 100 events
        if len(events) > 100:
            _expansion_progress[project_id] = events[-50:]

    async def _run():
        try:
            await run_expansion(project_id, on_progress=on_progress)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Expansion failed for project %d", project_id)
            await storage.update_expansion(project_id, runtime_state="interrupted")
        finally:
            _expansion_tasks.pop(project_id, None)

    # Cancel any lingering task
    old_task = _expansion_tasks.pop(project_id, None)
    if old_task and not old_task.done():
        old_task.cancel()

    _expansion_tasks[project_id] = asyncio.get_event_loop().create_task(_run())
    return JSONResponse({"status": "running"}, status_code=202)


@app.post("/api/v1/projects/{project_id}/expansion/pause")
async def api_v1_expansion_pause(project_id: int):
    """Pause the running expansion. Loop will stop after current op."""
    expansion = await storage.get_expansion(project_id)
    if not expansion or expansion["desired_state"] != "running":
        return JSONResponse({"error": "Not running"}, status_code=400)
    await storage.update_expansion(project_id, desired_state="paused")
    return JSONResponse({"ok": True, "status": "pausing"})


@app.post("/api/v1/projects/{project_id}/expansion/reset")
async def api_v1_expansion_reset(project_id: int):
    """Reset expansion state. Must not be running."""
    expansion = await storage.get_expansion(project_id)
    if expansion and expansion["runtime_state"] == "running":
        return JSONResponse({"error": "Cannot reset while running"}, status_code=400)
    await storage.reset_expansion(project_id)
    _expansion_progress.pop(project_id, None)
    return JSONResponse({"ok": True})


@app.get("/api/v1/projects/{project_id}/expansion/progress")
async def api_v1_expansion_progress(project_id: int):
    """Get live expansion progress events."""
    events = _expansion_progress.get(project_id, [])
    return JSONResponse({"progress": events})


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
    if kw_id:
        await storage.seed_node_if_expansion_exists(project_id, "keyword", kw_id, priority=80)
    return JSONResponse({"id": kw_id, "keyword": keyword}, status_code=201)


@app.delete("/api/v1/keywords/{keyword_id}")
async def api_v1_delete_keyword(keyword_id: int):
    ok = await storage.remove_tracked_keyword(keyword_id)
    if not ok:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse({"ok": True})


# ---------------------------------------------------------------------------
# REST API v1 — Campaigns
# ---------------------------------------------------------------------------


@app.get("/api/v1/projects/{project_id}/campaigns")
async def api_v1_campaigns(project_id: int):
    """List campaign runs for a project."""
    return JSONResponse(await storage.list_campaign_runs(project_id))


@app.get("/api/v1/campaigns/{run_id}")
async def api_v1_campaign_detail(run_id: int):
    """Get a campaign run with all its artifacts."""
    run = await storage.get_campaign_run(run_id)
    if not run:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse(run)


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
    locale = body.get("locale", "en").strip() or "en"
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
        locale=locale,
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


@app.patch("/api/v1/monitors/{monitor_id}")
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
# REST API v1 — Approvals
# ---------------------------------------------------------------------------


@app.get("/api/v1/approvals")
async def api_v1_approvals(status: str | None = None, limit: int = 50):
    from opencmo import service

    return JSONResponse(await service.list_approvals(status=status, limit=limit))


@app.get("/api/v1/approvals/{approval_id}")
async def api_v1_approval(approval_id: int):
    from opencmo import service

    approval = await service.get_approval(approval_id)
    if not approval:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse(approval)


@app.post("/api/v1/approvals")
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


@app.post("/api/v1/approvals/{approval_id}/approve")
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
        return JSONResponse({"error": result["error"], "approval": result.get("approval")}, status_code=status_code)
    return JSONResponse(result["approval"])


@app.post("/api/v1/approvals/{approval_id}/reject")
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


@app.get("/api/v1/tasks/{task_id}/findings")
async def api_v1_task_findings(task_id: str):
    return JSONResponse(await storage.get_task_findings(task_id))


@app.get("/api/v1/tasks/{task_id}/recommendations")
async def api_v1_task_recommendations(task_id: str):
    return JSONResponse(await storage.get_task_recommendations(task_id))


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

    context_item = None
    # Inject project context from knowledge graph
    from opencmo.context import resolve_chat_project, build_project_context
    project_id = await resolve_chat_project(body)
    if project_id:
        ctx = await build_project_context(project_id, depth="brief")
        if ctx:
            input_items.insert(0, {"role": "system", "content": f"[Project Context]\n{ctx}"})
            context_item = input_items[0]

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
            updated_items = result.to_input_list()
            if context_item and updated_items[:1] == [context_item]:
                updated_items = updated_items[1:]
            await chat_sessions.update_session(session_id, updated_items)
            agent_name = result.last_agent.name if result.last_agent else "CMO Agent"
            yield f"data: {json.dumps({'type': 'done', 'agent_name': agent_name, 'final_output': result.final_output})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# REST API v1 — Settings (API key, model, base URL)
# ---------------------------------------------------------------------------


def _mask_key(key: str) -> str:
    if len(key) > 8:
        return f"{key[:3]}...{key[-4:]}"
    return "***" if key else ""


async def _get_setting(name: str) -> str:
    return await storage.get_setting(name) or os.environ.get(name, "")


@app.get("/api/v1/settings")
async def api_v1_settings_get():
    from opencmo import config
    api_key = await _get_setting("OPENAI_API_KEY")
    base_url = await _get_setting("OPENAI_BASE_URL")
    model = await _get_setting("OPENCMO_MODEL_DEFAULT")
    # Reddit
    reddit_cid = await _get_setting("REDDIT_CLIENT_ID")
    reddit_secret = await _get_setting("REDDIT_CLIENT_SECRET")
    reddit_user = await _get_setting("REDDIT_USERNAME")
    reddit_pass = await _get_setting("REDDIT_PASSWORD")
    auto_publish = await _get_setting("OPENCMO_AUTO_PUBLISH")
    # Twitter
    twitter_api_key = await _get_setting("TWITTER_API_KEY")
    twitter_api_secret = await _get_setting("TWITTER_API_SECRET")
    twitter_access_token = await _get_setting("TWITTER_ACCESS_TOKEN")
    twitter_access_secret = await _get_setting("TWITTER_ACCESS_SECRET")
    # GEO platforms
    anthropic_key = await _get_setting("ANTHROPIC_API_KEY")
    google_ai_key = await _get_setting("GOOGLE_AI_API_KEY")
    geo_chatgpt = await _get_setting("OPENCMO_GEO_CHATGPT")
    # SEO
    pagespeed_key = await _get_setting("PAGESPEED_API_KEY")
    # Search (Tavily)
    tavily_key = await _get_setting("TAVILY_API_KEY")
    # SERP
    dataforseo_login = await _get_setting("DATAFORSEO_LOGIN")
    dataforseo_pass = await _get_setting("DATAFORSEO_PASSWORD")
    # Email
    smtp_host = await _get_setting("OPENCMO_SMTP_HOST")
    smtp_port = await _get_setting("OPENCMO_SMTP_PORT")
    smtp_user = await _get_setting("OPENCMO_SMTP_USER")
    smtp_pass = await _get_setting("OPENCMO_SMTP_PASS")
    report_email = await _get_setting("OPENCMO_REPORT_EMAIL")
    return JSONResponse({
        "api_key_set": bool(api_key),
        "api_key_masked": _mask_key(api_key),
        "base_url": base_url,
        "model": model,
        # Reddit
        "reddit_configured": bool(reddit_cid and reddit_secret and reddit_user and reddit_pass),
        "reddit_username": reddit_user,
        "auto_publish": auto_publish == "1",
        # Twitter
        "twitter_configured": bool(twitter_api_key and twitter_api_secret and twitter_access_token and twitter_access_secret),
        "twitter_api_key_masked": _mask_key(twitter_api_key),
        # GEO
        "anthropic_key_set": bool(anthropic_key),
        "anthropic_key_masked": _mask_key(anthropic_key),
        "google_ai_key_set": bool(google_ai_key),
        "google_ai_key_masked": _mask_key(google_ai_key),
        "geo_chatgpt_enabled": geo_chatgpt == "1",
        # SEO
        "pagespeed_key_set": bool(pagespeed_key),
        "pagespeed_key_masked": _mask_key(pagespeed_key),
        # Search (Tavily)
        "tavily_key_set": bool(tavily_key),
        "tavily_key_masked": _mask_key(tavily_key),
        # SERP
        "dataforseo_configured": bool(dataforseo_login and dataforseo_pass),
        "dataforseo_login": dataforseo_login,
        # Email
        "email_configured": bool(smtp_host and smtp_user and smtp_pass),
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
        "smtp_user": smtp_user,
        "report_email": report_email,
    })


_ALL_SETTING_KEYS = (
    "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENCMO_MODEL_DEFAULT",
    # Reddit
    "REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD",
    "OPENCMO_AUTO_PUBLISH",
    # Twitter
    "TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET",
    # GEO
    "ANTHROPIC_API_KEY", "GOOGLE_AI_API_KEY", "OPENCMO_GEO_CHATGPT",
    # SEO
    "PAGESPEED_API_KEY",
    # Search (Tavily)
    "TAVILY_API_KEY",
    # SERP
    "DATAFORSEO_LOGIN", "DATAFORSEO_PASSWORD",
    # Email
    "OPENCMO_SMTP_HOST", "OPENCMO_SMTP_PORT", "OPENCMO_SMTP_USER", "OPENCMO_SMTP_PASS",
    "OPENCMO_REPORT_EMAIL",
)


@app.post("/api/v1/settings")
async def api_v1_settings_save(request: Request):
    from opencmo import config
    body = await request.json()
    for key in _ALL_SETTING_KEYS:
        val = body.get(key)
        if val is not None:
            val = val.strip() if isinstance(val, str) else str(val)
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
