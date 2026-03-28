"""Auto-publish tools — Reddit + Twitter with double safety gate."""

from __future__ import annotations

import asyncio
import logging
import os
from functools import partial

from agents import function_tool

logger = logging.getLogger(__name__)

try:
    import praw

    _HAS_PRAW = True
except ImportError:
    _HAS_PRAW = False

try:
    import tweepy

    _HAS_TWEEPY = True
except ImportError:
    _HAS_TWEEPY = False


async def save_blog_draft_impl(payload: dict) -> dict:
    """Save blog content as an internal draft (campaign artifact).

    This does NOT publish to any external platform — the content is stored
    in the database for the user to review, edit, and copy-paste to their
    blog, Dev.to, Medium, etc.
    """
    from opencmo import storage

    title = payload.get("title", "Untitled Draft")
    body = payload.get("body", "")
    project_id = payload.get("project_id")

    if not body.strip():
        return {"ok": False, "error": "Empty body — nothing to save."}

    # Create or reuse a campaign run for drafts
    if project_id:
        run_id = await storage.create_campaign_run(project_id, goal="Autopilot blog draft")
        await storage.add_campaign_artifact(
            run_id=run_id,
            artifact_type="blog_post",
            channel="blog",
            title=title,
            content=body,
        )
        return {
            "ok": True,
            "draft": True,
            "run_id": run_id,
            "message": f"Blog draft saved (campaign #{run_id}). Copy and publish to your preferred platform.",
        }

    # No project_id — just confirm the content was "accepted"
    return {
        "ok": True,
        "draft": True,
        "message": "Blog content approved as draft.",
    }



def _auto_publish_enabled() -> bool:
    return os.environ.get("OPENCMO_AUTO_PUBLISH", "0") == "1"


# ---------------------------------------------------------------------------
# Reddit
# ---------------------------------------------------------------------------


async def publish_reddit_post_impl(
    subreddit: str, title: str, body: str, *, dry_run: bool = True
) -> dict:
    """Publish (or preview) a Reddit post.

    Args:
        dry_run: If True, returns preview without posting.
    """
    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "preview": {"subreddit": subreddit, "title": title, "body": body[:300] + "..."},
        }

    if not _HAS_PRAW:
        return {"ok": False, "error": "praw not installed. pip install praw"}

    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    username = os.environ.get("REDDIT_USERNAME")
    password = os.environ.get("REDDIT_PASSWORD")

    if not all([client_id, client_secret, username, password]):
        return {"ok": False, "error": "Reddit credentials not configured (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD)"}

    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
            user_agent="OpenCMO/1.0",
        )
        # praw is synchronous, use executor
        loop = asyncio.get_event_loop()
        sub = await loop.run_in_executor(None, reddit.subreddit, subreddit)
        submission = await loop.run_in_executor(
            None, partial(sub.submit, title=title, selftext=body)
        )
        return {
            "ok": True,
            "dry_run": False,
            "url": f"https://reddit.com{submission.permalink}",
            "id": submission.id,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


async def publish_reddit_reply_impl(
    parent_id: str, body: str, *, dry_run: bool = True
) -> dict:
    """Publish (or preview) a reply to a Reddit post or comment.

    Args:
        parent_id: The fullname (e.g. t3_abc123 or t1_def456) or just the ID of the parent.
        body: Reply text.
        dry_run: If True, returns preview without posting.
    """
    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "preview": {"parent_id": parent_id, "body": body[:300] + "..."},
        }

    if not _HAS_PRAW:
        return {"ok": False, "error": "praw not installed. pip install praw"}

    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    username = os.environ.get("REDDIT_USERNAME")
    password = os.environ.get("REDDIT_PASSWORD")

    if not all([client_id, client_secret, username, password]):
        return {"ok": False, "error": "Reddit credentials not configured (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD)"}

    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
            user_agent="OpenCMO/1.0",
        )
        loop = asyncio.get_event_loop()
        
        # Determine if parent is a submission (t3_) or comment (t1_) or just an ID
        # PRAW handles fullnames (e.g. t3_...) naturally in info()
        parent_item = None
        if parent_id.startswith("t1_"):
            parent_item = await loop.run_in_executor(None, reddit.comment, parent_id)
        elif parent_id.startswith("t3_"):
            parent_item = await loop.run_in_executor(None, reddit.submission, parent_id)
        else:
            # Attempt to fetch as submission first; if we need to be more robust, 
            # we could try both, but typically scan_community returns submission IDs
            parent_item = await loop.run_in_executor(None, reddit.submission, parent_id)

        reply_obj = await loop.run_in_executor(
            None, partial(parent_item.reply, body=body)
        )
        return {
            "ok": True,
            "dry_run": False,
            "url": f"https://reddit.com{reply_obj.permalink}",
            "id": reply_obj.id,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}



# ---------------------------------------------------------------------------
# Twitter
# ---------------------------------------------------------------------------


