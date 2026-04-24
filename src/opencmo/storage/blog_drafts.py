"""Blog drafts storage — CRUD for promotional blog generation results."""

from __future__ import annotations

import json

from opencmo.storage._db import get_db


async def create_blog_draft(
    project_id: int,
    task_id: str,
    style: str,
    language: str,
) -> dict:
    """Insert a new blog draft with status 'generating'. Returns the new row."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO blog_drafts (project_id, task_id, style, language)
               VALUES (?, ?, ?, ?)""",
            (project_id, task_id, style, language),
        )
        await db.commit()
        draft_id = cursor.lastrowid
    finally:
        await db.close()
    return await get_blog_draft(draft_id)  # type: ignore[arg-type]


async def update_blog_draft(
    draft_id: int,
    *,
    title: str | None = None,
    content: str | None = None,
    status: str | None = None,
    product_profile: dict | None = None,
    quality_scores: dict | None = None,
    paired_draft_id: int | None = None,
    approval_id: int | None = None,
    meta: dict | None = None,
) -> dict:
    """Update fields on an existing blog draft. Returns the updated row."""
    sets: list[str] = []
    params: list = []
    if title is not None:
        sets.append("title = ?")
        params.append(title)
    if content is not None:
        sets.append("content = ?")
        params.append(content)
    if status is not None:
        sets.append("status = ?")
        params.append(status)
        if status in ("completed", "failed"):
            sets.append("completed_at = datetime('now')")
    if product_profile is not None:
        sets.append("product_profile_json = ?")
        params.append(json.dumps(product_profile, ensure_ascii=False))
    if quality_scores is not None:
        sets.append("quality_scores_json = ?")
        params.append(json.dumps(quality_scores, ensure_ascii=False))
    if paired_draft_id is not None:
        sets.append("paired_draft_id = ?")
        params.append(paired_draft_id)
    if approval_id is not None:
        sets.append("approval_id = ?")
        params.append(approval_id)
    if meta is not None:
        sets.append("meta_json = ?")
        params.append(json.dumps(meta, ensure_ascii=False))
    if not sets:
        return await get_blog_draft(draft_id)  # type: ignore[return-value]
    params.append(draft_id)
    db = await get_db()
    try:
        await db.execute(
            f"UPDATE blog_drafts SET {', '.join(sets)} WHERE id = ?",
            tuple(params),
        )
        await db.commit()
    finally:
        await db.close()
    return await get_blog_draft(draft_id)  # type: ignore[return-value]


def _row_to_dict(row) -> dict:
    return {
        "id": row[0],
        "project_id": row[1],
        "task_id": row[2],
        "style": row[3],
        "language": row[4],
        "status": row[5],
        "title": row[6],
        "content": row[7],
        "product_profile": json.loads(row[8] or "{}"),
        "quality_scores": json.loads(row[9] or "{}"),
        "paired_draft_id": row[10],
        "approval_id": row[11],
        "meta": json.loads(row[12] or "{}"),
        "created_at": row[13],
        "completed_at": row[14],
    }


_SELECT_COLS = """id, project_id, task_id, style, language, status,
                  title, content, product_profile_json, quality_scores_json,
                  paired_draft_id, approval_id, meta_json,
                  created_at, completed_at"""


async def get_blog_draft(draft_id: int) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute(
            f"SELECT {_SELECT_COLS} FROM blog_drafts WHERE id = ?",
            (draft_id,),
        )
        row = await cursor.fetchone()
        return _row_to_dict(row) if row else None
    finally:
        await db.close()


async def list_blog_drafts(project_id: int, *, limit: int = 20) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            f"SELECT {_SELECT_COLS} FROM blog_drafts WHERE project_id = ? ORDER BY created_at DESC LIMIT ?",
            (project_id, limit),
        )
        rows = await cursor.fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        await db.close()


async def get_blog_drafts_by_task(task_id: str) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            f"SELECT {_SELECT_COLS} FROM blog_drafts WHERE task_id = ? ORDER BY id",
            (task_id,),
        )
        rows = await cursor.fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        await db.close()


async def count_blog_drafts(project_id: int) -> int:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM blog_drafts WHERE project_id = ?",
            (project_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else 0
    finally:
        await db.close()
