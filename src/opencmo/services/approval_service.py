"""Approval service — manage content approvals and publishing."""

from __future__ import annotations

import os

from opencmo import storage

_APPROVAL_CHANNELS = {
    "reddit_post": "reddit",
    "reddit_reply": "reddit",
    "twitter_post": "twitter",
    "blog_post": "blog",
    "reddit_comment": "reddit",
}

_PUBLISH_ENV_KEYS = {
    "reddit": (
        "OPENCMO_AUTO_PUBLISH",
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USERNAME",
        "REDDIT_PASSWORD",
    ),
    "twitter": (
        "OPENCMO_AUTO_PUBLISH",
        "TWITTER_API_KEY",
        "TWITTER_API_SECRET",
        "TWITTER_ACCESS_TOKEN",
        "TWITTER_ACCESS_SECRET",
    ),
}


async def _hydrate_publish_settings(channel: str) -> None:
    """Load publish-related keys from DB into env for non-BYOK flows."""
    from opencmo import llm
    for key in _PUBLISH_ENV_KEYS.get(channel, ()):
        value = await llm.get_key_async(key)
        if value and not os.environ.get(key):
            os.environ[key] = value


def _require_payload_fields(payload: dict, *fields: str) -> None:
    missing = [field for field in fields if not str(payload.get(field, "")).strip()]
    if missing:
        raise ValueError(f"Missing required payload fields: {', '.join(missing)}")


async def _preview_approval_payload(approval_type: str, payload: dict) -> tuple[str, dict]:
    from opencmo.tools import publishers

    if approval_type == "reddit_post":
        _require_payload_fields(payload, "subreddit", "title", "body")
        result = await publishers.publish_reddit_post_impl(
            payload["subreddit"], payload["title"], payload["body"], dry_run=True,
        )
    elif approval_type == "reddit_reply":
        _require_payload_fields(payload, "parent_id", "body")
        result = await publishers.publish_reddit_reply_impl(
            payload["parent_id"], payload["body"], dry_run=True,
        )
    elif approval_type == "twitter_post":
        _require_payload_fields(payload, "text")
        result = await publishers.publish_tweet_impl(payload["text"], dry_run=True)
    elif approval_type in ("blog_post", "reddit_comment"):
        _require_payload_fields(payload, "body")
        result = {
            "ok": True,
            "preview": {
                "title": payload.get("title", ""),
                "body": payload.get("body", "")[:500],
                "content_preview": payload.get("body", "")[:300] + "...",
            },
        }
    else:
        raise ValueError(f"Unsupported approval_type: {approval_type}")

    if not result.get("ok"):
        raise ValueError(result.get("error") or "Failed to build approval preview.")

    return _APPROVAL_CHANNELS[approval_type], result["preview"]


async def _execute_approval_payload(approval_type: str, payload: dict) -> dict:
    from opencmo.tools import publishers

    if approval_type == "reddit_post":
        return await publishers.publish_reddit_post_impl(
            payload["subreddit"], payload["title"], payload["body"], dry_run=False,
        )
    if approval_type == "reddit_reply":
        return await publishers.publish_reddit_reply_impl(
            payload["parent_id"], payload["body"], dry_run=False,
        )
    if approval_type == "twitter_post":
        return await publishers.publish_tweet_impl(payload["text"], dry_run=False)
    if approval_type in ("blog_post", "reddit_comment"):
        # Internal draft — store as campaign artifact, no external publish needed
        return await publishers.save_blog_draft_impl(payload)
    return {"ok": False, "error": f"Unsupported approval_type: {approval_type}"}


async def create_approval(
    project_id: int,
    approval_type: str,
    payload: dict,
    *,
    content: str = "",
    title: str = "",
    target_label: str = "",
    target_url: str = "",
    agent_name: str = "",
) -> dict:
    """Create a pending approval from the exact publish payload."""
    channel, preview = await _preview_approval_payload(approval_type, payload)
    body = content.strip()
    if not body:
        body = payload.get("body") or payload.get("text") or title
    return await storage.create_approval(
        project_id,
        channel,
        approval_type,
        body,
        payload,
        preview,
        title=title,
        target_label=target_label,
        target_url=target_url,
        agent_name=agent_name,
    )


async def list_approvals(status: str | None = None, limit: int = 50) -> list[dict]:
    """List approval records."""
    return await storage.list_approvals(status=status, limit=limit)


async def get_approval(approval_id: int) -> dict | None:
    """Return one approval record."""
    return await storage.get_approval(approval_id)


async def approve_approval(approval_id: int, decision_note: str = "") -> dict:
    """Publish the exact stored approval payload and persist the outcome."""
    approval = await storage.get_approval(approval_id)
    if not approval:
        return {"ok": False, "error": "Approval not found."}
    if approval["status"] != "pending":
        return {"ok": False, "error": f"Approval is already {approval['status']}."}

    channel = approval["channel"]
    await _hydrate_publish_settings(channel)
    # Blog drafts are internal — skip the external publish gate
    if channel != "blog" and os.environ.get("OPENCMO_AUTO_PUBLISH", "0") != "1":
        return {
            "ok": False,
            "error": "OPENCMO_AUTO_PUBLISH is not enabled.",
            "error_code": "auto_publish_disabled",
            "approval": approval,
        }

    result = await _execute_approval_payload(approval["approval_type"], approval["payload"])
    if result.get("ok"):
        await storage.update_approval_status(
            approval_id,
            "approved",
            decision_note=decision_note,
            publish_result=result,
        )
        return {"ok": True, "approval": await storage.get_approval(approval_id)}

    await storage.update_approval_status(
        approval_id,
        "failed",
        decision_note=decision_note,
        publish_result=result,
    )
    return {"ok": False, "error": result.get("error", "Publish failed."), "approval": await storage.get_approval(approval_id)}


async def reject_approval(approval_id: int, decision_note: str = "") -> dict:
    """Reject a pending approval without publishing."""
    approval = await storage.get_approval(approval_id)
    if not approval:
        return {"ok": False, "error": "Approval not found."}
    if approval["status"] != "pending":
        return {"ok": False, "error": f"Approval is already {approval['status']}."}

    await storage.update_approval_status(approval_id, "rejected", decision_note=decision_note)
    return {"ok": True, "approval": await storage.get_approval(approval_id)}