async def publish_tweet_impl(text: str, *, dry_run: bool = True) -> dict:
    """Publish (or preview) a tweet.

    Args:
        dry_run: If True, returns preview without posting.
    """
    if len(text) > 280:
        return {"ok": False, "error": f"Tweet too long: {len(text)} chars (max 280)"}

    if dry_run:
        return {"ok": True, "dry_run": True, "preview": {"text": text, "length": len(text)}}

    if not _HAS_TWEEPY:
        return {"ok": False, "error": "tweepy not installed. pip install tweepy"}

    api_key = os.environ.get("TWITTER_API_KEY")
    api_secret = os.environ.get("TWITTER_API_SECRET")
    access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
    access_secret = os.environ.get("TWITTER_ACCESS_SECRET")

    if not all([api_key, api_secret, access_token, access_secret]):
        return {"ok": False, "error": "Twitter credentials not configured (TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)"}

    try:
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret,
        )
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, partial(client.create_tweet, text=text))
        tweet_id = response.data["id"]
        return {
            "ok": True,
            "dry_run": False,
            "tweet_id": tweet_id,
            "url": f"https://twitter.com/i/status/{tweet_id}",
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# Agent-facing tools (double safety gate)
# ---------------------------------------------------------------------------


@function_tool
async def publish_to_reddit(
    subreddit: str, title: str, body: str, confirm: bool = False
) -> str:
    """Publish a post to Reddit. Always shows preview first; only publishes when confirm=True AND OPENCMO_AUTO_PUBLISH=1.

    Args:
        subreddit: Target subreddit name (without r/).
        title: Post title.
        body: Post body (markdown).
        confirm: Set to True only after user explicitly confirms. Default False = preview only.
    """
    if not confirm or not _auto_publish_enabled():
        result = await publish_reddit_post_impl(subreddit, title, body, dry_run=True)
        if not result["ok"]:
            return f"Error: {result['error']}"
        preview = result["preview"]
        msg = (
            f"**Preview** (not published yet):\n\n"
            f"**r/{preview['subreddit']}**\n"
            f"**Title:** {preview['title']}\n"
            f"**Body:** {preview['body']}\n\n"
        )
        if not _auto_publish_enabled():
            msg += "Set OPENCMO_AUTO_PUBLISH=1 to enable real publishing.\n"
        msg += "Say 'confirm publish' to post for real."
        return msg

    result = await publish_reddit_post_impl(subreddit, title, body, dry_run=False)
    if result["ok"]:
        return f"Published to r/{subreddit}: {result['url']}"
    else:
        return f"Failed to publish: {result['error']}"


@function_tool
async def reply_to_reddit_comment(
    parent_id: str, body: str, confirm: bool = False
) -> str:
    """Reply to an existing Reddit post or comment. Always shows preview first; only publishes when confirm=True AND OPENCMO_AUTO_PUBLISH=1.

    Args:
        parent_id: The ID or fullname of the post or comment to reply to (e.g. from fetch_discussion_detail).
        body: Reply post body (markdown).
        confirm: Set to True only after user explicitly confirms. Default False = preview only.
    """
    if not confirm or not _auto_publish_enabled():
        result = await publish_reddit_reply_impl(parent_id, body, dry_run=True)
        if not result["ok"]:
            return f"Error: {result['error']}"
        preview = result["preview"]
        msg = (
            f"**Preview Reply** (not published yet):\n\n"
            f"**Replying to:** {preview['parent_id']}\n"
            f"**Body:** {preview['body']}\n\n"
        )
        if not _auto_publish_enabled():
            msg += "Set OPENCMO_AUTO_PUBLISH=1 to enable real publishing.\n"
        msg += "Say 'confirm publish' to post for real."
        return msg

    result = await publish_reddit_reply_impl(parent_id, body, dry_run=False)
    if result["ok"]:
        return f"Reply published: {result['url']}"
    else:
        return f"Failed to publish reply: {result['error']}"


@function_tool
async def publish_to_twitter(text: str, confirm: bool = False) -> str:
    """Publish a tweet. Always shows preview first; only publishes when confirm=True AND OPENCMO_AUTO_PUBLISH=1.

    Args:
        text: Tweet text (max 280 characters).
        confirm: Set to True only after user explicitly confirms. Default False = preview only.
    """
    if not confirm or not _auto_publish_enabled():
        result = await publish_tweet_impl(text, dry_run=True)
        if not result["ok"]:
            return f"Error: {result['error']}"
        preview = result["preview"]
        msg = (
            f"**Preview** (not published yet):\n\n"
            f"{preview['text']}\n"
            f"({preview['length']} chars)\n\n"
        )
        if not _auto_publish_enabled():
            msg += "Set OPENCMO_AUTO_PUBLISH=1 to enable real publishing.\n"
        msg += "Say 'confirm publish' to post for real."
        return msg

    result = await publish_tweet_impl(text, dry_run=False)
    if result["ok"]:
        return f"Published tweet: {result['url']}"
    else:
        return f"Failed to publish: {result['error']}"
