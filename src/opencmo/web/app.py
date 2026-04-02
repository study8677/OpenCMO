"""FastAPI web dashboard for OpenCMO — Jinja2 SSR + REST API + SPA mount.

This module creates the ``app`` instance, registers auth middleware,
includes all domain routers, and provides the SPA catch-all route and
server entry point.
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import StreamingResponse

from opencmo import storage

_HERE = Path(__file__).parent
_SPA_DIR = _HERE.parent.parent.parent / "frontend" / "dist"  # <repo>/frontend/dist

app = FastAPI(title="OpenCMO Dashboard")
app.mount("/static", StaticFiles(directory=str(_HERE / "static")), name="static")
logger = logging.getLogger(__name__)


# In-memory expansion tracking (lightweight, no third task model)
_expansion_progress: dict[int, list[dict]] = {}   # project_id -> progress events
_expansion_tasks: dict[int, asyncio.Task] = {}     # project_id -> running asyncio.Task


# ---------------------------------------------------------------------------
# Lifecycle hooks
# ---------------------------------------------------------------------------


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
# BYOK middleware — per-user API key isolation
# ---------------------------------------------------------------------------

# Keys that can be injected from the X-User-Keys header
_INJECTABLE_KEYS = frozenset({
    "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENCMO_MODEL_DEFAULT",
    "TAVILY_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_AI_API_KEY",
    "PAGESPEED_API_KEY",
})


@app.middleware("http")
async def byok_middleware(request: Request, call_next):
    """Read per-user API keys from X-User-Keys header and inject via ContextVar.

    Uses ContextVar instead of os.environ for per-request key isolation,
    preventing race conditions where concurrent requests could overwrite
    each other's API keys.
    """
    raw = request.headers.get("X-User-Keys")
    if not raw:
        return await call_next(request)

    import base64
    import json as _json

    try:
        decoded = base64.b64decode(raw).decode()
        user_keys: dict = _json.loads(decoded)
    except Exception:
        return await call_next(request)

    # Filter to allowed keys only
    filtered = {
        k: v for k, v in user_keys.items()
        if k in _INJECTABLE_KEYS and isinstance(v, str) and v.strip()
    }
    if not filtered:
        return await call_next(request)

    # Inject into ContextVar (Task-local, no race condition)
    from opencmo import llm
    token = llm.set_request_keys(filtered)
    try:
        response = await call_next(request)
    finally:
        llm.reset_request_keys(token)

    return response


@app.get("/api/v1/health")
async def api_v1_health():
    from opencmo import scheduler

    return JSONResponse({
        "ok": True,
        "scheduler": scheduler.scheduler_status(),
    })


# ---------------------------------------------------------------------------
# Include domain routers
# ---------------------------------------------------------------------------

from opencmo.web.routers.legacy import router as legacy_router
from opencmo.web.routers.projects import router as projects_router
from opencmo.web.routers.graph import router as graph_router
from opencmo.web.routers.insights import router as insights_router
from opencmo.web.routers.keywords import router as keywords_router
from opencmo.web.routers.monitors import router as monitors_router
from opencmo.web.routers.campaigns import router as campaigns_router
from opencmo.web.routers.approvals import router as approvals_router
from opencmo.web.routers.tasks import router as tasks_router
from opencmo.web.routers.chat import router as chat_router
from opencmo.web.routers.settings import router as settings_router
from opencmo.web.routers.report import router as report_router
from opencmo.web.routers.events import router as events_router
from opencmo.web.routers.brand_kit import router as brand_kit_router
from opencmo.web.routers.performance import router as performance_router
from opencmo.web.routers.quick_actions import router as quick_actions_router

app.include_router(legacy_router)
app.include_router(projects_router)
app.include_router(graph_router)
app.include_router(insights_router)
app.include_router(keywords_router)
app.include_router(monitors_router)
app.include_router(campaigns_router)
app.include_router(approvals_router)
app.include_router(tasks_router)
app.include_router(chat_router)
app.include_router(settings_router)
app.include_router(report_router)
app.include_router(events_router)
app.include_router(brand_kit_router)
app.include_router(performance_router)
app.include_router(quick_actions_router)


# ---------------------------------------------------------------------------
# SPA mount — /app/ serves React frontend
# ---------------------------------------------------------------------------


@app.get("/app")
@app.get("/app/{full_path:path}")
async def spa_catchall(request: Request, full_path: str = ""):
    spa_root = _SPA_DIR.resolve()
    index = spa_root / "index.html"
    if not index.exists():
        return HTMLResponse(
            "<h1>Frontend not built</h1><p>Run <code>cd frontend && npm run build</code> to build the SPA.</p>",
            status_code=404,
        )
    # Serve static assets from dist
    if full_path and not full_path.startswith("index.html"):
        asset = (spa_root / full_path).resolve()
        if spa_root in asset.parents and asset.exists() and asset.is_file():
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
