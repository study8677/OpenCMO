"""Performance Tracker — fetch post-publish metrics for approved content."""

from __future__ import annotations

import json
import logging

from opencmo import storage
from opencmo.storage._db import get_db

logger = logging.getLogger(__name__)


async def fetch_reddit_post_metrics(post_url: str) -> dict | None:
    """Fetch engagement metrics from a Reddit post URL using PRAW."""
    try:
        import os

        import praw

        reddit = praw.Reddit(
            client_id=os.environ.get("REDDIT_CLIENT_ID", ""),
            client_secret=os.environ.get("REDDIT_CLIENT_SECRET", ""),
            username=os.environ.get("REDDIT_USERNAME", ""),
            password=os.environ.get("REDDIT_PASSWORD", ""),
            user_agent="OpenCMO/1.0",
        )
        submission = reddit.submission(url=post_url)
        return {
            "score": submission.score,
            "upvote_ratio": submission.upvote_ratio,
            "num_comments": submission.num_comments,
            "created_utc": submission.created_utc,
        }
    except Exception:
        logger.debug("Reddit metrics fetch failed for %s", post_url, exc_info=True)
        return None


async def fetch_tweet_metrics(tweet_id: str) -> dict | None:
    """Fetch engagement metrics from Twitter API v2."""
    try:
        import os

        import httpx

        bearer_token = os.environ.get("TWITTER_BEARER_TOKEN", "")
        if not bearer_token:
            return None
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.twitter.com/2/tweets/{tweet_id}",
                headers={"Authorization": f"Bearer {bearer_token}"},
                params={"tweet.fields": "public_metrics"},
            )
            if resp.status_code != 200:
                return None
            data = resp.json().get("data", {})
            metrics = data.get("public_metrics", {})
            return {
                "like_count": metrics.get("like_count", 0),
                "retweet_count": metrics.get("retweet_count", 0),
                "reply_count": metrics.get("reply_count", 0),
                "impression_count": metrics.get("impression_count", 0),
            }
    except Exception:
        logger.debug("Twitter metrics fetch failed for %s", tweet_id, exc_info=True)
        return None


async def collect_approval_metrics(approval_id: int) -> dict | None:
    """Collect post-publish metrics for a single approved item."""
    approval = await storage.get_approval(approval_id)
    if not approval or approval["status"] != "approved":
        return None

    publish_result = approval.get("publish_result")
    if not publish_result:
        return None

    channel = approval["channel"]
    metrics = None

    if channel == "reddit":
        url = publish_result.get("url")
        if url:
            metrics = await fetch_reddit_post_metrics(url)
    elif channel == "twitter":
        tweet_id = publish_result.get("tweet_id") or publish_result.get("id")
        if tweet_id:
            metrics = await fetch_tweet_metrics(str(tweet_id))

    if metrics:
        await update_post_metrics(approval_id, metrics)

    return metrics


async def update_post_metrics(approval_id: int, metrics: dict) -> None:
    """Store post-publish metrics on an approval record."""
    db = await get_db()
    try:
        await db.execute(
            "UPDATE approvals SET post_metrics_json = ? WHERE id = ?",
            (json.dumps(metrics, ensure_ascii=False), approval_id),
        )
        await db.commit()
    finally:
        await db.close()


async def list_approved_for_tracking(days: int = 14) -> list[dict]:
    """List approved items within the last N days that can have metrics refreshed."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, project_id, channel, approval_type, title, content,
                      publish_result_json, pre_metrics_json, post_metrics_json,
                      decided_at
               FROM approvals
               WHERE status = 'approved'
                 AND decided_at >= datetime('now', ?)
               ORDER BY decided_at DESC""",
            (f"-{days} days",),
        )
        rows = await cursor.fetchall()
        results = []
        for r in rows:
            results.append({
                "id": r[0],
                "project_id": r[1],
                "channel": r[2],
                "approval_type": r[3],
                "title": r[4],
                "content": (r[5] or "")[:200],
                "publish_result": json.loads(r[6]) if r[6] else None,
                "pre_metrics": json.loads(r[7] or "{}"),
                "post_metrics": json.loads(r[8] or "{}"),
                "decided_at": r[9],
            })
        return results
    finally:
        await db.close()


async def get_project_performance(project_id: int) -> list[dict]:
    """Get all trackable approvals for a project with their metrics."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, channel, approval_type, title, content,
                      publish_result_json, pre_metrics_json, post_metrics_json,
                      created_at, decided_at
               FROM approvals
               WHERE project_id = ? AND status = 'approved'
               ORDER BY decided_at DESC
               LIMIT 50""",
            (project_id,),
        )
        rows = await cursor.fetchall()
        results = []
        for r in rows:
            results.append({
                "id": r[0],
                "channel": r[1],
                "approval_type": r[2],
                "title": r[3],
                "content_preview": (r[4] or "")[:200],
                "publish_result": json.loads(r[5]) if r[5] else None,
                "pre_metrics": json.loads(r[6] or "{}"),
                "post_metrics": json.loads(r[7] or "{}"),
                "created_at": r[8],
                "decided_at": r[9],
            })
        return results
    finally:
        await db.close()


# --- Manual tracking ---

async def add_manual_tracking(
    project_id: int,
    platform: str,
    url: str,
    title: str = "",
    notes: str = "",
) -> int:
    """Add a manually tracked external URL for performance monitoring."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO manual_tracking (project_id, platform, url, title, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (project_id, platform, url, title, notes),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def list_manual_tracking(project_id: int) -> list[dict]:
    """List manually tracked items for a project."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT id, platform, url, title, notes, metrics_json, created_at
               FROM manual_tracking
               WHERE project_id = ?
               ORDER BY created_at DESC""",
            (project_id,),
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0],
                "platform": r[1],
                "url": r[2],
                "title": r[3],
                "notes": r[4],
                "metrics": json.loads(r[5] or "{}"),
                "created_at": r[6],
            }
            for r in rows
        ]
    finally:
        await db.close()


async def delete_manual_tracking(tracking_id: int) -> bool:
    """Delete a manually tracked item."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "DELETE FROM manual_tracking WHERE id = ?",
            (tracking_id,),
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()
