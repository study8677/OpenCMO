"""Persistent chat session management backed by SQLite."""

from __future__ import annotations

import json
import uuid

from opencmo import storage

MAX_HISTORY = 20


async def create_session() -> str:
    """Create a new chat session. Returns session_id."""
    session_id = uuid.uuid4().hex[:12]
    await storage.create_chat_session(session_id)
    return session_id


async def get_session(session_id: str) -> list | None:
    """Return input_items for a session, or None if not found."""
    row = await storage.get_chat_session(session_id)
    if row is None:
        return None
    return json.loads(row["input_items"])


async def update_session(session_id: str, input_items: list) -> None:
    """Replace session state with new input_items, applying truncation.

    Also auto-generates a title from the first user message if title is empty.
    """
    if len(input_items) > MAX_HISTORY:
        input_items = input_items[:1] + input_items[-(MAX_HISTORY - 1) :]

    # Auto-title: use first user message (truncated to 40 chars)
    row = await storage.get_chat_session(session_id)
    title = None
    if row and not row["title"]:
        for item in input_items:
            if isinstance(item, dict) and item.get("role") == "user":
                content = item.get("content", "")
                if isinstance(content, str) and content.strip():
                    title = content.strip()[:40]
                    break

    await storage.update_chat_session(session_id, json.dumps(input_items), title)


async def list_sessions() -> list[dict]:
    """Return all sessions (id, title, created_at, updated_at)."""
    return await storage.list_chat_sessions()


async def delete_session(session_id: str) -> bool:
    """Delete a session. Returns True if it existed."""
    return await storage.delete_chat_session(session_id)


async def get_session_messages(session_id: str) -> list[dict] | None:
    """Return display-ready messages for a session, or None if not found."""
    row = await storage.get_chat_session(session_id)
    if row is None:
        return None
    input_items = json.loads(row["input_items"])
    messages = []
    for item in input_items:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        if role in ("user", "assistant"):
            content = item.get("content", "")
            if isinstance(content, list):
                content = "".join(
                    p.get("text", "") for p in content if isinstance(p, dict)
                )
            if content:
                messages.append({"role": role, "content": content})
    return messages


async def clear_all() -> None:
    """Clear all sessions (for testing)."""
    await storage.clear_chat_sessions()
