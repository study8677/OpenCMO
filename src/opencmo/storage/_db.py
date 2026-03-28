"""Database core — schema, migrations, and connection management."""

from __future__ import annotations

import json
import os
from pathlib import Path

import aiosqlite

_DB_PATH = Path(os.environ.get("OPENCMO_DB_PATH", Path.home() / ".opencmo" / "data.db"))
_SCHEMA_READY_FOR: Path | None = None

_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_name TEXT NOT NULL,
    url TEXT NOT NULL,
    category TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(brand_name, url)
);

CREATE TABLE IF NOT EXISTS seo_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    url TEXT NOT NULL,
    scanned_at TEXT NOT NULL DEFAULT (datetime('now')),
    report_json TEXT NOT NULL,
    score_performance REAL,
    score_lcp REAL,
    score_cls REAL,
    score_tbt REAL,
    has_robots_txt INTEGER,
    has_sitemap INTEGER,
    has_schema_org INTEGER
);

CREATE TABLE IF NOT EXISTS geo_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    scanned_at TEXT NOT NULL DEFAULT (datetime('now')),
    geo_score INTEGER NOT NULL,
    visibility_score INTEGER,
    position_score INTEGER,
    sentiment_score INTEGER,
    platform_results_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS community_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    scanned_at TEXT NOT NULL DEFAULT (datetime('now')),
    total_hits INTEGER,
    results_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tracked_discussions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    platform TEXT NOT NULL,
    detail_id TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_checked_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(project_id, platform, detail_id)
);

CREATE TABLE IF NOT EXISTS discussion_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discussion_id INTEGER NOT NULL REFERENCES tracked_discussions(id),
    checked_at TEXT NOT NULL DEFAULT (datetime('now')),
    raw_score INTEGER NOT NULL,
    comments_count INTEGER NOT NULL,
    engagement_score INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS scheduled_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    job_type TEXT NOT NULL,
    cron_expr TEXT NOT NULL DEFAULT '0 9 * * *',
    enabled INTEGER NOT NULL DEFAULT 1,
    last_run_at TEXT,
    next_run_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tracked_keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    keyword TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(project_id, keyword)
);

CREATE TABLE IF NOT EXISTS serp_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    keyword TEXT NOT NULL,
    position INTEGER,
    url_found TEXT,
    provider TEXT NOT NULL,
    error TEXT,
    checked_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT '',
    input_items TEXT NOT NULL DEFAULT '[]',
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    channel TEXT NOT NULL,
    approval_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    title TEXT NOT NULL DEFAULT '',
    target_label TEXT NOT NULL DEFAULT '',
    target_url TEXT NOT NULL DEFAULT '',
    agent_name TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    preview_json TEXT NOT NULL DEFAULT '{}',
    publish_result_json TEXT,
    decision_note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    decided_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_approvals_status_created_at
ON approvals(status, created_at DESC);

CREATE TABLE IF NOT EXISTS competitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    name TEXT NOT NULL,
    url TEXT,
    category TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(project_id, name)
);

CREATE TABLE IF NOT EXISTS competitor_keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competitor_id INTEGER NOT NULL REFERENCES competitors(id),
    keyword TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(competitor_id, keyword)
);

CREATE TABLE IF NOT EXISTS scan_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL UNIQUE,
    monitor_id INTEGER,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    job_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    summary TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS scan_run_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES scan_runs(id),
    stage TEXT NOT NULL,
    agent TEXT,
    status TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    detail TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS scan_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES scan_runs(id),
    domain TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    confidence REAL,
    evidence_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS scan_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES scan_runs(id),
    domain TEXT NOT NULL,
    priority TEXT NOT NULL,
    owner_type TEXT NOT NULL,
    action_type TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    rationale TEXT NOT NULL,
    confidence REAL,
    evidence_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS graph_expansions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) UNIQUE,
    desired_state TEXT NOT NULL DEFAULT 'idle',
    runtime_state TEXT NOT NULL DEFAULT 'idle',
    current_wave INTEGER NOT NULL DEFAULT 0,
    nodes_discovered INTEGER NOT NULL DEFAULT 0,
    nodes_explored INTEGER NOT NULL DEFAULT 0,
    heartbeat_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS graph_expansion_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    node_type TEXT NOT NULL,
    db_row_id INTEGER NOT NULL,
    wave_discovered INTEGER NOT NULL DEFAULT 0,
    explored INTEGER NOT NULL DEFAULT 0,
    priority INTEGER NOT NULL DEFAULT 50,
    reason TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(project_id, node_type, db_row_id)
);

CREATE TABLE IF NOT EXISTS graph_expansion_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    source_type TEXT NOT NULL,
    source_db_id INTEGER NOT NULL,
    target_type TEXT NOT NULL,
    target_db_id INTEGER NOT NULL,
    relation TEXT NOT NULL,
    wave INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(project_id, target_type, target_db_id)
);

