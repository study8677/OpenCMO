"""Project CRUD operations."""

from __future__ import annotations

from opencmo.storage._db import get_db


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


async def find_projects_by_brand(brand_name: str) -> list[dict]:
    """Find projects whose brand_name matches (case-insensitive)."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, brand_name, url, category FROM projects WHERE brand_name = ? COLLATE NOCASE",
            (brand_name,),
        )
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
        await db.execute("DELETE FROM reports WHERE project_id = ?", (project_id,))
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
        # Delete background tasks and their events
        await db.execute(
            """DELETE FROM background_task_events WHERE task_id IN
               (SELECT task_id FROM background_tasks WHERE project_id = ?)""",
            (project_id,),
        )
        await db.execute("DELETE FROM background_tasks WHERE project_id = ?", (project_id,))
        # Delete remaining tables with project_id
        await db.execute("DELETE FROM chat_sessions WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM approvals WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM graph_expansion_edges WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM citability_scans WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM ai_crawler_scans WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM brand_presence_scans WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM brand_kits WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM manual_tracking WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM report_tasks WHERE project_id = ?", (project_id,))
        # Delete the project itself
        cursor = await db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()
