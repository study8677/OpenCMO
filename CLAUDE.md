# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenCMO is an open-source AI Chief Marketing Officer — a multi-agent system for indie hackers and startups. It monitors SEO/GEO/SERP/Community metrics, generates platform-specific content, and visualizes competitive landscapes via an interactive 3D knowledge graph.

## Architecture

**Full-stack: Python backend + React TypeScript frontend**

- **Backend** (`src/opencmo/`): FastAPI + openai-agents framework, SQLite storage
- **Frontend** (`frontend/`): React 19 SPA with Vite, Tailwind CSS 4, TanStack Query, Three.js
- **Entry points**: `opencmo` (CLI chatbot), `opencmo-web` (web dashboard on port 8080)

### Backend layers

- `agents/cmo.py` — Orchestrator with 40+ tools; delegates to 25+ specialist agents via `agent.as_tool()`. Two routing strategies: single-platform handoff (deep interaction) vs multi-channel tool calls (collects all outputs via campaign runs)
- `agents/*.py` — Platform experts + intelligence agents. Each is a standalone `Agent()` with `name`, `instructions`, `tools`, and `model=get_model("agent_name")`
- `tools/*.py` — Crawling, search (WebSearchTool → Tavily fallback → crawl4ai scrape), SEO audit, SERP tracking, GEO detection, community scraping, publishing
- `service.py` — Business logic bridge used by both CLI and Web: monitor CRUD, multi-agent URL analysis (3-round debate → JSON strategy), competitor discovery, approval workflow
- `storage.py` — Async SQLite (WAL mode, foreign keys) with 27+ tables. No ORM — raw aiosqlite with dict rows. Schema auto-created; migrations via `ALTER TABLE` + try/except. DB path: `OPENCMO_DB_PATH` or `~/.opencmo/data.db`
- `web/app.py` — FastAPI routes: REST API at `/api/v1/`, SPA serving at `/app/`, SSE chat streaming. Token auth via Bearer header or cookie (public prefixes: `/static/`, `/api/v1/auth/`, `/api/v1/health`)
- `config.py` — Model resolution cascade: `OPENCMO_MODEL_{AGENT}` > `OPENCMO_MODEL_DEFAULT` > `'gpt-4o'`. Returns `OpenAIChatCompletionsModel` for custom `OPENAI_BASE_URL` providers. `apply_runtime_settings()` loads API keys from DB settings table into `os.environ`
- `scheduler.py` — APScheduler (optional dep, graceful fallback). `run_scheduled_scan()` executes SEO/GEO/Community/SERP independently, not through agent framework
- `graph_expansion.py` — Wave-based BFS discovery of competitors and keywords. Heartbeat-tracked (60s stale window), backpressure via `MAX_OPS_PER_WAVE=20`
- `web/task_registry.py` — In-memory (not persisted) OrderedDict, max 100 tasks. Wraps async scan workflows with progress tracking
- `web/chat_sessions.py` — SQLite-backed chat history. Auto-titling from first message. Max 20 messages per session (truncated)

### Frontend layers

- `pages/` — Route-level components (Dashboard, SEO, GEO, SERP, Community, Graph, Chat, Approvals, Monitors)
- `components/` — Organized by domain: `charts/` (recharts + react-force-graph-3d), `chat/` (SSE streaming), `monitors/`, `auth/`, `layout/`, `dashboard/`, `project/`
- `hooks/` — TanStack Query hooks per domain (`useProjects`, `useSeoData`, `useGraphData`, etc.). Stale time 30s, retry 1. `useChat` manages local state + SSE via async generator
- `api/client.ts` — `apiFetch()` adds Bearer token, dispatches `opencmo:unauthorized` on 401. Domain modules export typed wrappers around `apiJson()`
- `i18n/` — React context-based EN + ZH translations
- Routing: React Router v7 at base `/app`. Provider stack: QueryClient → I18n → Auth → Router

### Key patterns

