"""Database core — schema, versioned migrations, and connection management."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)

_DB_PATH = Path(os.environ.get("OPENCMO_DB_PATH", Path.home() / ".opencmo" / "data.db"))
_SCHEMA_READY_FOR: Path | None = None

_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

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
    has_schema_org INTEGER,
    seo_health_score REAL   -- multi-dimensional health score 0-100 (v9+)
);

CREATE TABLE IF NOT EXISTS geo_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    scanned_at TEXT NOT NULL DEFAULT (datetime('now')),
    geo_score INTEGER,            -- NULL = all providers errored (v9+)
    visibility_score INTEGER,
    position_score INTEGER,
    sentiment_score INTEGER,
    crawl_success_rate REAL,      -- fraction of providers that returned data (v9+)
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
    convergence_cluster_id TEXT,
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
    engagement_score INTEGER NOT NULL,
    velocity REAL,
    text_relevance REAL
);

CREATE TABLE IF NOT EXISTS scheduled_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    job_type TEXT NOT NULL,
    cron_expr TEXT NOT NULL DEFAULT '0 9 * * *',
    enabled INTEGER NOT NULL DEFAULT 1,
    autopilot INTEGER NOT NULL DEFAULT 1,
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

CREATE TABLE IF NOT EXISTS site_counters (
    key TEXT PRIMARY KEY,
    value INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
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
    source_insight_id INTEGER,
    pre_metrics_json TEXT DEFAULT '{}',
    post_metrics_json TEXT DEFAULT '{}',
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

CREATE INDEX IF NOT EXISTS idx_competitor_keywords_competitor_id
ON competitor_keywords(competitor_id);

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
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_scan_findings_run_id
ON scan_findings(run_id);

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
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_scan_recommendations_run_id
ON scan_recommendations(run_id);

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
    execution_status TEXT NOT NULL DEFAULT 'none',
    linked_approval_id INTEGER,
    execution_context TEXT NOT NULL DEFAULT '{}',
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

CREATE TABLE IF NOT EXISTS brand_kits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL UNIQUE REFERENCES projects(id),
    tone_of_voice TEXT NOT NULL DEFAULT '',
    target_audience TEXT NOT NULL DEFAULT '',
    core_values TEXT NOT NULL DEFAULT '',
    forbidden_words TEXT NOT NULL DEFAULT '[]',
    best_examples TEXT NOT NULL DEFAULT '',
    custom_instructions TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS manual_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    platform TEXT NOT NULL DEFAULT 'other',
    url TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    metrics_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS background_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL,
    project_id INTEGER REFERENCES projects(id),
    status TEXT NOT NULL DEFAULT 'queued',
    payload_json TEXT NOT NULL DEFAULT '{}',
    result_json TEXT NOT NULL DEFAULT '{}',
    error_json TEXT NOT NULL DEFAULT '{}',
    dedupe_key TEXT,
    priority INTEGER NOT NULL DEFAULT 50,
    run_after TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    worker_id TEXT,
    claimed_at TEXT,
    heartbeat_at TEXT,
    started_at TEXT,
    completed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS background_task_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL REFERENCES background_tasks(task_id),
    event_type TEXT NOT NULL,
    phase TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_background_tasks_status_priority
ON background_tasks(status, priority, run_after, created_at);

CREATE INDEX IF NOT EXISTS idx_background_tasks_project_created
ON background_tasks(project_id, created_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_background_tasks_dedupe_active
ON background_tasks(dedupe_key)
WHERE dedupe_key IS NOT NULL
  AND status IN ('queued', 'claimed', 'running', 'cancel_requested');

CREATE INDEX IF NOT EXISTS idx_background_task_events_task_id
ON background_task_events(task_id, id);

-- Indexes for hot scan query paths (ORDER BY scanned_at/checked_at DESC)
CREATE INDEX IF NOT EXISTS idx_seo_scans_project_date
ON seo_scans(project_id, scanned_at DESC);

CREATE INDEX IF NOT EXISTS idx_geo_scans_project_date
ON geo_scans(project_id, scanned_at DESC);

CREATE INDEX IF NOT EXISTS idx_community_scans_project_date
ON community_scans(project_id, scanned_at DESC);

CREATE INDEX IF NOT EXISTS idx_serp_snapshots_project_keyword_date
ON serp_snapshots(project_id, keyword, checked_at DESC);

CREATE INDEX IF NOT EXISTS idx_scan_runs_project_date
ON scan_runs(project_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_projects_brand_name
ON projects(brand_name COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS github_leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    login TEXT NOT NULL,
    github_id INTEGER,
    name TEXT NOT NULL DEFAULT '',
    bio TEXT NOT NULL DEFAULT '',
    company TEXT NOT NULL DEFAULT '',
    location TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    blog TEXT NOT NULL DEFAULT '',
    twitter_username TEXT NOT NULL DEFAULT '',
    hireable INTEGER,
    followers INTEGER NOT NULL DEFAULT 0,
    following INTEGER NOT NULL DEFAULT 0,
    public_repos INTEGER NOT NULL DEFAULT 0,
    created_at_gh TEXT NOT NULL DEFAULT '',
    top_languages TEXT NOT NULL DEFAULT '[]',
    total_stars INTEGER NOT NULL DEFAULT 0,
    top_repos_json TEXT NOT NULL DEFAULT '[]',
    source TEXT NOT NULL DEFAULT '',
    seed_username TEXT NOT NULL DEFAULT '',
    outreach_score REAL NOT NULL DEFAULT 0,
    outreach_status TEXT NOT NULL DEFAULT 'not_contacted',
    outreach_channel TEXT NOT NULL DEFAULT '',
    outreach_note TEXT NOT NULL DEFAULT '',
    enriched INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(project_id, login)
);

CREATE INDEX IF NOT EXISTS idx_github_leads_project_score
ON github_leads(project_id, outreach_score DESC);

CREATE INDEX IF NOT EXISTS idx_github_leads_project_status
ON github_leads(project_id, outreach_status);

CREATE TABLE IF NOT EXISTS github_discovery_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    task_id TEXT NOT NULL,
    seed_username TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'both',
    max_hops INTEGER NOT NULL DEFAULT 1,
    total_discovered INTEGER NOT NULL DEFAULT 0,
    total_enriched INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'running',
    error TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT
);
"""

