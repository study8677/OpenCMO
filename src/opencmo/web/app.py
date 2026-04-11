"""FastAPI web dashboard for OpenCMO — Jinja2 SSR + REST API + SPA mount.

This module creates the ``app`` instance, registers auth middleware,
includes all domain routers, and provides the SPA catch-all route and
server entry point.
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
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

_BLOG_STATIC_SITE_COPY = """
<main id="static-site-copy">
  <header>
    <p>OpenCMO Blog</p>
    <h1>A public field guide to what OpenCMO is, who it is for, and how the system should be used</h1>
    <p>
      The OpenCMO blog explains why the workspace exists, when it becomes worth adopting,
      how the first 30 days should run, and which technical choices make the public site
      readable to both people and machines.
    </p>
  </header>
  <section>
    <h2>Start with these notes</h2>
    <ul>
      <li>Who should use OpenCMO, and when it starts paying for itself</li>
      <li>Your first 30 days with OpenCMO: a practical rollout plan</li>
      <li>Why we refused to build another marketing dashboard</li>
      <li>How to make your site readable to Google and AI agents</li>
    </ul>
  </section>
  <section>
    <h2>Why this page exists</h2>
    <p>
      The blog is part of the public product surface. It helps buyers, operators,
      search engines, and AI agents understand what OpenCMO does without entering
      the private workspace routes.
    </p>
  </section>