- **Agent tool vs handoff**: `.as_tool()` returns output to orchestrator; `handoff()` transfers control for direct user conversation
- **Optional deps with graceful fallback**: scheduler, web, publish, geo-premium, tavily all degrade gracefully if not installed
- **SSE chat protocol**: `POST /api/v1/chat` streams events — `delta` (text), `agent` (handoff), `tool_called`, `tool_output`, `final_output`
- **Provider-adaptive search**: Native WebSearchTool for OpenAI, Tavily if key present, crawl4ai Google scrape as last resort
- **Approval-first publishing**: Content queued with exact payload for human review; publish only after explicit approve. `OPENCMO_AUTO_PUBLISH=1` gates actual API calls
- **Settings table as runtime config**: Web UI settings panel writes to SQLite KV store; `apply_runtime_settings()` loads them into env vars at startup
- **Custom provider compatibility**: Disables OpenAI tracing for non-OpenAI providers to avoid 401 noise
- Frontend proxies `/api` to `http://127.0.0.1:8080` in dev (vite.config.ts)

## Commands

### Setup

```bash
pip install -e ".[all]"   # Install with all optional deps
crawl4ai-setup             # Initialize crawler (required once)
cp .env.example .env       # Configure API keys
```

### Backend

```bash
opencmo                    # Interactive CLI chatbot
opencmo-web                # Web dashboard (http://localhost:8080/app)
```

### Frontend

```bash
cd frontend
npm install
npm run dev                # Dev server at localhost:5173
npm run build              # Production build (tsc -b && vite build)
```

### Tests

```bash
pytest tests/              # Run all tests
pytest tests/test_web.py   # Run single test file
pytest tests/ -k "test_seo" # Run tests matching pattern
```

Tests use temp SQLite DBs (via `tmp_path`), reset in-memory state (task registry, chat sessions), and mock all external APIs. No real API integration tests.

## Environment Variables

Required: `OPENAI_API_KEY` (or equivalent for chosen provider)

Key optional variables — see `.env.example` for full list:
- `OPENCMO_MODEL_DEFAULT` / `OPENCMO_MODEL_{AGENT}` — model selection (cascade: per-agent > default > gpt-4o)
- `OPENAI_BASE_URL` — custom API provider (NVIDIA, DeepSeek, Ollama, etc.)
- `OPENCMO_DB_PATH` — SQLite database location (default: `~/.opencmo/data.db`)
- `OPENCMO_WEB_TOKEN` — dashboard auth token
- `ANTHROPIC_API_KEY`, `GOOGLE_AI_API_KEY` — extended GEO platforms
- `TAVILY_API_KEY` — structured web search
- `DATAFORSEO_LOGIN/PASSWORD` — SERP tracking
- `OPENCMO_AUTO_PUBLISH=1` + Reddit/Twitter credentials — auto-publishing
- `OPENCMO_SMTP_*` + `OPENCMO_REPORT_EMAIL` — email reports

## BWG Server Deployment (aidcmo.com)

**Server**: BandwagonHost VPS — `97.64.16.217`, SSH port `2222`, user `root`

```bash
ssh -p 2222 root@97.64.16.217
```

**Code location**: `/opt/OpenCMO/`
**systemd service**: `opencmo` (runs `opencmo-web` on port 8080)
**Database**: `/root/.opencmo/data.db`
**Config**: `/opt/OpenCMO/.env`

### Deploy latest code

```bash
ssh -p 2222 root@97.64.16.217 "
  cd /opt/OpenCMO &&
  git pull origin main &&
  pip install -e '.[all]' -q &&
  systemctl restart opencmo &&
  systemctl is-active opencmo
"
```

### Frontend build

The server has only 1GB RAM — `npm run build` will OOM. **Always build locally and rsync**:

```bash
cd frontend && npm run build
rsync -avz --delete dist/ root@97.64.16.217:/opt/OpenCMO/frontend/dist/ -e "ssh -p 2222"
```

### Nginx

- Config file: `/etc/nginx/conf.d/aidcmo.conf` (NOT `sites-enabled/` — nginx.conf only includes `conf.d/*.conf`)
- HTTPS via Let's Encrypt (certbot via snap, not apt)
- Proxies `https://aidcmo.com/` → `http://127.0.0.1:8080`
- To reload: `nginx -t && systemctl reload nginx`

### Key gotchas

- **nginx.conf includes only `conf.d/`** — putting configs in `sites-enabled/` has no effect on this server
- **Another server block (`724claw.conf`) was previously intercepting aidcmo.com** — check `conf.d/` for conflicting `server_name` entries if 502 appears unexpectedly
- **SPA is served from root `/`** — React Router `basename="/"`, Vite `base: "/"`, FastAPI catchall at `/{full_path:path}`
- **certbot must be installed via snap**, not apt (apt version has Python `requests_toolbelt` conflict)
