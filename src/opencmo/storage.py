"""SQLite storage layer for persistent scan data."""

from __future__ import annotations

import json
import os
from pathlib import Path

import aiosqlite

_DB_PATH = Path(os.environ.get("OPENCMO_DB_PATH", Path.home() / ".opencmo" / "data.db"))

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
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


async def get_db() -> aiosqlite.Connection:
    """Open (or create) the database, ensure schema, enable WAL mode."""
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(_DB_PATH))
    await db.execute("PRAGMA journal_mode=WAL")
    await db.executescript(_SCHEMA)
    await db.commit()
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


async def remove_scheduled_job(job_id: int) -> bool:
    """Remove a scheduled job. Returns True if deleted."""
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM scheduled_jobs WHERE id = ?", (job_id,))
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


async def create_chat_session(session_id: str, title: str = "") -> None:
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO chat_sessions (id, title) VALUES (?, ?)",
            (session_id, title),
        )
        await db.commit()
    finally:
        await db.close()


async def list_chat_sessions() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, title, created_at, updated_at FROM chat_sessions ORDER BY updated_at DESC"
        )
        rows = await cursor.fetchall()
        return [
            {"id": r[0], "title": r[1], "created_at": r[2], "updated_at": r[3]}
            for r in rows
        ]
    finally:
        await db.close()


async def get_chat_session(session_id: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, title, input_items, created_at, updated_at FROM chat_sessions WHERE id = ?",
            (session_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return {
            "id": row[0], "title": row[1], "input_items": row[2],
            "created_at": row[3], "updated_at": row[4],
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
