"""Scheduled jobs storage."""

from __future__ import annotations

from opencmo.storage._db import get_db


async def add_scheduled_job(
    project_id: int,
    job_type: str,
    locale: str = "en",
    cron_expr: str = "0 9 * * *",
) -> int:
    """Add a scheduled job. Returns job id."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO scheduled_jobs (project_id, job_type, locale, cron_expr) VALUES (?, ?, ?, ?)",
            (project_id, job_type, locale, cron_expr),
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
                      j.job_type, j.locale, j.cron_expr, j.enabled, j.last_run_at, j.next_run_at
               FROM scheduled_jobs j JOIN projects p ON j.project_id = p.id
               ORDER BY j.id"""
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0], "project_id": r[1], "brand_name": r[2], "url": r[3],
                "category": r[4], "job_type": r[5], "locale": r[6], "cron_expr": r[7],
                "enabled": bool(r[8]), "last_run_at": r[9], "next_run_at": r[10],
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
                      j.job_type, j.locale, j.cron_expr, j.enabled, j.last_run_at, j.next_run_at
               FROM scheduled_jobs j JOIN projects p ON j.project_id = p.id
               WHERE j.id = ?""",
            (job_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0], "project_id": row[1], "brand_name": row[2], "url": row[3],
            "category": row[4], "job_type": row[5], "locale": row[6], "cron_expr": row[7],
            "enabled": bool(row[8]), "last_run_at": row[9], "next_run_at": row[10],
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
    locale: str | None = None,
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
        if locale is not None:
            parts.append("locale = ?")
            params.append(locale)
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
