"""Projects API router — /api/v1/projects/**, /api/v1/overview, scan data endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from opencmo import storage

router = APIRouter(prefix="/api/v1")


@router.get("/projects")
async def api_v1_projects():
    from opencmo import service
    return JSONResponse(await service.get_status_summary())


@router.get("/projects/{project_id}")
async def api_v1_project(project_id: int):
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse(project)


@router.delete("/projects/{project_id}")
async def api_v1_delete_project(project_id: int):
    # Stop graph expansion if any
    await storage.update_expansion(project_id, desired_state="idle")
    ok = await storage.delete_project(project_id)
    if not ok:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse({"ok": True})


@router.post("/projects/{project_id}/pause")
async def api_v1_pause_project(project_id: int):
    # 1. Pause scheduled jobs
    jobs = await storage.list_scheduled_jobs()
    from opencmo.scheduler import sync_job_record
    for job in jobs:
        if job["project_id"] == project_id and job["enabled"]:
            await storage.update_scheduled_job(job["id"], enabled=False)
            job["enabled"] = False
            sync_job_record(job)
            
    # 2. Pause graph expansion
    expansion = await storage.get_expansion(project_id)
    if expansion and expansion["desired_state"] == "running":
        await storage.update_expansion(project_id, desired_state="paused")
        
    return JSONResponse({"ok": True, "status": "paused"})


@router.post("/projects/{project_id}/resume")
async def api_v1_resume_project(project_id: int):
    # 1. Resume scheduled jobs
    jobs = await storage.list_scheduled_jobs()
    from opencmo.scheduler import sync_job_record
    for job in jobs:
        if job["project_id"] == project_id and not job["enabled"]:
            await storage.update_scheduled_job(job["id"], enabled=True)
            job["enabled"] = True
            sync_job_record(job)
            
    # 2. Resume graph expansion
    from opencmo.web.routers.graph import api_v1_expansion_start
    await api_v1_expansion_start(project_id)
    
    return JSONResponse({"ok": True, "status": "running"})


@router.get("/overview")
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


@router.get("/projects/{project_id}/summary")
async def api_v1_project_summary(project_id: int):
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Not found"}, status_code=404)
        
    jobs = await storage.list_scheduled_jobs()
    project_jobs = [j for j in jobs if j["project_id"] == project_id]
    is_paused = len(project_jobs) > 0 and all(not j["enabled"] for j in project_jobs)
    
    latest = await storage.get_latest_scans(project_id)
    previous = await storage.get_previous_scans(project_id)
    monitoring = await storage.get_latest_monitoring_summary(project_id)
    latest_reports = await storage.get_latest_reports(project_id)
    return JSONResponse({
        "project": project,
        "is_paused": is_paused,
        "latest": latest,
        "previous": previous,
        "latest_monitoring": monitoring,
        "latest_reports": latest_reports,
    })


@router.get("/projects/{project_id}/next-actions")
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


# --- Scan data endpoints ---


@router.get("/projects/{project_id}/seo/history")
async def api_v1_seo_history(project_id: int):
    return JSONResponse(await storage.get_seo_history(project_id))


@router.get("/projects/{project_id}/seo/chart")
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


@router.get("/projects/{project_id}/geo/history")
async def api_v1_geo_history(project_id: int):
    return JSONResponse(await storage.get_geo_history(project_id))


@router.get("/projects/{project_id}/geo/chart")
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


@router.get("/projects/{project_id}/community/history")
async def api_v1_community_history(project_id: int):
    return JSONResponse(await storage.get_community_history(project_id))


@router.get("/projects/{project_id}/community/discussions")
async def api_v1_community_discussions(project_id: int):
    discussions = await storage.get_tracked_discussions(project_id)
    history = await storage.get_community_history(project_id, limit=1)
    if not history:
        return JSONResponse(discussions)

    latest_results = history[0].get("results_json", "")
    try:
        import json as _json

        payload = _json.loads(latest_results) if latest_results else {}
        latest_hits = {
            (hit["platform"], hit["detail_id"]): hit
            for hit in payload.get("hits", [])
        }
    except Exception:
        latest_hits = {}

    enriched = []
    tracked_keys: set[tuple[str, str]] = set()
    for discussion in discussions:
        key = (discussion["platform"], discussion["detail_id"])
        tracked_keys.add(key)
        latest = latest_hits.get(key, {})
        enriched.append({
            **discussion,
            "intent_type": latest.get("intent_type"),
            "match_reason": latest.get("match_reason"),
            "matched_query": latest.get("matched_query"),
            "matched_terms": latest.get("matched_terms"),
            "confidence": latest.get("confidence"),
            "source_kind": latest.get("source_kind"),
        })
    for index, ((platform, detail_id), latest) in enumerate(latest_hits.items(), start=1):
        if latest.get("source_kind") != "external_search" or (platform, detail_id) in tracked_keys:
            continue
        enriched.append({
            "id": -index,
            "platform": platform,
            "detail_id": detail_id,
            "title": latest.get("title", ""),
            "url": latest.get("url", ""),
            "first_seen_at": history[0]["scanned_at"],
            "last_checked_at": history[0]["scanned_at"],
            "raw_score": latest.get("raw_score"),
            "comments_count": latest.get("comments_count"),
            "engagement_score": latest.get("engagement_score"),
            "intent_type": latest.get("intent_type"),
            "match_reason": latest.get("match_reason"),
            "matched_query": latest.get("matched_query"),
            "matched_terms": latest.get("matched_terms"),
            "confidence": latest.get("confidence"),
            "source_kind": latest.get("source_kind"),
        })
    return JSONResponse(enriched)


@router.get("/projects/{project_id}/community/chart")
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


@router.get("/projects/{project_id}/serp/latest")
async def api_v1_serp_latest(project_id: int):
    return JSONResponse(await storage.get_all_serp_latest(project_id))


@router.get("/projects/{project_id}/serp/chart")
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
