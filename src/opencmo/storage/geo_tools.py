"""Citability, AI crawler, and brand presence scan storage."""

from __future__ import annotations

from opencmo.storage._db import get_db

# --- Citability scans ---

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


# --- AI crawler scans ---

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


# --- Brand presence scans ---

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
