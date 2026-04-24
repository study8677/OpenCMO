# AGENTS.md

## Architecture at a Glance

```
Frontend (React 19 + Vite)  ←→  FastAPI /api/v1/  ←→  SQLite (WAL)
                                      ↓
                              Background Worker
                                      ↓
                    ┌─────── 6-Stage Monitoring Pipeline ───────┐
                    │ 1. Context Build (crawl + 3-role AI debate)│
                    │ 2. Signal Collect (SEO/GEO/Community/SERP) │
                    │ 3. Signal Normalize                        │
                    │ 4. Domain Review (4 AI analysts)           │
                    │ 5. Strategy Synthesis                      │
                    │ 6. Persist & Publish                       │
                    └────────────────────────────────────────────┘
```

## Key Directories

| Path | Role |
|------|------|
| `src/opencmo/agents/` | 25+ specialist agents (CMO orchestrator + platform experts). Names must be ASCII — no Chinese. |
| `src/opencmo/tools/` | Crawl, search, SEO audit, GEO detection, community providers, SERP tracking |
| `src/opencmo/services/` | Domain services: intelligence (AI debate), approval, monitoring |
| `src/opencmo/background/` | Worker + executor registry (scan, report, graph expansion) |
| `src/opencmo/storage/` | Async SQLite, 30+ tables, no ORM |
| `src/opencmo/web/` | FastAPI app, routers, SSE chat, BYOK middleware |
| `src/opencmo/llm.py` | Centralized LLM client: ContextVar isolation, retry + backoff, model resolution |
| `frontend/src/` | React SPA: pages/, components/, hooks/ (TanStack Query), api/, i18n/ (EN/ZH/JA/KO/ES) |

## Critical Patterns

- **LLM calls**: Always use `llm.chat_completion_messages()` for retry. Never call `client.chat.completions.create()` directly.
- **Agent names**: ASCII only (`Zhihu Expert`, not `知乎专家`). openai-agents generates `transfer_to_{name}` tool names.
- **Timestamps**: SQLite stores UTC. Frontend must use `utcDate()` from `utils/time.ts` to parse.
- **Community search**: Tavily → crawl4ai Google scrape fallback. Skip category queries when category is placeholder `"auto"`.
- **BYOK**: Per-request API keys via `X-User-Keys` header → ContextVar. Background tasks capture and restore keys.
- **SPA routing**: No `AnimatePresence key={pathname}` in AppShell — causes full remount and breaks query cache.
- **Production topology**: Primary production is `newyork` (`192.3.16.77`). OpenCMO runs behind nginx on `80/443`, proxied to local `127.0.0.1:8081`. Nginx config: `/etc/nginx/sites-enabled/aidcmo.conf`.
- **Nginx security headers**: `Strict-Transport-Security` + `X-Frame-Options: DENY` configured in `aidcmo.conf`.
- **Port allocation**: Do not assume production app port is `8080`. `8080` is occupied by `sub2api` on `newyork`; OpenCMO uses `8081`.
- **BWG role**: `BWG` is no longer the primary OpenCMO host. Treat it as a lightweight box, temporary reverse proxy, or fallback node unless explicitly re-promoted.
- **Browser-backed scans**: SEO/context fallback paths use `crawl4ai`/Playwright. Fresh servers need browser binaries installed, or scans will fail with `BrowserType.launch` executable errors.

## Commands

```bash
# Backend
pip install -e ".[all]"        # Install
opencmo-web                    # Run locally (port 8080 by default)
pytest tests/                  # Test
ruff check src/ tests/         # Lint

# Frontend
cd frontend && npm install
npm run dev                    # Dev (port 5173, proxies /api → 8080)
npm run build                  # Prod build

# Deploy frontend assets to New York
cd frontend && npm run build   # Build locally (avoid server-side frontend builds)
rsync -avz --delete frontend/dist/ root@192.3.16.77:/opt/OpenCMO/frontend/dist/

# Deploy backend code to New York
rsync -avz --delete \
  --exclude '.git' \
  --exclude 'frontend/node_modules' \
  --exclude 'frontend/dist' \
  --exclude '.venv' \
  ./ root@192.3.16.77:/opt/OpenCMO/
ssh newyork "cd /opt/OpenCMO && source .venv/bin/activate && pip install -e . -q && systemctl restart opencmo"

# New York service / runtime checks
ssh newyork "systemctl status opencmo --no-pager"
ssh newyork "journalctl -u opencmo -n 200 --no-pager"
ssh newyork "ss -ltnp | grep -E ':80|:443|:8081'"

# Install Playwright browsers on New York when scan workers need them
ssh newyork "cd /opt/OpenCMO && .venv/bin/playwright install chromium"

# BWG is optional fallback / proxy only
ssh bwg "systemctl status nginx --no-pager"
```

## Coding Conventions

- **Python**: snake_case, 4-space indent, type hints where useful, line length 120 (ruff)
- **TypeScript**: strict mode, PascalCase components, useX hooks, double quotes
- **Commits**: `feat:` / `fix:` / `docs:` prefix, short imperative subject
- **i18n**: All user-facing strings via translation keys (EN/ZH/JA/KO/ES). Never hardcode.
- **Secrets**: `.env` or settings UI only. Never commit API keys or `.db` files.
