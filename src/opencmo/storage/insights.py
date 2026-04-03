"""Insights storage and autopilot helpers."""

from __future__ import annotations

from opencmo.storage._db import get_db


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


# --- Autopilot helpers ---


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
