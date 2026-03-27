"""SQLite storage layer for persistent scan data."""

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


async def ensure_project(brand_name: str, url: str, category: str) -> int:
    """Upsert a project row and return its id."""
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR IGNORE INTO projects (brand_name, url, category) VALUES (?, ?, ?)",
            (brand_name, url, category),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT id FROM projects WHERE brand_name = ? AND url = ?",
            (brand_name, url),
        )
        row = await cursor.fetchone()
        return row[0]
    finally:
        await db.close()


async def update_project(project_id: int, brand_name: str | None = None, category: str | None = None) -> None:
    """Update project metadata (brand_name and/or category)."""
    db = await get_db()
    try:
        if brand_name and category:
            await db.execute(
                "UPDATE projects SET brand_name = ?, category = ? WHERE id = ?",
                (brand_name, category, project_id),
            )
        elif brand_name:
            await db.execute(
                "UPDATE projects SET brand_name = ? WHERE id = ?",
                (brand_name, project_id),
            )
        elif category:
            await db.execute(
                "UPDATE projects SET category = ? WHERE id = ?",
                (category, project_id),
            )
        await db.commit()
    finally:
        await db.close()


async def get_project(project_id: int) -> dict | None:
    """Return project dict by id, or None."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, brand_name, url, category FROM projects WHERE id = ?",
            (project_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return {"id": row[0], "brand_name": row[1], "url": row[2], "category": row[3]}
    finally:
        await db.close()


async def list_projects() -> list[dict]:
    """Return all projects."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT id, brand_name, url, category FROM projects")
        rows = await cursor.fetchall()
        return [{"id": r[0], "brand_name": r[1], "url": r[2], "category": r[3]} for r in rows]
    finally:
        await db.close()


async def delete_project(project_id: int) -> bool:
    """Delete a project and all its related data. Returns True if deleted."""
    db = await get_db()
    try:
        await db.execute("UPDATE chat_sessions SET project_id = NULL WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM approvals WHERE project_id = ?", (project_id,))
        # Delete graph expansion data
        await db.execute("DELETE FROM graph_expansion_edges WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM graph_expansion_nodes WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM graph_expansions WHERE project_id = ?", (project_id,))
        # Delete discussion snapshots (via tracked_discussions)
        await db.execute(
            """DELETE FROM discussion_snapshots WHERE discussion_id IN
               (SELECT id FROM tracked_discussions WHERE project_id = ?)""",
            (project_id,),
        )
        # Delete tracked discussions
        await db.execute("DELETE FROM tracked_discussions WHERE project_id = ?", (project_id,))
        # Delete scans
        await db.execute("DELETE FROM seo_scans WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM geo_scans WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM community_scans WHERE project_id = ?", (project_id,))
        # Delete SERP data
        await db.execute("DELETE FROM serp_snapshots WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM tracked_keywords WHERE project_id = ?", (project_id,))
        # Delete competitors and their keywords
        await db.execute(
            """DELETE FROM competitor_keywords WHERE competitor_id IN
               (SELECT id FROM competitors WHERE project_id = ?)""",
            (project_id,),
        )
        await db.execute("DELETE FROM competitors WHERE project_id = ?", (project_id,))
        # Delete campaign artifacts and runs
        await db.execute(
            """DELETE FROM campaign_artifacts WHERE run_id IN
               (SELECT id FROM campaign_runs WHERE project_id = ?)""",
            (project_id,),
        )
        await db.execute("DELETE FROM campaign_runs WHERE project_id = ?", (project_id,))
        # Delete trend briefings and insights
        await db.execute("DELETE FROM trend_briefings WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM insights WHERE project_id = ?", (project_id,))
        # Delete monitoring artifacts
        await db.execute(
            """DELETE FROM scan_findings WHERE run_id IN
               (SELECT id FROM scan_runs WHERE project_id = ?)""",
            (project_id,),
        )
        await db.execute(
            """DELETE FROM scan_recommendations WHERE run_id IN
               (SELECT id FROM scan_runs WHERE project_id = ?)""",
            (project_id,),
        )
        await db.execute(
            """DELETE FROM scan_run_steps WHERE run_id IN
               (SELECT id FROM scan_runs WHERE project_id = ?)""",
            (project_id,),
        )
        await db.execute("DELETE FROM scan_runs WHERE project_id = ?", (project_id,))
        # Delete scheduled jobs
        await db.execute("DELETE FROM scheduled_jobs WHERE project_id = ?", (project_id,))
        # Delete the project itself
        cursor = await db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def save_seo_scan(
    project_id: int,
    url: str,
    report_json: str,
    *,
    score_performance: float | None = None,
    score_lcp: float | None = None,
    score_cls: float | None = None,
    score_tbt: float | None = None,
    has_robots_txt: bool | None = None,
    has_sitemap: bool | None = None,
    has_schema_org: bool | None = None,
) -> int:
    """Save an SEO scan snapshot. Returns scan id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO seo_scans
               (project_id, url, report_json,
                score_performance, score_lcp, score_cls, score_tbt,
                has_robots_txt, has_sitemap, has_schema_org)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                project_id, url, report_json,
                score_performance, score_lcp, score_cls, score_tbt,
                int(has_robots_txt) if has_robots_txt is not None else None,
                int(has_sitemap) if has_sitemap is not None else None,
                int(has_schema_org) if has_schema_org is not None else None,
            ),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def save_geo_scan(
    project_id: int,
    geo_score: int,
    *,
    visibility_score: int | None = None,
    position_score: int | None = None,
    sentiment_score: int | None = None,
    platform_results_json: str = "{}",
) -> int:
    """Save a GEO scan snapshot. Returns scan id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO geo_scans
               (project_id, geo_score, visibility_score, position_score,
                sentiment_score, platform_results_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (project_id, geo_score, visibility_score, position_score,
             sentiment_score, platform_results_json),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def save_community_scan(
    project_id: int,
    total_hits: int,
    results_json: str,
) -> int:
    """Save a community scan snapshot. Returns scan id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO community_scans (project_id, total_hits, results_json) VALUES (?, ?, ?)",
            (project_id, total_hits, results_json),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def upsert_tracked_discussion(project_id: int, hit: dict) -> int:
    """Upsert a tracked discussion from a DiscussionHit dict. Returns discussion id."""
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO tracked_discussions (project_id, platform, detail_id, title, url)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(project_id, platform, detail_id)
               DO UPDATE SET last_checked_at = datetime('now'), title = excluded.title""",
            (project_id, hit["platform"], hit["detail_id"], hit["title"], hit["url"]),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT id FROM tracked_discussions WHERE project_id = ? AND platform = ? AND detail_id = ?",
            (project_id, hit["platform"], hit["detail_id"]),
        )
        row = await cursor.fetchone()
        return row[0]
    finally:
        await db.close()


async def save_discussion_snapshot(
    discussion_id: int,
    raw_score: int,
    comments_count: int,
    engagement_score: int,
) -> int:
    """Save a discussion engagement snapshot. Returns snapshot id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO discussion_snapshots
               (discussion_id, raw_score, comments_count, engagement_score)
               VALUES (?, ?, ?, ?)""",
            (discussion_id, raw_score, comments_count, engagement_score),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


# --- Scheduled jobs ---