# ---------------------------------------------------------------------------
# Versioned migrations — each entry is (version, description, sql_list).
# Runs once per version; progress tracked in ``schema_version`` table.
# All columns here are also in _SCHEMA so new databases start complete.
# These migrations only run for DBs created before the columns were added.
# ---------------------------------------------------------------------------

_MIGRATIONS: list[tuple[int, str, list[str]]] = [
    (1, "graph expansion node priority/reason", [
        "ALTER TABLE graph_expansion_nodes ADD COLUMN priority INTEGER NOT NULL DEFAULT 50",
        "ALTER TABLE graph_expansion_nodes ADD COLUMN reason TEXT NOT NULL DEFAULT ''",
    ]),
    (2, "discussion convergence and scoring columns", [
        "ALTER TABLE tracked_discussions ADD COLUMN convergence_cluster_id TEXT",
        "ALTER TABLE discussion_snapshots ADD COLUMN velocity REAL",
        "ALTER TABLE discussion_snapshots ADD COLUMN text_relevance REAL",
    ]),
    (3, "autopilot execution tracking on insights", [
        "ALTER TABLE insights ADD COLUMN execution_status TEXT NOT NULL DEFAULT 'none'",
        "ALTER TABLE insights ADD COLUMN linked_approval_id INTEGER",
        "ALTER TABLE insights ADD COLUMN execution_context TEXT NOT NULL DEFAULT '{}'",
    ]),
    (4, "autopilot source tracking on approvals", [
        "ALTER TABLE approvals ADD COLUMN source_insight_id INTEGER",
        "ALTER TABLE approvals ADD COLUMN pre_metrics_json TEXT DEFAULT '{}'",
        "ALTER TABLE approvals ADD COLUMN post_metrics_json TEXT DEFAULT '{}'",
    ]),
    (5, "autopilot flag on scheduled_jobs", [
        "ALTER TABLE scheduled_jobs ADD COLUMN autopilot INTEGER NOT NULL DEFAULT 1",
    ]),
    (6, "project-scoped chat sessions", [
        "ALTER TABLE chat_sessions ADD COLUMN project_id INTEGER REFERENCES projects(id)",
    ]),
    (7, "scan table indexes for hot query paths", [
        "CREATE INDEX IF NOT EXISTS idx_seo_scans_project_date ON seo_scans(project_id, scanned_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_geo_scans_project_date ON geo_scans(project_id, scanned_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_community_scans_project_date ON community_scans(project_id, scanned_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_serp_snapshots_project_keyword_date ON serp_snapshots(project_id, keyword, checked_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_scan_runs_project_date ON scan_runs(project_id, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_projects_brand_name ON projects(brand_name COLLATE NOCASE)",
    ]),
    (8, "dedupe partial unique index on background_tasks", [
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_background_tasks_dedupe_active ON background_tasks(dedupe_key) WHERE dedupe_key IS NOT NULL AND status IN ('queued', 'claimed', 'running', 'cancel_requested')",
    ]),
    (9, "seo_health_score and geo crawl_success_rate columns", [
        "ALTER TABLE seo_scans ADD COLUMN seo_health_score REAL",
        "ALTER TABLE geo_scans ADD COLUMN crawl_success_rate REAL",
    ]),
    (10, "finding and recommendation metadata json columns", [
        "ALTER TABLE scan_findings ADD COLUMN metadata_json TEXT NOT NULL DEFAULT '{}'",
        "ALTER TABLE scan_recommendations ADD COLUMN metadata_json TEXT NOT NULL DEFAULT '{}'",
    ]),
    (11, "github leads and discovery runs tables", [
        """CREATE TABLE IF NOT EXISTS github_leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES projects(id),
            login TEXT NOT NULL,
            github_id INTEGER,
            name TEXT NOT NULL DEFAULT '',
            bio TEXT NOT NULL DEFAULT '',
            company TEXT NOT NULL DEFAULT '',
            location TEXT NOT NULL DEFAULT '',
            email TEXT NOT NULL DEFAULT '',
            blog TEXT NOT NULL DEFAULT '',
            twitter_username TEXT NOT NULL DEFAULT '',
            hireable INTEGER,
            followers INTEGER NOT NULL DEFAULT 0,
            following INTEGER NOT NULL DEFAULT 0,
            public_repos INTEGER NOT NULL DEFAULT 0,
            created_at_gh TEXT NOT NULL DEFAULT '',
            top_languages TEXT NOT NULL DEFAULT '[]',
            total_stars INTEGER NOT NULL DEFAULT 0,
            top_repos_json TEXT NOT NULL DEFAULT '[]',
            source TEXT NOT NULL DEFAULT '',
            seed_username TEXT NOT NULL DEFAULT '',
            outreach_score REAL NOT NULL DEFAULT 0,
            outreach_status TEXT NOT NULL DEFAULT 'not_contacted',
            outreach_channel TEXT NOT NULL DEFAULT '',
            outreach_note TEXT NOT NULL DEFAULT '',
            enriched INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(project_id, login)
        )""",
        "CREATE INDEX IF NOT EXISTS idx_github_leads_project_score ON github_leads(project_id, outreach_score DESC)",
        "CREATE INDEX IF NOT EXISTS idx_github_leads_project_status ON github_leads(project_id, outreach_status)",
        """CREATE TABLE IF NOT EXISTS github_discovery_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES projects(id),
            task_id TEXT NOT NULL,
            seed_username TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'both',
            max_hops INTEGER NOT NULL DEFAULT 1,
            total_discovered INTEGER NOT NULL DEFAULT 0,
            total_enriched INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'running',
            error TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            completed_at TEXT
        )""",
    ]),
    (12, "site counters table", [
        """CREATE TABLE IF NOT EXISTS site_counters (
            key TEXT PRIMARY KEY,
            value INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )""",
    ]),
]