CREATE TABLE IF NOT EXISTS campaign_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    goal TEXT NOT NULL,
    channels TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'drafting',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS campaign_artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES campaign_runs(id),
    artifact_type TEXT NOT NULL,
    channel TEXT,
    title TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS trend_briefings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id),
    topic TEXT NOT NULL,
    mode TEXT NOT NULL DEFAULT 'summary',
    platforms_queried TEXT NOT NULL,
    time_window_days INTEGER NOT NULL DEFAULT 30,
    total_hits INTEGER NOT NULL,
    briefing_markdown TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    insight_type TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'info',
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    action_type TEXT NOT NULL DEFAULT 'navigate',
    action_params TEXT NOT NULL DEFAULT '{}',
    read INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_insights_project_read
ON insights(project_id, read, created_at DESC);

CREATE TABLE IF NOT EXISTS citability_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    url TEXT NOT NULL,
    scanned_at TEXT NOT NULL DEFAULT (datetime('now')),
    avg_score REAL NOT NULL,
    top_blocks_json TEXT NOT NULL DEFAULT '[]',
    bottom_blocks_json TEXT NOT NULL DEFAULT '[]',
    grade_distribution_json TEXT NOT NULL DEFAULT '{}',
    report_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_crawler_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    url TEXT NOT NULL,
    scanned_at TEXT NOT NULL DEFAULT (datetime('now')),
    blocked_count INTEGER NOT NULL DEFAULT 0,
    total_crawlers INTEGER NOT NULL DEFAULT 14,
    has_llms_txt INTEGER,
    results_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS brand_presence_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    brand_name TEXT NOT NULL,
    scanned_at TEXT NOT NULL DEFAULT (datetime('now')),
    footprint_score INTEGER NOT NULL DEFAULT 0,
    platforms_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    kind TEXT NOT NULL,
    audience TEXT NOT NULL,
    version INTEGER NOT NULL,
    is_latest INTEGER NOT NULL DEFAULT 1,
    source_run_id INTEGER REFERENCES scan_runs(id),
    window_start TEXT,
    window_end TEXT,
    generation_status TEXT NOT NULL DEFAULT 'completed',
    content TEXT NOT NULL DEFAULT '',
    content_html TEXT NOT NULL DEFAULT '',
    meta_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_reports_project_kind_audience_version
ON reports(project_id, kind, audience, version);

CREATE INDEX IF NOT EXISTS idx_reports_project_latest
ON reports(project_id, kind, audience, is_latest, created_at DESC);
"""


async def ensure_db() -> None:
    """Create the database and schema once per process and DB path."""
    global _SCHEMA_READY_FOR
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if _SCHEMA_READY_FOR == _DB_PATH and _DB_PATH.exists():
        return

    db = await aiosqlite.connect(str(_DB_PATH))
    try:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")
        await db.executescript(_SCHEMA)
        # Migrations for existing databases
        for col, default in [("priority", "50"), ("reason", "''")]:
            try:
                await db.execute(
                    f"ALTER TABLE graph_expansion_nodes ADD COLUMN {col} "
                    f"{'INTEGER' if col == 'priority' else 'TEXT'} NOT NULL DEFAULT {default}"
                )
            except Exception:
                pass  # column already exists
        # Add convergence and scoring columns
        for table, col, col_type, default in [
            ("tracked_discussions", "convergence_cluster_id", "TEXT", None),
            ("discussion_snapshots", "velocity", "REAL", None),
            ("discussion_snapshots", "text_relevance", "REAL", None),
        ]:
            try:
                stmt = f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"
                if default is not None:
                    stmt += f" DEFAULT {default}"
                await db.execute(stmt)
            except Exception:
                pass
        # Autopilot: add execution tracking columns to insights
        for col, col_type, default in [
            ("execution_status", "TEXT", "'none'"),
            ("linked_approval_id", "INTEGER", None),
            ("execution_context", "TEXT", "'{}'"),
        ]:
            try:
                stmt = f"ALTER TABLE insights ADD COLUMN {col} {col_type}"
                if default is not None:
                    stmt += f" NOT NULL DEFAULT {default}"
                await db.execute(stmt)
            except Exception:
                pass

        # Autopilot: add source tracking columns to approvals
        for col, col_type, default in [
            ("source_insight_id", "INTEGER", None),
            ("pre_metrics_json", "TEXT", "'{}'"),
            ("post_metrics_json", "TEXT", "'{}'"),
        ]:
            try:
                stmt = f"ALTER TABLE approvals ADD COLUMN {col} {col_type}"
                if default is not None:
                    stmt += f" DEFAULT {default}"
                await db.execute(stmt)
            except Exception:
                pass

        # Autopilot: add autopilot flag to scheduled_jobs
        try:
            await db.execute("ALTER TABLE scheduled_jobs ADD COLUMN autopilot INTEGER NOT NULL DEFAULT 1")
        except Exception:
            pass

        # Chat sessions: keep optional project association for project-scoped chat.
        try:
            await db.execute("ALTER TABLE chat_sessions ADD COLUMN project_id INTEGER REFERENCES projects(id)")
        except Exception:
            pass

        await db.commit()
        _SCHEMA_READY_FOR = _DB_PATH
    finally:
        await db.close()


async def get_db() -> aiosqlite.Connection:
    """Open the database with WAL mode and foreign keys enabled."""
    await ensure_db()
    db = await aiosqlite.connect(str(_DB_PATH))
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db