async def add_scheduled_job(
    project_id: int,
    job_type: str,
    cron_expr: str = "0 9 * * *",
) -> int:
    """Add a scheduled job. Returns job id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO scheduled_jobs (project_id, job_type, cron_expr) VALUES (?, ?, ?)",
            (project_id, job_type, cron_expr),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def list_scheduled_jobs() -> list[dict]:
    """Return all scheduled jobs with project info."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT j.id, j.project_id, p.brand_name, p.url, p.category,
                      j.job_type, j.cron_expr, j.enabled, j.last_run_at, j.next_run_at
               FROM scheduled_jobs j JOIN projects p ON j.project_id = p.id
               ORDER BY j.id"""
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0], "project_id": r[1], "brand_name": r[2], "url": r[3],
                "category": r[4], "job_type": r[5], "cron_expr": r[6],
                "enabled": bool(r[7]), "last_run_at": r[8], "next_run_at": r[9],
            }
            for r in rows
        ]
    finally:
        await db.close()


async def get_scheduled_job(job_id: int) -> dict | None:
    """Return a single scheduled job with project info."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT j.id, j.project_id, p.brand_name, p.url, p.category,
                      j.job_type, j.cron_expr, j.enabled, j.last_run_at, j.next_run_at
               FROM scheduled_jobs j JOIN projects p ON j.project_id = p.id
               WHERE j.id = ?""",
            (job_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0], "project_id": row[1], "brand_name": row[2], "url": row[3],
            "category": row[4], "job_type": row[5], "cron_expr": row[6],
            "enabled": bool(row[7]), "last_run_at": row[8], "next_run_at": row[9],
        }
    finally:
        await db.close()


async def remove_scheduled_job(job_id: int) -> bool:
    """Remove a scheduled job. Returns True if deleted."""
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM scheduled_jobs WHERE id = ?", (job_id,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def update_scheduled_job(
    job_id: int,
    cron_expr: str | None = None,
    enabled: bool | None = None,
) -> bool:
    """Update a scheduled job's cron expression and/or enabled flag. Returns True if found."""
    db = await get_db()
    try:
        parts: list[str] = []
        params: list = []
        if cron_expr is not None:
            parts.append("cron_expr = ?")
            params.append(cron_expr)
        if enabled is not None:
            parts.append("enabled = ?")
            params.append(int(enabled))
        if not parts:
            return True
        params.append(job_id)
        cursor = await db.execute(
            f"UPDATE scheduled_jobs SET {', '.join(parts)} WHERE id = ?",
            params,
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def update_job_last_run(job_id: int) -> None:
    """Update last_run_at for a job."""
    db = await get_db()
    try:
        await db.execute(
            "UPDATE scheduled_jobs SET last_run_at = datetime('now') WHERE id = ?",
            (job_id,),
        )
        await db.commit()
    finally:
        await db.close()


# --- Query helpers for trends ---

async def get_seo_history(project_id: int, limit: int = 20) -> list[dict]:
    """Return recent SEO scans for a project."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, url, scanned_at, score_performance, score_lcp, score_cls,
                      score_tbt, has_robots_txt, has_sitemap, has_schema_org
               FROM seo_scans WHERE project_id = ? ORDER BY scanned_at DESC LIMIT ?""",
            (project_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0], "url": r[1], "scanned_at": r[2],
                "score_performance": r[3], "score_lcp": r[4], "score_cls": r[5],
                "score_tbt": r[6], "has_robots_txt": bool(r[7]) if r[7] is not None else None,
                "has_sitemap": bool(r[8]) if r[8] is not None else None,
                "has_schema_org": bool(r[9]) if r[9] is not None else None,
            }
            for r in rows
        ]
    finally:
        await db.close()


async def get_geo_history(project_id: int, limit: int = 20) -> list[dict]:
    """Return recent GEO scans for a project."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, scanned_at, geo_score, visibility_score, position_score,
                      sentiment_score, platform_results_json
               FROM geo_scans WHERE project_id = ? ORDER BY scanned_at DESC LIMIT ?""",
            (project_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0], "scanned_at": r[1], "geo_score": r[2],
                "visibility_score": r[3], "position_score": r[4],
                "sentiment_score": r[5], "platform_results_json": r[6],
            }
            for r in rows
        ]
    finally:
        await db.close()


async def get_community_history(project_id: int, limit: int = 20) -> list[dict]:
    """Return recent community scans for a project."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, scanned_at, total_hits, results_json
               FROM community_scans WHERE project_id = ? ORDER BY scanned_at DESC LIMIT ?""",
            (project_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            {"id": r[0], "scanned_at": r[1], "total_hits": r[2], "results_json": r[3]}
            for r in rows
        ]
    finally:
        await db.close()


async def get_tracked_discussions(project_id: int) -> list[dict]:
    """Return tracked discussions with latest snapshot for a project."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT td.id, td.platform, td.detail_id, td.title, td.url,
                      td.first_seen_at, td.last_checked_at,
                      ds.raw_score, ds.comments_count, ds.engagement_score
               FROM tracked_discussions td
               LEFT JOIN discussion_snapshots ds ON ds.discussion_id = td.id
                 AND ds.id = (SELECT MAX(id) FROM discussion_snapshots WHERE discussion_id = td.id)
               WHERE td.project_id = ?
               ORDER BY ds.engagement_score DESC NULLS LAST""",
            (project_id,),
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0], "platform": r[1], "detail_id": r[2], "title": r[3],
                "url": r[4], "first_seen_at": r[5], "last_checked_at": r[6],
                "raw_score": r[7], "comments_count": r[8], "engagement_score": r[9],
            }
            for r in rows
        ]
    finally:
        await db.close()


async def get_discussion_snapshots(discussion_id: int) -> list[dict]:
    """Return all snapshots for a discussion (time series)."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, checked_at, raw_score, comments_count, engagement_score
               FROM discussion_snapshots WHERE discussion_id = ? ORDER BY checked_at""",
            (discussion_id,),
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0], "checked_at": r[1], "raw_score": r[2],
                "comments_count": r[3], "engagement_score": r[4],
            }
            for r in rows
        ]
    finally:
        await db.close()


async def create_scan_run(task_id: str, monitor_id: int | None, project_id: int, job_type: str) -> int:
    """Create or return a persisted monitoring run."""
    db = await get_db()
    try:
        await db.execute(
            """INSERT OR IGNORE INTO scan_runs (task_id, monitor_id, project_id, job_type)
               VALUES (?, ?, ?, ?)""",
            (task_id, monitor_id, project_id, job_type),
        )
        await db.commit()
        cursor = await db.execute("SELECT id FROM scan_runs WHERE task_id = ?", (task_id,))
        row = await cursor.fetchone()
        return row[0]
    finally:
        await db.close()


async def list_scan_runs_by_monitor(monitor_id: int, limit: int = 10) -> list[dict]:
    """List past scan runs for a monitor, newest first."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT r.id, r.task_id, r.job_type, r.status, r.summary, r.created_at, r.completed_at,
                      (SELECT COUNT(*) FROM scan_findings WHERE run_id = r.id) AS findings_count,
                      (SELECT COUNT(*) FROM scan_recommendations WHERE run_id = r.id) AS recs_count
               FROM scan_runs r
               WHERE r.monitor_id = ?
               ORDER BY r.created_at DESC
               LIMIT ?""",
            (monitor_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0], "task_id": r[1], "job_type": r[2], "status": r[3],
                "summary": r[4], "created_at": r[5], "completed_at": r[6],
                "findings_count": r[7], "recommendations_count": r[8],
            }
            for r in rows
        ]
    finally:
        await db.close()


async def update_scan_run(
    run_id: int,
    *,
    status: str | None = None,
    summary: str | None = None,
    completed: bool = False,
) -> None:
    """Update a persisted monitoring run."""
    db = await get_db()
    try:
        parts: list[str] = []
        params: list = []
        if status is not None:
            parts.append("status = ?")
            params.append(status)
        if summary is not None:
            parts.append("summary = ?")
            params.append(summary)
        if completed:
            parts.append("completed_at = datetime('now')")
        if not parts:
            return
        params.append(run_id)
        await db.execute(f"UPDATE scan_runs SET {', '.join(parts)} WHERE id = ?", params)
        await db.commit()
    finally:
        await db.close()