_LATEST_VERSION = _MIGRATIONS[-1][0]


async def _get_schema_version(db: aiosqlite.Connection) -> int:
    """Read current schema version, or 0 if the table doesn't exist yet."""
    try:
        cursor = await db.execute("SELECT MAX(version) FROM schema_version")
        row = await cursor.fetchone()
        return row[0] if row and row[0] is not None else 0
    except Exception:
        return 0


async def _get_table_columns(db: aiosqlite.Connection, table_name: str) -> set[str]:
    """Return the column names for a table."""
    cursor = await db.execute(f"PRAGMA table_info({table_name})")
    rows = await cursor.fetchall()
    return {row[1] for row in rows}


def _is_idempotent_migration_error(exc: Exception) -> bool:
    """Allow safe re-runs when a column or index already exists."""
    message = str(exc).lower()
    return "duplicate column name" in message or "already exists" in message


async def _reconcile_required_columns(db: aiosqlite.Connection) -> None:
    """Repair historical schema drift even when schema_version is already current."""
    required_columns = {
        "seo_scans": {"seo_health_score": "ALTER TABLE seo_scans ADD COLUMN seo_health_score REAL"},
        "geo_scans": {"crawl_success_rate": "ALTER TABLE geo_scans ADD COLUMN crawl_success_rate REAL"},
    }

    for table_name, columns in required_columns.items():
        existing_columns = await _get_table_columns(db, table_name)
        for column_name, statement in columns.items():
            if column_name not in existing_columns:
                await db.execute(statement)


async def _run_migrations(db: aiosqlite.Connection) -> None:
    """Apply pending migrations, skipping already-applied columns gracefully."""
    current = await _get_schema_version(db)
    if current >= _LATEST_VERSION:
        return

    for version, description, statements in _MIGRATIONS:
        if version <= current:
            continue
        for stmt in statements:
            try:
                await db.execute(stmt)
            except Exception as exc:
                if not _is_idempotent_migration_error(exc):
                    raise
        await db.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
        logger.debug("Migration %d applied: %s", version, description)

    await db.commit()


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

        # For fresh databases, stamp the latest version directly.
        current = await _get_schema_version(db)
        if current == 0:
            await db.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (_LATEST_VERSION,),
            )
            await db.commit()
        else:
            await _run_migrations(db)

        await _reconcile_required_columns(db)
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
