"""Legacy SSR HTML routes and chart JSON endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from opencmo import storage

router = APIRouter()

# Jinja2 templates (lazy import to avoid coupling with app.py)
_templates = None


def _get_templates():
    global _templates
    if _templates is None:
        from pathlib import Path

        from fastapi.templating import Jinja2Templates
        _templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))
    return _templates


# ---------------------------------------------------------------------------
# SSR HTML routes
# ---------------------------------------------------------------------------


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    projects = await storage.list_projects()
    project_data = []
    for p in projects:
        latest = await storage.get_latest_scans(p["id"])
        project_data.append({**p, "latest": latest})
    return _get_templates().TemplateResponse("dashboard.html", {"request": request, "projects": project_data})


@router.get("/project/{project_id}", response_class=HTMLResponse)
async def project_overview(request: Request, project_id: int):
    project = await storage.get_project(project_id)
    if not project:
        return HTMLResponse("Project not found", status_code=404)
    latest = await storage.get_latest_scans(project_id)
    seo_history = await storage.get_seo_history(project_id, limit=10)
    geo_history = await storage.get_geo_history(project_id, limit=10)
    discussions = await storage.get_tracked_discussions(project_id)
    return _get_templates().TemplateResponse("project.html", {
        "request": request,
        "project": project,
        "latest": latest,
        "seo_history": seo_history,
        "geo_history": geo_history,
        "discussions": discussions,
    })


@router.get("/project/{project_id}/seo", response_class=HTMLResponse)
async def project_seo(request: Request, project_id: int):
    project = await storage.get_project(project_id)
    if not project:
        return HTMLResponse("Project not found", status_code=404)
    history = await storage.get_seo_history(project_id, limit=20)
    return _get_templates().TemplateResponse("seo.html", {
        "request": request, "project": project, "history": history,
    })


@router.get("/project/{project_id}/geo", response_class=HTMLResponse)
async def project_geo(request: Request, project_id: int):
    project = await storage.get_project(project_id)
    if not project:
        return HTMLResponse("Project not found", status_code=404)
    history = await storage.get_geo_history(project_id, limit=20)
    return _get_templates().TemplateResponse("geo.html", {
        "request": request, "project": project, "history": history,
    })


@router.get("/project/{project_id}/serp", response_class=HTMLResponse)
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
    return _get_templates().TemplateResponse("serp.html", {
        "request": request,
        "project": project,
        "keywords": kw_data,
        "serp_history": serp_history,
    })


@router.get("/project/{project_id}/community", response_class=HTMLResponse)
async def project_community(request: Request, project_id: int):
    project = await storage.get_project(project_id)
    if not project:
        return HTMLResponse("Project not found", status_code=404)
    discussions = await storage.get_tracked_discussions(project_id)
    community_history = await storage.get_community_history(project_id, limit=10)
    return _get_templates().TemplateResponse("community.html", {
        "request": request, "project": project,
        "discussions": discussions, "community_history": community_history,
    })


# ---------------------------------------------------------------------------
# Legacy JSON API routes (Chart.js data sources)
# ---------------------------------------------------------------------------


@router.get("/api/project/{project_id}/seo-data")
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


@router.get("/api/project/{project_id}/geo-data")
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


@router.get("/api/project/{project_id}/serp-data")
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


@router.get("/api/project/{project_id}/community-data")
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