async def add_scan_run_step(
    run_id: int,
    *,
    stage: str,
    status: str,
    summary: str = "",
    agent: str | None = None,
    detail: str | None = None,
) -> int:
    """Append a persisted monitoring step event."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO scan_run_steps (run_id, stage, agent, status, summary, detail)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (run_id, stage, agent, status, summary, detail or summary),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def replace_scan_artifacts(
    run_id: int,
    findings: list[dict],
    recommendations: list[dict],
) -> None:
    """Replace persisted findings and recommendations for a run."""
    db = await get_db()
    try:
        await db.execute("DELETE FROM scan_findings WHERE run_id = ?", (run_id,))
        await db.execute("DELETE FROM scan_recommendations WHERE run_id = ?", (run_id,))

        for finding in findings:
            await db.execute(
                """INSERT INTO scan_findings
                   (run_id, domain, severity, title, summary, confidence, evidence_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id,
                    finding["domain"],
                    finding["severity"],
                    finding["title"],
                    finding["summary"],
                    finding.get("confidence"),
                    json.dumps(finding.get("evidence_refs", [])),
                ),
            )

        for rec in recommendations:
            await db.execute(
                """INSERT INTO scan_recommendations
                   (run_id, domain, priority, owner_type, action_type, title, summary, rationale, confidence, evidence_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id,
                    rec["domain"],
                    rec["priority"],
                    rec["owner_type"],
                    rec["action_type"],
                    rec["title"],
                    rec["summary"],
                    rec["rationale"],
                    rec.get("confidence"),
                    json.dumps(rec.get("evidence_refs", [])),
                ),
            )

        await db.commit()
    finally:
        await db.close()


async def get_task_findings(task_id: str) -> list[dict]:
    """Return persisted findings for a monitoring task."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT f.domain, f.severity, f.title, f.summary, f.confidence, f.evidence_json
               FROM scan_findings f
               JOIN scan_runs r ON r.id = f.run_id
               WHERE r.task_id = ?
               ORDER BY
                 CASE f.severity
                   WHEN 'critical' THEN 0
                   WHEN 'warning' THEN 1
                   ELSE 2
                 END,
                 f.id""",
            (task_id,),
        )
        rows = await cursor.fetchall()
        return [
            {
                "domain": row[0],
                "severity": row[1],
                "title": row[2],
                "summary": row[3],
                "confidence": row[4],
                "evidence_refs": json.loads(row[5] or "[]"),
            }
            for row in rows
        ]
    finally:
        await db.close()


async def get_task_recommendations(task_id: str) -> list[dict]:
    """Return persisted recommendations for a monitoring task."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT rec.domain, rec.priority, rec.owner_type, rec.action_type,
                      rec.title, rec.summary, rec.rationale, rec.confidence, rec.evidence_json
               FROM scan_recommendations rec
               JOIN scan_runs r ON r.id = rec.run_id
               WHERE r.task_id = ?
               ORDER BY
                 CASE rec.priority
                   WHEN 'high' THEN 0
                   WHEN 'medium' THEN 1
                   ELSE 2
                 END,
                 rec.id""",
            (task_id,),
        )
        rows = await cursor.fetchall()
        return [
            {
                "domain": row[0],
                "priority": row[1],
                "owner_type": row[2],
                "action_type": row[3],
                "title": row[4],
                "summary": row[5],
                "rationale": row[6],
                "confidence": row[7],
                "evidence_refs": json.loads(row[8] or "[]"),
            }
            for row in rows
        ]
    finally:
        await db.close()


async def get_latest_monitoring_summary(project_id: int) -> dict | None:
    """Return summary info for the latest persisted monitoring run."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT r.id, r.status, r.summary, r.created_at, r.completed_at
               FROM scan_runs r
               WHERE r.project_id = ?
               ORDER BY r.id DESC
               LIMIT 1""",
            (project_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None

        findings_cur = await db.execute(
            "SELECT COUNT(*) FROM scan_findings WHERE run_id = ?",
            (row[0],),
        )
        findings_count = (await findings_cur.fetchone())[0]
        recs_cur = await db.execute(
            "SELECT COUNT(*) FROM scan_recommendations WHERE run_id = ?",
            (row[0],),
        )
        recommendations_count = (await recs_cur.fetchone())[0]

        return {
            "run_id": row[0],
            "status": row[1],
            "summary": row[2],
            "created_at": row[3],
            "completed_at": row[4],
            "findings_count": findings_count,
            "recommendations_count": recommendations_count,
        }
    finally:
        await db.close()


async def get_latest_scans(project_id: int) -> dict:
    """Get the latest scan of each type for a project, including SERP summary."""
    db = await get_db()
    try:
        seo = await db.execute(
            "SELECT scanned_at, score_performance FROM seo_scans WHERE project_id = ? ORDER BY scanned_at DESC LIMIT 1",
            (project_id,),
        )
        seo_row = await seo.fetchone()

        geo = await db.execute(
            "SELECT scanned_at, geo_score FROM geo_scans WHERE project_id = ? ORDER BY scanned_at DESC LIMIT 1",
            (project_id,),
        )
        geo_row = await geo.fetchone()

        comm = await db.execute(
            "SELECT scanned_at, total_hits FROM community_scans WHERE project_id = ? ORDER BY scanned_at DESC LIMIT 1",
            (project_id,),
        )
        comm_row = await comm.fetchone()

        # SERP: latest snapshot per keyword (error IS NULL only)
        serp_cur = await db.execute(
            """SELECT keyword, position, checked_at FROM serp_snapshots
               WHERE project_id = ? AND error IS NULL
               AND id IN (
                   SELECT MAX(id) FROM serp_snapshots
                   WHERE project_id = ? AND error IS NULL
                   GROUP BY keyword
               )
               ORDER BY keyword""",
            (project_id, project_id),
        )
        serp_rows = await serp_cur.fetchall()
        serp_summary = [
            {"keyword": r[0], "position": r[1], "checked_at": r[2]}
            for r in serp_rows
        ] if serp_rows else []

        return {
            "seo": {"scanned_at": seo_row[0], "score": seo_row[1]} if seo_row else None,
            "geo": {"scanned_at": geo_row[0], "score": geo_row[1]} if geo_row else None,
            "community": {"scanned_at": comm_row[0], "total_hits": comm_row[1]} if comm_row else None,
            "serp": serp_summary,
        }
    finally:
        await db.close()


async def get_previous_scans(project_id: int) -> dict | None:
    """Get the second-most-recent scan of each type (for delta calculation)."""
    db = await get_db()
    try:
        seo = await db.execute(
            "SELECT scanned_at, score_performance FROM seo_scans WHERE project_id = ? ORDER BY scanned_at DESC LIMIT 1 OFFSET 1",
            (project_id,),
        )
        seo_row = await seo.fetchone()

        geo = await db.execute(
            "SELECT scanned_at, geo_score FROM geo_scans WHERE project_id = ? ORDER BY scanned_at DESC LIMIT 1 OFFSET 1",
            (project_id,),
        )
        geo_row = await geo.fetchone()

        if not seo_row and not geo_row:
            return None

        result = {}
        if seo_row:
            result["seo"] = {"scanned_at": seo_row[0], "score": seo_row[1]}
        if geo_row:
            result["geo"] = {"scanned_at": geo_row[0], "score": geo_row[1]}
        return result
    finally:
        await db.close()


# --- Tracked keywords & SERP snapshots ---

async def add_tracked_keyword(project_id: int, keyword: str) -> int:
    """Add a keyword to the tracked list. Returns keyword id."""
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR IGNORE INTO tracked_keywords (project_id, keyword) VALUES (?, ?)",
            (project_id, keyword),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT id FROM tracked_keywords WHERE project_id = ? AND keyword = ?",
            (project_id, keyword),
        )
        row = await cursor.fetchone()
        return row[0]
    finally:
        await db.close()


async def list_tracked_keywords(project_id: int) -> list[dict]:
    """Return all tracked keywords for a project."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, keyword, created_at FROM tracked_keywords WHERE project_id = ? ORDER BY id",
            (project_id,),
        )
        rows = await cursor.fetchall()
        return [{"id": r[0], "keyword": r[1], "created_at": r[2]} for r in rows]
    finally:
        await db.close()