</main>
""".strip()

_BLOG_JSON_LD = json.dumps(
    {
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": "OpenCMO Blog",
        "description": (
            "A public field guide to what OpenCMO is, who it is for, and how the system "
            "should be used."
        ),
        "url": "https://www.aidcmo.com/blog",
        "publisher": {
            "@type": "Organization",
            "name": "OpenCMO",
            "url": "https://www.aidcmo.com/",
        },
        "blogPost": [
            {
                "@type": "BlogPosting",
                "headline": "Why we refused to build another marketing dashboard",
                "url": "https://www.aidcmo.com/blog#ai-cmo-workspace",
                "description": (
                    "Why OpenCMO is designed as a visibility workspace instead of another "
                    "collection of disconnected charts."
                ),
            },
            {
                "@type": "BlogPosting",
                "headline": "Why SEO, GEO, SERP, and community signals belong in the same war room",
                "url": "https://www.aidcmo.com/blog#visibility-operating-system",
                "description": (
                    "Why modern brand discovery has to be monitored across search, AI, "
                    "SERP language, and public discussion at the same time."
                ),
            },
            {
                "@type": "BlogPosting",
                "headline": "How to make one site readable to Google, AI agents, and humans",
                "url": "https://www.aidcmo.com/blog#crawler-readable-brand-surface",
                "description": (
                    "How homepage copy, metadata, sitemap, and llms.txt work together to "
                    "make a product easier to parse and recommend."
                ),
            },
            {
                "@type": "BlogPosting",
                "headline": "Inside OpenCMO: what the workspace actually contains",
                "url": "https://www.aidcmo.com/blog#inside-opencmo-workspace",
                "description": (
                    "A walkthrough of the monitoring, review, context, and execution "
                    "surfaces inside the OpenCMO workspace."
                ),
            },
            {
                "@type": "BlogPosting",
                "headline": "Who should use OpenCMO, and when it starts paying for itself",
                "url": "https://www.aidcmo.com/blog#who-should-use-opencmo",
                "description": (
                    "A buyer-oriented note on when fragmented visibility work becomes large "
                    "enough to justify a dedicated operating layer."
                ),
            },
            {
                "@type": "BlogPosting",
                "headline": "Your first 30 days with OpenCMO: a practical rollout plan",
                "url": "https://www.aidcmo.com/blog#first-30-days-with-opencmo",
                "description": (
                    "A practical onboarding sequence for the first scans, reviews, and "
                    "execution loops inside OpenCMO."
                ),
            },
        ],
    },
    separators=(",", ":"),
)


def _apply_public_route_metadata(html: str, full_path: str) -> str:
    normalized = full_path.strip("/")
    if normalized != "blog":
        return html

    replacements = [
        (
            r"<title>.*?</title>",
            "<title>OpenCMO Blog | Field Guide to Visibility Operations and OpenCMO</title>",
        ),
        (
            r'<meta\s+name="description"\s+content="[^"]*"\s*/?>',
            '<meta name="description" content="Read the public OpenCMO field guide covering adoption fit, first-30-day rollout, crawler-readable surfaces, and visibility operations." />',
        ),
        (
            r'<link\s+rel="canonical"\s+href="[^"]*"\s*/?>',
            '<link rel="canonical" href="https://www.aidcmo.com/blog" />',
        ),
        (
            r'<meta\s+property="og:title"\s+content="[^"]*"\s*/?>',
            '<meta property="og:title" content="OpenCMO Blog | Field Guide to Visibility Operations and OpenCMO" />',
        ),
        (
            r'<meta\s+property="og:description"\s+content="[^"]*"\s*/?>',
            '<meta property="og:description" content="Read the public OpenCMO field guide covering adoption fit, rollout, crawler-readable surfaces, and visibility operations." />',
        ),
        (
            r'<meta\s+property="og:url"\s+content="[^"]*"\s*/?>',
            '<meta property="og:url" content="https://www.aidcmo.com/blog" />',
        ),
        (
            r'<meta\s+name="twitter:title"\s+content="[^"]*"\s*/?>',
            '<meta name="twitter:title" content="OpenCMO Blog | Field Guide to Visibility Operations and OpenCMO" />',
        ),
        (
            r'<meta\s+name="twitter:description"\s+content="[^"]*"\s*/?>',
            '<meta name="twitter:description" content="Read the public OpenCMO field guide covering adoption fit, rollout, crawler-readable surfaces, and visibility operations." />',
        ),
        (
            r'<script\s+type="application/ld\+json">.*?</script>',
            f'<script type="application/ld+json">{_BLOG_JSON_LD}</script>',
        ),
    ]

    rendered = html
    for pattern, replacement in replacements:
        rendered = re.sub(pattern, replacement, rendered, count=1, flags=re.IGNORECASE)

    return re.sub(
        r'<main id="static-site-copy">.*?</main>',
        _BLOG_STATIC_SITE_COPY,
        rendered,
        count=1,
        flags=re.DOTALL,
    )


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

    # Load DB-stored API settings into os.environ so background workers can read them.
    from opencmo.config import apply_runtime_settings
    await apply_runtime_settings()
    logger.info("Runtime settings loaded from DB into environment")


@app.on_event("startup")
async def _startup_runtime_services():
    """Start optional runtime services after DB bootstrap."""
    from opencmo import scheduler
    from opencmo.background.executors import (
        run_github_enrich_executor,
        run_graph_expansion_executor,
        run_report_executor,
        run_scan_executor,
    )
    from opencmo.background.worker import get_background_worker

    worker = get_background_worker()
    worker.register_executor("scan", run_scan_executor)
    worker.register_executor("report", run_report_executor)
    worker.register_executor("graph_expansion", run_graph_expansion_executor)
    worker.register_executor("github_enrich", run_github_enrich_executor)
    await worker.start()

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
    from opencmo.background.worker import get_background_worker

    await get_background_worker().stop()
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

from opencmo.web.routers.approvals import router as approvals_router
from opencmo.web.routers.brand_kit import router as brand_kit_router
from opencmo.web.routers.campaigns import router as campaigns_router
from opencmo.web.routers.chat import router as chat_router
from opencmo.web.routers.events import router as events_router
from opencmo.web.routers.github import router as github_router
from opencmo.web.routers.graph import router as graph_router
from opencmo.web.routers.insights import router as insights_router
from opencmo.web.routers.keywords import router as keywords_router
from opencmo.web.routers.legacy import router as legacy_router
from opencmo.web.routers.monitors import router as monitors_router
from opencmo.web.routers.performance import router as performance_router
from opencmo.web.routers.projects import router as projects_router
from opencmo.web.routers.quick_actions import router as quick_actions_router
from opencmo.web.routers.report import router as report_router
from opencmo.web.routers.settings import router as settings_router
from opencmo.web.routers.site import router as site_router
from opencmo.web.routers.tasks import router as tasks_router

app.include_router(legacy_router, prefix="/legacy")
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
app.include_router(site_router)
app.include_router(report_router)
app.include_router(events_router)
app.include_router(brand_kit_router)
app.include_router(performance_router)
app.include_router(quick_actions_router)
app.include_router(github_router)


# ---------------------------------------------------------------------------
# SPA mount — /app/ serves React frontend
# ---------------------------------------------------------------------------


@app.get("/")
@app.get("/{full_path:path}")
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

    new_visitor_id: str | None = None
    try:
        await storage.increment_site_counter("total_visits")
        if not request.cookies.get("opencmo_visitor_id"):
            new_visitor_id = uuid.uuid4().hex
            await storage.increment_site_counter("unique_visitors")
    except Exception:
        logger.exception("Failed to record site visit counters")

    rendered_html = _apply_public_route_metadata(index.read_text(), full_path)

    # SPA fallback — always return index.html
    response = HTMLResponse(rendered_html)
    if new_visitor_id:
        response.set_cookie(
            "opencmo_visitor_id",
            new_visitor_id,
            max_age=60 * 60 * 24 * 365,
            httponly=True,
            samesite="lax",
            secure=request.url.scheme == "https",
        )
    return response


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------


def run_server(port: int = 8080):
    import uvicorn

    load_dotenv()
    host = os.environ.get("OPENCMO_WEB_HOST", "127.0.0.1")
    uvicorn.run(app, host=host, port=port)
