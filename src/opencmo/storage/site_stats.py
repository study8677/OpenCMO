"""Storage helpers for lightweight site-wide counters."""

from __future__ import annotations

from opencmo.storage._db import get_db


async def get_site_counter(key: str) -> int:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT value FROM site_counters WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return int(row[0]) if row else 0
    finally:
        await db.close()


async def increment_site_counter(key: str, amount: int = 1) -> int:
    db = await get_db()
    try:
        await db.execute(
            """
            INSERT INTO site_counters (key, value, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET
                value = value + excluded.value,
                updated_at = datetime('now')
            """,
            (key, amount),
        )
        await db.commit()

        cursor = await db.execute("SELECT value FROM site_counters WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return int(row[0]) if row else 0
    finally:
        await db.close()