async def remove_tracked_keyword(keyword_id: int) -> bool:
    """Remove a tracked keyword by id. Returns True if deleted."""
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM tracked_keywords WHERE id = ?", (keyword_id,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def save_serp_snapshot(
    project_id: int,
    keyword: str,
    position: int | None,
    url_found: str | None,
    provider: str,
    error: str | None,
) -> int:
    """Save a SERP ranking snapshot. Returns snapshot id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO serp_snapshots
               (project_id, keyword, position, url_found, provider, error)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (project_id, keyword, position, url_found, provider, error),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def get_serp_history(
    project_id: int, keyword: str, limit: int = 20
) -> list[dict]:
    """Return recent SERP snapshots for a project+keyword."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, keyword, position, url_found, provider, error, checked_at
               FROM serp_snapshots
               WHERE project_id = ? AND keyword = ?
               ORDER BY checked_at DESC LIMIT ?""",
            (project_id, keyword, limit),
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0], "keyword": r[1], "position": r[2], "url_found": r[3],
                "provider": r[4], "error": r[5], "checked_at": r[6],
            }
            for r in rows
        ]
    finally:
        await db.close()


async def get_all_serp_latest(project_id: int) -> list[dict]:
    """Return latest SERP snapshot per keyword for a project."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT keyword, position, url_found, provider, error, checked_at
               FROM serp_snapshots
               WHERE project_id = ?
               AND id IN (
                   SELECT MAX(id) FROM serp_snapshots
                   WHERE project_id = ?
                   GROUP BY keyword
               )
               ORDER BY keyword""",
            (project_id, project_id),
        )
        rows = await cursor.fetchall()
        return [
            {
                "keyword": r[0], "position": r[1], "url_found": r[2],
                "provider": r[3], "error": r[4], "checked_at": r[5],
            }
            for r in rows
        ]
    finally:
        await db.close()


# --- Chat sessions ---


async def create_chat_session(
    session_id: str, title: str = "", project_id: int | None = None
) -> None:
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO chat_sessions (id, title, project_id) VALUES (?, ?, ?)",
            (session_id, title, project_id),
        )
        await db.commit()
    finally:
        await db.close()


async def list_chat_sessions() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT s.id, s.title, s.created_at, s.updated_at, s.project_id, p.brand_name
               FROM chat_sessions s
               LEFT JOIN projects p ON p.id = s.project_id
               ORDER BY s.updated_at DESC, s.id DESC"""
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0],
                "title": r[1],
                "created_at": r[2],
                "updated_at": r[3],
                "project_id": r[4],
                "project_name": r[5],
            }
            for r in rows
        ]
    finally:
        await db.close()


async def get_chat_session(session_id: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT s.id, s.title, s.input_items, s.created_at, s.updated_at, s.project_id, p.brand_name
               FROM chat_sessions s
               LEFT JOIN projects p ON p.id = s.project_id
               WHERE s.id = ?""",
            (session_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return {
            "id": row[0], "title": row[1], "input_items": row[2],
            "created_at": row[3], "updated_at": row[4],
            "project_id": row[5], "project_name": row[6],
        }
    finally:
        await db.close()


async def update_chat_session(
    session_id: str, input_items_json: str, title: str | None = None
) -> None:
    db = await get_db()
    try:
        if title is not None:
            await db.execute(
                "UPDATE chat_sessions SET input_items = ?, title = ?, updated_at = datetime('now') WHERE id = ?",
                (input_items_json, title, session_id),
            )
        else:
            await db.execute(
                "UPDATE chat_sessions SET input_items = ?, updated_at = datetime('now') WHERE id = ?",
                (input_items_json, session_id),
            )
        await db.commit()
    finally:
        await db.close()


async def delete_chat_session(session_id: str) -> bool:
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def clear_chat_sessions() -> None:
    db = await get_db()
    try:
        await db.execute("DELETE FROM chat_sessions")
        await db.commit()
    finally:
        await db.close()


# --- Settings ---


async def get_setting(key: str) -> str | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row[0] if row else None
    finally:
        await db.close()


async def set_setting(key: str, value: str) -> None:
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        await db.commit()
    finally:
        await db.close()


async def delete_setting(key: str) -> bool:
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM settings WHERE key = ?", (key,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


# --- Approvals ---


def _approval_row_to_dict(row) -> dict:
    d = {
        "id": row[0],
        "project_id": row[1],
        "channel": row[2],
        "approval_type": row[3],
        "status": row[4],
        "title": row[5],
        "target_label": row[6],
        "target_url": row[7],
        "agent_name": row[8],
        "content": row[9],
        "payload": json.loads(row[10] or "{}"),
        "preview": json.loads(row[11] or "{}"),
        "publish_result": json.loads(row[12]) if row[12] else None,
        "decision_note": row[13],
        "created_at": row[14],
        "decided_at": row[15],
    }
    # Autopilot fields (may not exist in older rows)
    if len(row) > 16:
        d["source_insight_id"] = row[16]
        d["pre_metrics_json"] = row[17] or "{}"
        d["post_metrics_json"] = row[18] or "{}"
    return d


async def create_approval(
    project_id: int,
    channel: str,
    approval_type: str,
    content: str,
    payload: dict,
    preview: dict,
    *,
    title: str = "",
    target_label: str = "",
    target_url: str = "",
    agent_name: str = "",
) -> dict:
    """Insert a pending approval and return the stored record."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO approvals (
                   project_id, channel, approval_type, title, target_label, target_url,
                   agent_name, content, payload_json, preview_json
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                project_id,
                channel,
                approval_type,
                title,
                target_label,
                target_url,
                agent_name,
                content,
                json.dumps(payload, ensure_ascii=False),
                json.dumps(preview, ensure_ascii=False),
            ),
        )
        await db.commit()
        approval_id = cursor.lastrowid
    finally:
        await db.close()

    return await get_approval(approval_id)


async def get_approval(approval_id: int) -> dict | None:
    """Return one approval item."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, project_id, channel, approval_type, status, title, target_label,
                      target_url, agent_name, content, payload_json, preview_json,
                      publish_result_json, decision_note, created_at, decided_at,
                      source_insight_id, pre_metrics_json, post_metrics_json
               FROM approvals WHERE id = ?""",
            (approval_id,),
        )
        row = await cursor.fetchone()
        return _approval_row_to_dict(row) if row else None
    finally:
        await db.close()


async def list_approvals(status: str | None = None, limit: int = 50) -> list[dict]:
    """List approvals, newest first."""
    db = await get_db()
    try:
        if status:
            cursor = await db.execute(
                """SELECT id, project_id, channel, approval_type, status, title, target_label,
                          target_url, agent_name, content, payload_json, preview_json,
                          publish_result_json, decision_note, created_at, decided_at
                   FROM approvals
                   WHERE status = ?
                   ORDER BY created_at DESC, id DESC
                   LIMIT ?""",
                (status, limit),
            )
        else:
            cursor = await db.execute(
                """SELECT id, project_id, channel, approval_type, status, title, target_label,
                          target_url, agent_name, content, payload_json, preview_json,
                          publish_result_json, decision_note, created_at, decided_at
                   FROM approvals
                   ORDER BY created_at DESC, id DESC
                   LIMIT ?""",
                (limit,),
            )
        rows = await cursor.fetchall()
        return [_approval_row_to_dict(row) for row in rows]
    finally:
        await db.close()


async def update_approval_status(
    approval_id: int,
    status: str,
    *,
    decision_note: str = "",
    publish_result: dict | None = None,
) -> bool:
    """Update approval decision state and optional publish result."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """UPDATE approvals
               SET status = ?, decision_note = ?, publish_result_json = ?, decided_at = datetime('now')
               WHERE id = ?""",
            (
                status,
                decision_note,
                json.dumps(publish_result, ensure_ascii=False) if publish_result is not None else None,
                approval_id,
            ),
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


# --- Competitors ---


async def add_competitor(
    project_id: int, name: str, url: str | None = None, category: str | None = None
) -> int:
    """Add a competitor. Returns competitor id."""
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR IGNORE INTO competitors (project_id, name, url, category) VALUES (?, ?, ?, ?)",
            (project_id, name, url, category),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT id FROM competitors WHERE project_id = ? AND name = ?",
            (project_id, name),
        )
        row = await cursor.fetchone()
        return row[0]
    finally:
        await db.close()


async def list_competitors(project_id: int) -> list[dict]:
    """Return all competitors for a project."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, name, url, category, created_at FROM competitors WHERE project_id = ? ORDER BY id",
            (project_id,),
        )
        rows = await cursor.fetchall()
        return [
            {"id": r[0], "name": r[1], "url": r[2], "category": r[3], "created_at": r[4]}
            for r in rows
        ]
    finally:
        await db.close()


