"""Brand Kit storage — per-project brand guidelines for agent content generation."""

from __future__ import annotations

import json

from opencmo.storage._db import get_db


async def get_brand_kit(project_id: int) -> dict | None:
    """Return brand kit for a project, or None if not set."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT project_id, tone_of_voice, target_audience, core_values,
                      forbidden_words, best_examples, custom_instructions, updated_at
               FROM brand_kits WHERE project_id = ?""",
            (project_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            "project_id": row[0],
            "tone_of_voice": row[1],
            "target_audience": row[2],
            "core_values": row[3],
            "forbidden_words": json.loads(row[4] or "[]"),
            "best_examples": row[5],
            "custom_instructions": row[6],
            "updated_at": row[7],
        }
    finally:
        await db.close()


async def upsert_brand_kit(
    project_id: int,
    *,
    tone_of_voice: str = "",
    target_audience: str = "",
    core_values: str = "",
    forbidden_words: list[str] | None = None,
    best_examples: str = "",
    custom_instructions: str = "",
) -> dict:
    """Create or update the brand kit for a project."""
    fw_json = json.dumps(forbidden_words or [], ensure_ascii=False)
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO brand_kits (
                   project_id, tone_of_voice, target_audience, core_values,
                   forbidden_words, best_examples, custom_instructions, updated_at
               ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
               ON CONFLICT(project_id) DO UPDATE SET
                   tone_of_voice = excluded.tone_of_voice,
                   target_audience = excluded.target_audience,
                   core_values = excluded.core_values,
                   forbidden_words = excluded.forbidden_words,
                   best_examples = excluded.best_examples,
                   custom_instructions = excluded.custom_instructions,
                   updated_at = datetime('now')
            """,
            (
                project_id, tone_of_voice, target_audience, core_values,
                fw_json, best_examples, custom_instructions,
            ),
        )
        await db.commit()
    finally:
        await db.close()
    return await get_brand_kit(project_id)


def _render_brand_overlay(kit: dict) -> str:
    """Render a structured brand overlay with bounded priority."""
    parts = [
        "## Brand Overlay",
        "- This overlay is lower priority than truth, evidence, and channel-native rules.",
        "- Preserve the brand where it does not conflict with those higher-priority rules.",
    ]
    if kit.get("tone_of_voice"):
        parts.append(f"- Tone: {kit['tone_of_voice']}")
    if kit.get("target_audience"):
        parts.append(f"- Audience: {kit['target_audience']}")
    if kit.get("core_values"):
        parts.append(f"- Core Values: {kit['core_values']}")
    if kit.get("forbidden_words"):
        words = ", ".join(kit["forbidden_words"])
        parts.append(f"- Forbidden: {words}")
    if kit.get("best_examples"):
        parts.append(f"- Best Examples:\n{kit['best_examples']}")
    if kit.get("custom_instructions"):
        parts.append(f"- Custom Notes: {kit['custom_instructions']}")
    return "\n".join(parts)


async def build_brand_kit_prompt(project_id: int) -> str:
    """Build a system prompt fragment from the brand kit. Returns empty string if no kit."""
    kit = await get_brand_kit(project_id)
    if not kit:
        return ""
    return _render_brand_overlay(kit)
