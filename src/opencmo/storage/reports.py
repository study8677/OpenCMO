"""Report storage for strategic and periodic AI CMO briefings."""

from __future__ import annotations

import json

from opencmo.storage._db import get_db

REPORT_KINDS = ("strategic", "periodic")
REPORT_AUDIENCES = ("human", "agent")


def _row_to_dict(row) -> dict:
    return {
        "id": row[0],
        "project_id": row[1],
        "kind": row[2],
        "audience": row[3],
        "version": row[4],
        "is_latest": bool(row[5]),
        "source_run_id": row[6],
        "window_start": row[7],
        "window_end": row[8],
        "generation_status": row[9],
        "status": row[9],
        "content": row[10],
        "content_html": row[11],
        "meta": json.loads(row[12] or "{}"),
        "created_at": row[13],
    }


async def create_report_bundle(
    *,
    project_id: int,
    kind: str,
    source_run_id: int | None,
    window_start: str | None,
    window_end: str | None,
    records: dict[str, dict],
) -> list[dict]:
    """Persist a versioned human+agent report bundle and mark it latest."""
    if kind not in REPORT_KINDS:
        raise ValueError(f"Unsupported report kind: {kind}")

    audiences = [aud for aud in REPORT_AUDIENCES if aud in records]
    if not audiences:
        raise ValueError("At least one report audience is required.")

    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT COALESCE(MAX(version), 0) FROM reports WHERE project_id = ? AND kind = ?",
            (project_id, kind),
        )
        version_row = await cursor.fetchone()
        version = int(version_row[0] or 0) + 1

        created_ids: list[int] = []
        for audience in audiences:
            record = records[audience]
            await db.execute(
                """UPDATE reports
                   SET is_latest = 0
                   WHERE project_id = ? AND kind = ? AND audience = ?""",
                (project_id, kind, audience),
            )
            insert = await db.execute(
                """INSERT INTO reports (
                       project_id, kind, audience, version, is_latest, source_run_id,
                       window_start, window_end, generation_status, content, content_html, meta_json
                   ) VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    project_id,
                    kind,
                    audience,
                    version,
                    source_run_id,
                    window_start,
                    window_end,
                    record.get("generation_status", "completed"),
                    record.get("content", ""),
                    record.get("content_html", ""),
                    json.dumps(record.get("meta", {}), ensure_ascii=False),
                ),
            )
            created_ids.append(insert.lastrowid)

        await db.commit()
    finally:
        await db.close()

    created: list[dict] = []
    for report_id in created_ids:
        report = await get_report(report_id)
        if report:
            created.append(report)
    created.sort(key=lambda item: REPORT_AUDIENCES.index(item["audience"]))
    return created


async def list_reports(
    project_id: int,
    *,
    kind: str | None = None,
    audience: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """List report records for a project, newest first."""
    db = await get_db()
    try:
        where = ["project_id = ?"]
        params: list[object] = [project_id]
        if kind:
            where.append("kind = ?")
            params.append(kind)
        if audience:
            where.append("audience = ?")
            params.append(audience)
        params.append(limit)
        cursor = await db.execute(
            f"""SELECT id, project_id, kind, audience, version, is_latest, source_run_id,
                       window_start, window_end, generation_status, content, content_html,
                       meta_json, created_at
                FROM reports
                WHERE {' AND '.join(where)}
                ORDER BY created_at DESC, id DESC
                LIMIT ?""",
            params,
        )
        rows = await cursor.fetchall()
        return [_row_to_dict(row) for row in rows]
    finally:
        await db.close()


async def get_report(report_id: int) -> dict | None:
    """Return one report record."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, project_id, kind, audience, version, is_latest, source_run_id,
                      window_start, window_end, generation_status, content, content_html,
                      meta_json, created_at
               FROM reports
               WHERE id = ?""",
            (report_id,),
        )
        row = await cursor.fetchone()
        return _row_to_dict(row) if row else None
    finally:
        await db.close()


async def get_latest_report(project_id: int, kind: str, audience: str) -> dict | None:
    """Return the latest report for one kind+audience pair."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, project_id, kind, audience, version, is_latest, source_run_id,
                      window_start, window_end, generation_status, content, content_html,
                      meta_json, created_at
               FROM reports
               WHERE project_id = ? AND kind = ? AND audience = ? AND is_latest = 1
               ORDER BY id DESC
               LIMIT 1""",
            (project_id, kind, audience),
        )
        row = await cursor.fetchone()
        return _row_to_dict(row) if row else None
    finally:
        await db.close()


async def get_latest_reports(project_id: int) -> dict:
    """Return the latest report pointer for each kind+audience pair."""
    latest = {
        kind: {audience: None for audience in REPORT_AUDIENCES}
        for kind in REPORT_KINDS
    }
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, project_id, kind, audience, version, is_latest, source_run_id,
                      window_start, window_end, generation_status, content, content_html,
                      meta_json, created_at
               FROM reports
               WHERE project_id = ? AND is_latest = 1
               ORDER BY id DESC""",
            (project_id,),
        )
        rows = await cursor.fetchall()
        for row in rows:
            item = _row_to_dict(row)
            if item["kind"] in latest and item["audience"] in latest[item["kind"]]:
                latest[item["kind"]][item["audience"]] = item
        return latest
    finally:
        await db.close()