async def get_competitor(competitor_id: int) -> dict | None:
    """Return a single competitor by ID."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, project_id, name, url FROM competitors WHERE id = ?",
            (competitor_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return {"id": row[0], "project_id": row[1], "name": row[2], "url": row[3]}
    finally:
        await db.close()


async def remove_competitor(competitor_id: int) -> bool:
    """Remove a competitor and its keywords."""
    db = await get_db()
    try:
        await db.execute("DELETE FROM competitor_keywords WHERE competitor_id = ?", (competitor_id,))
        cursor = await db.execute("DELETE FROM competitors WHERE id = ?", (competitor_id,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def add_competitor_keyword(competitor_id: int, keyword: str) -> int:
    """Add a keyword to a competitor. Returns keyword id."""
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR IGNORE INTO competitor_keywords (competitor_id, keyword) VALUES (?, ?)",
            (competitor_id, keyword),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT id FROM competitor_keywords WHERE competitor_id = ? AND keyword = ?",
            (competitor_id, keyword),
        )
        row = await cursor.fetchone()
        return row[0]
    finally:
        await db.close()


async def list_competitor_keywords(competitor_id: int) -> list[dict]:
    """Return all keywords for a competitor."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, keyword, created_at FROM competitor_keywords WHERE competitor_id = ? ORDER BY id",
            (competitor_id,),
        )
        rows = await cursor.fetchall()
        return [{"id": r[0], "keyword": r[1], "created_at": r[2]} for r in rows]
    finally:
        await db.close()


# --- Graph expansion ---


async def get_or_create_expansion(project_id: int) -> dict:
    """Return the expansion row for a project, creating it if absent."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, project_id, desired_state, runtime_state, current_wave, "
            "nodes_discovered, nodes_explored, heartbeat_at, created_at, updated_at "
            "FROM graph_expansions WHERE project_id = ?",
            (project_id,),
        )
        row = await cursor.fetchone()
        if row:
            return _expansion_row_to_dict(row)
        await db.execute(
            "INSERT INTO graph_expansions (project_id) VALUES (?)", (project_id,),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT id, project_id, desired_state, runtime_state, current_wave, "
            "nodes_discovered, nodes_explored, heartbeat_at, created_at, updated_at "
            "FROM graph_expansions WHERE project_id = ?",
            (project_id,),
        )
        row = await cursor.fetchone()
        return _expansion_row_to_dict(row)
    finally:
        await db.close()


def _expansion_row_to_dict(row) -> dict:
    return {
        "id": row[0], "project_id": row[1],
        "desired_state": row[2], "runtime_state": row[3],
        "current_wave": row[4], "nodes_discovered": row[5],
        "nodes_explored": row[6], "heartbeat_at": row[7],
        "created_at": row[8], "updated_at": row[9],
    }


async def get_expansion(project_id: int) -> dict | None:
    """Read current expansion state. Returns None if no expansion exists."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, project_id, desired_state, runtime_state, current_wave, "
            "nodes_discovered, nodes_explored, heartbeat_at, created_at, updated_at "
            "FROM graph_expansions WHERE project_id = ?",
            (project_id,),
        )
        row = await cursor.fetchone()
        return _expansion_row_to_dict(row) if row else None
    finally:
        await db.close()


async def update_expansion(project_id: int, **kwargs) -> None:
    """Update expansion fields. Accepts: desired_state, runtime_state, current_wave,
    nodes_discovered, nodes_explored, heartbeat_at."""
    allowed = {"desired_state", "runtime_state", "current_wave",
               "nodes_discovered", "nodes_explored", "heartbeat_at"}
    sets = {k: v for k, v in kwargs.items() if k in allowed}
    if not sets:
        return
    sets["updated_at"] = "datetime('now')"
    clauses = []
    values = []
    for k, v in sets.items():
        if v == "datetime('now')":
            clauses.append(f"{k} = datetime('now')")
        else:
            clauses.append(f"{k} = ?")
            values.append(v)
    values.append(project_id)
    db = await get_db()
    try:
        await db.execute(
            f"UPDATE graph_expansions SET {', '.join(clauses)} WHERE project_id = ?",
            tuple(values),
        )
        await db.commit()
    finally:
        await db.close()


async def seed_expansion_nodes(project_id: int) -> int:
    """Insert existing keywords and competitors as wave-0 unexplored nodes. Idempotent.

    Assigns priority scores so the expansion engine explores the most valuable
    nodes first:
      - competitors: 90 (high value — discovering competitor landscape)
      - keywords without SERP data: 80 (need ranking info)
      - keywords with low SERP position: 70 (opportunity gaps)
      - keywords with good SERP position: 40 (already performing)
      - competitor_keywords: 60 (moderate — cross-reference value)
    """
    db = await get_db()
    try:
        count = 0
        # Keywords — prioritize those without SERP data or with low rankings
        cursor = await db.execute(
            """SELECT k.id, ss.position FROM tracked_keywords k
               LEFT JOIN (
                   SELECT keyword, position, ROW_NUMBER() OVER (
                       PARTITION BY keyword ORDER BY checked_at DESC
                   ) AS rn FROM serp_snapshots WHERE project_id = ?
               ) ss ON ss.keyword = k.keyword AND ss.rn = 1
               WHERE k.project_id = ?""",
            (project_id, project_id),
        )
        for row in await cursor.fetchall():
            kw_id, position = row[0], row[1]
            if position is None:
                priority = 80  # No SERP data — needs exploration
                reason = "no_serp_data"
            elif position > 10:
                priority = 70  # Low ranking — opportunity gap
                reason = f"low_rank_{position}"
            else:
                priority = 40  # Already ranking well
                reason = f"ranking_{position}"
            r = await db.execute(
                "INSERT OR IGNORE INTO graph_expansion_nodes "
                "(project_id, node_type, db_row_id, wave_discovered, explored, priority, reason) "
                "VALUES (?, 'keyword', ?, 0, 0, ?, ?)",
                (project_id, kw_id, priority, reason),
            )
            count += r.rowcount

        # Competitors — always high priority
        cursor = await db.execute(
            "SELECT id FROM competitors WHERE project_id = ?", (project_id,),
        )
        for row in await cursor.fetchall():
            r = await db.execute(
                "INSERT OR IGNORE INTO graph_expansion_nodes "
                "(project_id, node_type, db_row_id, wave_discovered, explored, priority, reason) "
                "VALUES (?, 'competitor', ?, 0, 0, 90, 'competitor_discovery')",
                (project_id, row[0]),
            )
            count += r.rowcount

        # Competitor keywords — moderate priority
        cursor = await db.execute(
            "SELECT ck.id FROM competitor_keywords ck "
            "JOIN competitors c ON c.id = ck.competitor_id "
            "WHERE c.project_id = ?",
            (project_id,),
        )
        for row in await cursor.fetchall():
            r = await db.execute(
                "INSERT OR IGNORE INTO graph_expansion_nodes "
                "(project_id, node_type, db_row_id, wave_discovered, explored, priority, reason) "
                "VALUES (?, 'competitor_keyword', ?, 0, 0, 60, 'comp_kw_cross_ref')",
                (project_id, row[0]),
            )
            count += r.rowcount
        await db.commit()
        return count
    finally:
        await db.close()


async def get_min_unexplored_wave(project_id: int) -> int | None:
    """Return the lowest wave number that has unexplored nodes, or None."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT MIN(wave_discovered) FROM graph_expansion_nodes "
            "WHERE project_id = ? AND explored = 0",
            (project_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row and row[0] is not None else None
    finally:
        await db.close()


async def get_frontier_nodes(project_id: int, wave: int) -> list[dict]:
    """Return unexplored nodes for exactly the given wave, ordered by priority (highest first)."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, node_type, db_row_id, wave_discovered, priority, reason "
            "FROM graph_expansion_nodes "
            "WHERE project_id = ? AND explored = 0 AND wave_discovered = ? "
            "ORDER BY priority DESC, id",
            (project_id, wave),
        )
        rows = await cursor.fetchall()
        return [{"id": r[0], "node_type": r[1], "db_row_id": r[2],
                 "wave_discovered": r[3], "priority": r[4], "reason": r[5]} for r in rows]
    finally:
        await db.close()


