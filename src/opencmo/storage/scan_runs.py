"""Monitoring scan runs, findings, and recommendations."""

from __future__ import annotations

import json

from opencmo.storage._db import get_db


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


async def fail_scan_run_by_task_id(task_id: str, message: str) -> None:
    """Mark the scan_run for a given background task_id as failed.

    Called when the background task is failed externally (stale heartbeat / recovery)
    so that the scan_run table stays in sync with the background_tasks table.
    """
    db = await get_db()
    try:
        await db.execute(
            """UPDATE scan_runs SET status='failed', summary=?, completed_at=datetime('now')
               WHERE task_id=? AND status='running'""",
            (message, task_id),
        )
        await db.commit()
    finally:
        await db.close()


async def update_scan_run_notes(task_id: str, notes: str) -> None:
    """Update user-editable notes on a scan run by task_id."""
    db = await get_db()
    try:
        await db.execute(
            "UPDATE scan_runs SET summary = ? WHERE task_id = ?",
            (notes, task_id),
        )
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
                   (run_id, domain, severity, title, summary, confidence, evidence_json, metadata_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id,
                    finding["domain"],
                    finding["severity"],
                    finding["title"],
                    finding["summary"],
                    finding.get("confidence"),
                    json.dumps(finding.get("evidence_refs", [])),
                    json.dumps(finding.get("metadata", {})),
                ),
            )

        for rec in recommendations:
            await db.execute(
                """INSERT INTO scan_recommendations
                   (run_id, domain, priority, owner_type, action_type, title, summary, rationale, confidence, evidence_json, metadata_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
                    json.dumps(rec.get("metadata", {})),
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
            """SELECT f.domain, f.severity, f.title, f.summary, f.confidence, f.evidence_json, f.metadata_json
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
                "metadata": json.loads(row[6] or "{}"),
            }
            for row in rows
        ]
    finally:
        await db.close()


async def get_task_findings_by_project(project_id: int, limit: int = 6) -> list[dict]:
    """Return most recent findings for a project (across all scan runs)."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT f.domain, f.severity, f.title, f.summary, f.metadata_json
               FROM scan_findings f
               JOIN scan_runs r ON r.id = f.run_id
               WHERE r.project_id = ?
               ORDER BY r.id DESC,
                 CASE f.severity
                   WHEN 'critical' THEN 0
                   WHEN 'warning' THEN 1
                   ELSE 2
                 END,
                 f.id
               LIMIT ?""",
            (project_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            {
                "domain": row[0],
                "severity": row[1],
                "title": row[2],
                "summary": row[3],
                "metadata": json.loads(row[4] or "{}"),
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
                      rec.title, rec.summary, rec.rationale, rec.confidence, rec.evidence_json, rec.metadata_json
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
                "metadata": json.loads(row[9] or "{}"),
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