async def mark_node_explored(project_id: int, node_type: str, db_row_id: int) -> None:
    db = await get_db()
    try:
        await db.execute(
            "UPDATE graph_expansion_nodes SET explored = 1 "
            "WHERE project_id = ? AND node_type = ? AND db_row_id = ?",
            (project_id, node_type, db_row_id),
        )
        await db.commit()
    finally:
        await db.close()


async def add_expansion_node(
    project_id: int, node_type: str, db_row_id: int, wave: int,
    priority: int = 50, reason: str = "",
) -> bool:
    """Insert an expansion node. Returns True if newly inserted."""
    db = await get_db()
    try:
        r = await db.execute(
            "INSERT OR IGNORE INTO graph_expansion_nodes "
            "(project_id, node_type, db_row_id, wave_discovered, explored, priority, reason) "
            "VALUES (?, ?, ?, ?, 0, ?, ?)",
            (project_id, node_type, db_row_id, wave, priority, reason),
        )
        await db.commit()
        return r.rowcount > 0
    finally:
        await db.close()


async def add_expansion_edge(
    project_id: int,
    source_type: str, source_db_id: int,
    target_type: str, target_db_id: int,
    relation: str, wave: int,
) -> None:
    """Record a discovery edge. INSERT OR IGNORE (unique on target)."""
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR IGNORE INTO graph_expansion_edges "
            "(project_id, source_type, source_db_id, target_type, target_db_id, relation, wave) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (project_id, source_type, source_db_id, target_type, target_db_id, relation, wave),
        )
        await db.commit()
    finally:
        await db.close()


async def reset_expansion(project_id: int) -> None:
    """Clear all expansion tracking for a project."""
    db = await get_db()
    try:
        await db.execute("DELETE FROM graph_expansion_edges WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM graph_expansion_nodes WHERE project_id = ?", (project_id,))
        await db.execute(
            "UPDATE graph_expansions SET desired_state='idle', runtime_state='idle', "
            "current_wave=0, nodes_discovered=0, nodes_explored=0, "
            "heartbeat_at=NULL, updated_at=datetime('now') WHERE project_id = ?",
            (project_id,),
        )
        await db.commit()
    finally:
        await db.close()


async def seed_node_if_expansion_exists(
    project_id: int, node_type: str, db_row_id: int,
    priority: int = 50, reason: str = "auto-seeded",
) -> None:
    """Seed a node into graph_expansion_nodes if an expansion row exists for this project.

    Called after adding keywords/competitors via service.py or web/app.py to keep
    the graph frontier in sync with newly added entities.
    Does nothing if no expansion has been created for the project.
    """
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id FROM graph_expansions WHERE project_id = ?", (project_id,),
        )
        if not await cursor.fetchone():
            return  # No expansion exists, skip seeding
        await db.execute(
            "INSERT OR IGNORE INTO graph_expansion_nodes "
            "(project_id, node_type, db_row_id, wave_discovered, explored, priority, reason) "
            "VALUES (?, ?, ?, 0, 0, ?, ?)",
            (project_id, node_type, db_row_id, priority, reason),
        )
        await db.commit()
    finally:
        await db.close()


async def fix_stale_expansions(timeout_seconds: int = 60) -> int:
    """Mark expansions with stale heartbeats as interrupted. Called on startup."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "UPDATE graph_expansions "
            "SET runtime_state = 'interrupted', desired_state = 'paused', "
            "updated_at = datetime('now') "
            "WHERE runtime_state = 'running' "
            "AND (heartbeat_at IS NULL OR heartbeat_at < datetime('now', ? || ' seconds'))",
            (f"-{timeout_seconds}",),
        )
        await db.commit()
        return cursor.rowcount
    finally:
        await db.close()


async def _get_expansion_edge_lookup(project_id: int) -> dict[tuple[str, int], tuple[str, int]]:
    """Return {(target_type, target_db_id): (source_type, source_db_id)} for expansion edges."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT source_type, source_db_id, target_type, target_db_id "
            "FROM graph_expansion_edges WHERE project_id = ?",
            (project_id,),
        )
        rows = await cursor.fetchall()
        return {(r[2], r[3]): (r[0], r[1]) for r in rows}
    finally:
        await db.close()


async def _get_expansion_depth_lookup(project_id: int) -> dict[tuple[str, int], tuple[int, bool]]:
    """Return {(node_type, db_row_id): (wave_discovered, explored)} for expansion nodes."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT node_type, db_row_id, wave_discovered, explored "
            "FROM graph_expansion_nodes WHERE project_id = ?",
            (project_id,),
        )
        rows = await cursor.fetchall()
        return {(r[0], r[1]): (r[2], bool(r[3])) for r in rows}
    finally:
        await db.close()


# --- Knowledge graph data ---


async def get_graph_data(project_id: int) -> dict:
    """Build a force-graph-compatible JSON structure with nodes and links.

    Node types: brand, keyword, discussion, serp, competitor, competitor_keyword
    Link types: has_keyword, has_discussion, serp_rank, competitor_of, comp_keyword,
                keyword_overlap, expanded_from

    Expansion-aware: if expansion edges exist, discovered nodes link to their
    parent (the node that discovered them) instead of to the brand.
    """
    nodes: list[dict] = []
    links: list[dict] = []

    # 1. Brand node (center)
    project = await get_project(project_id)
    if not project:
        return {"nodes": [], "links": []}

    brand_id = f"brand_{project_id}"
    nodes.append({
        "id": brand_id,
        "label": project["brand_name"],
        "type": "brand",
        "url": project["url"],
        "category": project["category"],
        "depth": 0,
        "explored": True,
    })

    # Load expansion lookups
    edge_lookup = await _get_expansion_edge_lookup(project_id)
    depth_lookup = await _get_expansion_depth_lookup(project_id)

    # Helper: resolve graph node ID from (type, db_row_id)
    _type_prefix = {"keyword": "kw", "competitor": "comp", "competitor_keyword": "ckw"}

    def _graph_id(node_type: str, db_id: int) -> str:
        prefix = _type_prefix.get(node_type, node_type)
        return f"{prefix}_{db_id}"

    def _annotate(node: dict, node_type: str, db_id: int) -> dict:
        info = depth_lookup.get((node_type, db_id))
        if info:
            node["depth"] = info[0]
            node["explored"] = info[1]
        else:
            node["depth"] = 0
            node["explored"] = True
        return node

    def _link_source(node_type: str, db_id: int, default_source: str) -> tuple[str, str]:
        """Return (source_graph_id, link_type) using expansion edge if present."""
        parent = edge_lookup.get((node_type, db_id))
        if parent:
            return _graph_id(parent[0], parent[1]), "expanded_from"
        return default_source, None  # None means use default link type

    # 2. Keyword nodes
    keywords = await list_tracked_keywords(project_id)
    kw_name_to_id: dict[str, str] = {}
    for kw in keywords:
        kid = f"kw_{kw['id']}"
        kw_name_to_id[kw["keyword"].lower()] = kid
        nodes.append(_annotate(
            {"id": kid, "label": kw["keyword"], "type": "keyword"},
            "keyword", kw["id"],
        ))
        src, ltype = _link_source("keyword", kw["id"], brand_id)
        links.append({"source": src, "target": kid, "type": ltype or "has_keyword"})

    # 3. SERP ranking nodes (attach to keywords)
    serp_latest = await get_all_serp_latest(project_id)
    for s in serp_latest:
        sid = f"serp_{s['keyword']}"
        position = s.get("position")
        if position is None:
            continue
        provider = s.get("provider", "google")
        nodes.append({
            "id": sid,
            "label": f"#{position} {provider}",
            "type": "serp",
            "position": position,
            "provider": provider,
            "depth": 0,
            "explored": True,
        })
        kw_node = kw_name_to_id.get(s["keyword"].lower())
        links.append({"source": kw_node or brand_id, "target": sid, "type": "serp_rank"})

    # 4. Discussion nodes (no expansion — v1 skip)
    discussions = await get_tracked_discussions(project_id)
    for d in discussions:
        did = f"disc_{d['id']}"
        nodes.append({
            "id": did,
            "label": d["title"][:40] + ("..." if len(d["title"]) > 40 else ""),
            "type": "discussion",
            "platform": d["platform"],
            "url": d["url"],
            "engagement": d.get("engagement_score", 0) or 0,
            "comments": d.get("comments_count", 0) or 0,
            "depth": 0,
            "explored": True,
        })
        links.append({"source": brand_id, "target": did, "type": "has_discussion"})

    # 5. Competitor nodes + their keywords
    competitors = await list_competitors(project_id)
    for comp in competitors:
        cid = f"comp_{comp['id']}"
        nodes.append(_annotate(
            {"id": cid, "label": comp["name"], "type": "competitor", "url": comp.get("url")},
            "competitor", comp["id"],
        ))
        src, ltype = _link_source("competitor", comp["id"], brand_id)
        links.append({"source": src, "target": cid, "type": ltype or "competitor_of"})

        comp_kws = await list_competitor_keywords(comp["id"])
        for ckw in comp_kws:
            ckid = f"ckw_{ckw['id']}"
            nodes.append(_annotate(
                {"id": ckid, "label": ckw["keyword"], "type": "competitor_keyword"},
                "competitor_keyword", ckw["id"],
            ))
            ckw_src, ckw_ltype = _link_source("competitor_keyword", ckw["id"], cid)
            links.append({"source": ckw_src, "target": ckid, "type": ckw_ltype or "comp_keyword"})

            brand_kw_node = kw_name_to_id.get(ckw["keyword"].lower())
            if brand_kw_node:
                links.append({"source": brand_kw_node, "target": ckid, "type": "keyword_overlap"})

    # Expansion metadata
    expansion = await get_expansion(project_id)

    return {
        "nodes": nodes,
        "links": links,
        "expansion": {
            "desired_state": expansion["desired_state"],
            "runtime_state": expansion["runtime_state"],
            "current_wave": expansion["current_wave"],
            "nodes_discovered": expansion["nodes_discovered"],
            "nodes_explored": expansion["nodes_explored"],
        } if expansion else None,
    }


# ---------------------------------------------------------------------------
# Campaign Runs & Artifacts
# ---------------------------------------------------------------------------


async def create_campaign_run(
    project_id: int, goal: str, channels: list[str],
) -> dict:
    """Create a new campaign run."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO campaign_runs (project_id, goal, channels) VALUES (?, ?, ?)",
            (project_id, goal, json.dumps(channels)),
        )
        await db.commit()
        run_id = cursor.lastrowid
        return {"id": run_id, "project_id": project_id, "goal": goal,
                "channels": channels, "status": "drafting"}
    finally:
        await db.close()


async def add_campaign_artifact(
    run_id: int, artifact_type: str, content: str,
    channel: str | None = None, title: str = "",
) -> int:
    """Add an artifact (research_brief, angle_matrix, channel_draft, review) to a campaign."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO campaign_artifacts (run_id, artifact_type, channel, title, content) "
            "VALUES (?, ?, ?, ?, ?)",
            (run_id, artifact_type, channel, title, content),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def update_campaign_status(run_id: int, status: str) -> None:
    """Update campaign run status."""
    db = await get_db()
    try:
        completed = "datetime('now')" if status in ("completed", "cancelled") else "NULL"
        await db.execute(
            f"UPDATE campaign_runs SET status = ?, completed_at = {completed} WHERE id = ?",
            (status, run_id),
        )
        await db.commit()
    finally:
        await db.close()


async def get_campaign_run(run_id: int) -> dict | None:
    """Get a campaign run with its artifacts."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, project_id, goal, channels, status, created_at, completed_at "
            "FROM campaign_runs WHERE id = ?", (run_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        run = {
            "id": row[0], "project_id": row[1], "goal": row[2],
            "channels": json.loads(row[3]), "status": row[4],
            "created_at": row[5], "completed_at": row[6],
        }
        cursor = await db.execute(
            "SELECT id, artifact_type, channel, title, content, created_at "
            "FROM campaign_artifacts WHERE run_id = ? ORDER BY id",
            (run_id,),
        )
        rows = await cursor.fetchall()
        run["artifacts"] = [
            {"id": r[0], "artifact_type": r[1], "channel": r[2],
             "title": r[3], "content": r[4], "created_at": r[5]}
            for r in rows
        ]
        return run
    finally:
        await db.close()


async def list_campaign_runs(project_id: int, limit: int = 20) -> list[dict]:
    """List recent campaign runs for a project."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT cr.id, cr.goal, cr.channels, cr.status, cr.created_at, cr.completed_at, "
            "(SELECT COUNT(*) FROM campaign_artifacts ca WHERE ca.run_id = cr.id) as artifact_count "
            "FROM campaign_runs cr WHERE cr.project_id = ? ORDER BY cr.id DESC LIMIT ?",
            (project_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            {"id": r[0], "goal": r[1], "channels": json.loads(r[2]),
             "status": r[3], "created_at": r[4], "completed_at": r[5],
             "artifact_count": r[6]}
            for r in rows
        ]
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Insights
# ---------------------------------------------------------------------------


async def save_insight(
    project_id: int, insight_type: str, severity: str,
    title: str, summary: str, action_type: str, action_params: str,
) -> int:
    """Save an insight and return its id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO insights (project_id, insight_type, severity, title, summary, action_type, action_params) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (project_id, insight_type, severity, title, summary, action_type, action_params),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def is_insight_duplicate(project_id: int, insight_type: str, title: str) -> bool:
    """Check if a similar insight was created in the last 24 hours."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM insights "
            "WHERE project_id = ? AND insight_type = ? AND title = ? "
            "AND created_at > datetime('now', '-24 hours')",
            (project_id, insight_type, title),
        )
        row = await cursor.fetchone()
        return row[0] > 0
    finally:
        await db.close()


async def list_insights(
    project_id: int | None = None, unread_only: bool = False, limit: int = 20,
) -> list[dict]:
    """List insights, optionally filtered by project and read status."""
    db = await get_db()
    try:
        clauses = []
        params: list = []
        if project_id is not None:
            clauses.append("project_id = ?")
            params.append(project_id)
        if unread_only:
            clauses.append("read = 0")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        cursor = await db.execute(
            f"SELECT id, project_id, insight_type, severity, title, summary, "
            f"action_type, action_params, read, created_at "
            f"FROM insights {where} ORDER BY created_at DESC LIMIT ?",
            (*params, limit),
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0], "project_id": r[1], "insight_type": r[2],
                "severity": r[3], "title": r[4], "summary": r[5],
                "action_type": r[6], "action_params": r[7],
                "read": bool(r[8]), "created_at": r[9],
            }
            for r in rows
        ]
    finally:
        await db.close()


async def mark_insight_read(insight_id: int) -> bool:
    """Mark an insight as read. Returns True if updated."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "UPDATE insights SET read = 1 WHERE id = ? AND read = 0",
            (insight_id,),
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


async def get_insights_summary(project_id: int | None = None) -> dict:
    """Get unread insight count and latest 3 for the notification bell."""
    db = await get_db()
    try:
        where = "WHERE project_id = ? AND read = 0" if project_id else "WHERE read = 0"
        params = (project_id,) if project_id else ()

        cursor = await db.execute(f"SELECT COUNT(*) FROM insights {where}", params)
        count = (await cursor.fetchone())[0]

        cursor2 = await db.execute(
            f"SELECT id, project_id, insight_type, severity, title, summary, "
            f"action_type, action_params, created_at "
            f"FROM insights {where} ORDER BY created_at DESC LIMIT 3",
            params,
        )
        rows = await cursor2.fetchall()
        recent = [
            {
                "id": r[0], "project_id": r[1], "insight_type": r[2],
                "severity": r[3], "title": r[4], "summary": r[5],
                "action_type": r[6], "action_params": r[7], "created_at": r[8],
            }
            for r in rows
        ]
        return {"unread_count": count, "recent": recent}
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Autopilot helpers
# ---------------------------------------------------------------------------


async def get_pending_actionable_insights(project_id: int, limit: int = 3) -> list[dict]:
    """Get insights eligible for autopilot execution (warning/critical, not yet executed)."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, project_id, insight_type, severity, title, summary, "
            "action_type, action_params, created_at "
            "FROM insights "
            "WHERE project_id = ? "
            "  AND severity IN ('warning', 'critical') "
            "  AND execution_status = 'none' "
            "  AND created_at > datetime('now', '-48 hours') "
            "ORDER BY CASE severity WHEN 'critical' THEN 0 ELSE 1 END, created_at DESC "
            "LIMIT ?",
            (project_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0], "project_id": r[1], "insight_type": r[2],
                "severity": r[3], "title": r[4], "summary": r[5],
                "action_type": r[6], "action_params": r[7], "created_at": r[8],
            }
            for r in rows
        ]
    finally:
        await db.close()


async def update_insight_execution(
    insight_id: int, status: str, approval_id: int | None = None, context: str = "{}",
) -> None:
    """Update execution status of an insight."""
    db = await get_db()
    try:
        await db.execute(
            "UPDATE insights SET execution_status = ?, linked_approval_id = ?, execution_context = ? "
            "WHERE id = ?",
            (status, approval_id, context, insight_id),
        )
        await db.commit()
    finally:
        await db.close()


async def create_approval_with_source(
    project_id: int,
    channel: str,
    approval_type: str,
    content: str,
    payload: dict,
    preview: dict,
    *,
    title: str = "",
    target_label: str = "",
    target_url: str = "",
    agent_name: str = "",
    source_insight_id: int | None = None,
    pre_metrics_json: str = "{}",
) -> dict:
    """Insert a pending approval with source tracking and return the stored record."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO approvals (
                   project_id, channel, approval_type, title, target_label, target_url,
                   agent_name, content, payload_json, preview_json,
                   source_insight_id, pre_metrics_json
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                project_id, channel, approval_type, title, target_label, target_url,
                agent_name, content,
                json.dumps(payload, ensure_ascii=False),
                json.dumps(preview, ensure_ascii=False),
                source_insight_id, pre_metrics_json,
            ),
        )
        await db.commit()
        approval_id = cursor.lastrowid
    finally:
        await db.close()
    return await get_approval(approval_id)


async def snapshot_project_metrics(project_id: int) -> dict:
    """Take a snapshot of current project metrics for before/after comparison."""
    metrics = {}
    db = await get_db()
    try:
        # Latest GEO score
        cursor = await db.execute(
            "SELECT geo_score, visibility_score, position_score, sentiment_score "
            "FROM geo_scans WHERE project_id = ? ORDER BY scanned_at DESC LIMIT 1",
            (project_id,),
        )
        row = await cursor.fetchone()
        if row:
            metrics["geo"] = {"score": row[0], "visibility": row[1], "position": row[2], "sentiment": row[3]}

        # Latest SERP positions
        cursor = await db.execute(
            "SELECT keyword, position FROM serp_snapshots "
            "WHERE project_id = ? AND error IS NULL "
            "AND checked_at = (SELECT MAX(checked_at) FROM serp_snapshots WHERE project_id = ?)",
            (project_id, project_id),
        )
        serp_rows = await cursor.fetchall()
        if serp_rows:
            metrics["serp"] = {r[0]: r[1] for r in serp_rows}

        # Latest community hits
        cursor = await db.execute(
            "SELECT total_hits FROM community_scans WHERE project_id = ? ORDER BY scanned_at DESC LIMIT 1",
            (project_id,),
        )
        row = await cursor.fetchone()
        if row:
            metrics["community"] = {"total_hits": row[0]}
    finally:
        await db.close()
    return metrics


async def is_project_autopilot_enabled(project_id: int) -> bool:
    """Check if autopilot is enabled for any job of this project."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT autopilot FROM scheduled_jobs WHERE project_id = ? AND enabled = 1 LIMIT 1",
            (project_id,),
        )
        row = await cursor.fetchone()
        return bool(row and row[0])
    finally:
        await db.close()


async def count_recent_autopilot_approvals(project_id: int, hours: int = 24) -> int:
    """Count autopilot-generated approvals in the last N hours to prevent flooding."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM approvals "
            "WHERE project_id = ? AND source_insight_id IS NOT NULL "
            "AND created_at > datetime('now', ?)",
            (project_id, f"-{hours} hours"),
        )
        row = await cursor.fetchone()
        return row[0]
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Citability scans
# ---------------------------------------------------------------------------

async def save_citability_scan(
    project_id: int,
    url: str,
    avg_score: float,
    *,
    top_blocks_json: str = "[]",
    bottom_blocks_json: str = "[]",
    grade_distribution_json: str = "{}",
    report_json: str = "{}",
) -> int:
    """Save a citability scan snapshot. Returns scan id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO citability_scans
               (project_id, url, avg_score, top_blocks_json,
                bottom_blocks_json, grade_distribution_json, report_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (project_id, url, avg_score, top_blocks_json,
             bottom_blocks_json, grade_distribution_json, report_json),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def get_citability_history(project_id: int, limit: int = 20) -> list[dict]:
    """Return recent citability scans for a project."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, url, scanned_at, avg_score, grade_distribution_json
               FROM citability_scans WHERE project_id = ?
               ORDER BY scanned_at DESC LIMIT ?""",
            (project_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            {"id": r[0], "url": r[1], "scanned_at": r[2],
             "avg_score": r[3], "grade_distribution_json": r[4]}
            for r in rows
        ]
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# AI crawler scans
# ---------------------------------------------------------------------------

async def save_ai_crawler_scan(
    project_id: int,
    url: str,
    blocked_count: int,
    *,
    total_crawlers: int = 14,
    has_llms_txt: bool | None = None,
    results_json: str = "{}",
) -> int:
    """Save an AI crawler scan snapshot. Returns scan id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO ai_crawler_scans
               (project_id, url, blocked_count, total_crawlers,
                has_llms_txt, results_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (project_id, url, blocked_count, total_crawlers,
             int(has_llms_txt) if has_llms_txt is not None else None,
             results_json),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def get_ai_crawler_history(project_id: int, limit: int = 20) -> list[dict]:
    """Return recent AI crawler scans for a project."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, url, scanned_at, blocked_count, total_crawlers,
                      has_llms_txt, results_json
               FROM ai_crawler_scans WHERE project_id = ?
               ORDER BY scanned_at DESC LIMIT ?""",
            (project_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            {"id": r[0], "url": r[1], "scanned_at": r[2],
             "blocked_count": r[3], "total_crawlers": r[4],
             "has_llms_txt": bool(r[5]) if r[5] is not None else None,
             "results_json": r[6]}
            for r in rows
        ]
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Brand presence scans
# ---------------------------------------------------------------------------

async def save_brand_presence_scan(
    project_id: int,
    brand_name: str,
    footprint_score: int,
    *,
    platforms_json: str = "{}",
) -> int:
    """Save a brand presence scan snapshot. Returns scan id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO brand_presence_scans
               (project_id, brand_name, footprint_score, platforms_json)
               VALUES (?, ?, ?, ?)""",
            (project_id, brand_name, footprint_score, platforms_json),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def get_brand_presence_history(project_id: int, limit: int = 20) -> list[dict]:
    """Return recent brand presence scans for a project."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, brand_name, scanned_at, footprint_score, platforms_json
               FROM brand_presence_scans WHERE project_id = ?
               ORDER BY scanned_at DESC LIMIT ?""",
            (project_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            {"id": r[0], "brand_name": r[1], "scanned_at": r[2],
             "footprint_score": r[3], "platforms_json": r[4]}
            for r in rows
        ]
    finally:
        await db.close()
