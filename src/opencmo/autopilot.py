"""Autopilot Engine — turns insights into actionable content, pushed to approval queue.

Zero LLM *decision* cost. Decisions are rule-based (insight_type → agent mapping).
LLM is only invoked for content generation via the existing expert agents.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from opencmo import storage

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Action type → Agent mapping
# ---------------------------------------------------------------------------

# Maps insight_type to a list of (channel, agent_name, content_prompt_template) tuples.
# Templates use {brand}, {category}, {keyword}, {summary} placeholders.
INSIGHT_TO_ACTIONS: dict[str, list[dict]] = {
    "serp_drop": [
        {
            "channel": "blog",
            "agent": "blog_expert",
            "approval_type": "blog_post",
            "prompt": (
                "Write a high-quality SEO blog post for {brand} (category: {category}). "
                "Focus on the keyword '{keyword}' which recently dropped in search rankings. "
                "Context: {summary}. "
                "Make the content informative, include the keyword naturally, "
                "and optimize for search engines. Return the full blog post."
            ),
        },
    ],
    "geo_decline": [
        {
            "channel": "blog",
            "agent": "blog_expert",
            "approval_type": "blog_post",
            "prompt": (
                "Write a comparison/explainer article for {brand} (category: {category}) "
                "to improve AI search engine visibility. Context: {summary}. "
                "Include clear product positioning, feature comparisons with alternatives, "
                "and structured data-friendly formatting. "
                "Make it highly citable by AI systems like ChatGPT, Perplexity, and Claude."
            ),
        },
    ],
    "community_buzz": [
        {
            "channel": "reddit",
            "agent": "reddit_expert",
            "approval_type": "reddit_comment",
            "prompt": (
                "Write a helpful, authentic Reddit comment for {brand} (category: {category}). "
                "Context: {summary}. "
                "The comment should be genuinely helpful, not promotional. "
                "Mention {brand} naturally only if relevant to the discussion. "
                "Be conversational and add real value."
            ),
        },
    ],
    "competitor_gap": [
        {
            "channel": "blog",
            "agent": "blog_expert",
            "approval_type": "blog_post",
            "prompt": (
                "Write a comparison article for {brand} (category: {category}). "
                "Context: {summary}. "
                "Focus on keywords that competitors rank for but {brand} doesn't yet cover. "
                "Include honest comparisons and highlight {brand}'s unique strengths."
            ),
        },
    ],
    "seo_regress": [
        {
            "channel": "blog",
            "agent": "blog_expert",
            "approval_type": "blog_post",
            "prompt": (
                "Write a technical blog post for {brand} (category: {category}) "
                "focusing on SEO best practices and performance optimization. "
                "Context: {summary}. "
                "Include practical tips that demonstrate expertise in this domain."
            ),
        },
    ],
}

# Maximum autopilot approvals per project per 24h cycle
MAX_AUTOPILOT_PER_DAY = 3


# ---------------------------------------------------------------------------
# Content generation via existing agents
# ---------------------------------------------------------------------------


async def _generate_content_with_agent(agent_name: str, prompt: str) -> str | None:
    """Call an expert agent to generate content. Returns None on failure."""
    try:
        from opencmo.config import get_model

        from agents import Agent, Runner

        agent = Agent(
            name=agent_name,
            instructions=(
                f"You are {agent_name}, an expert content creator. "
                "Generate high-quality, publication-ready content based on the brief. "
                "Return ONLY the content, no meta-commentary."
            ),
            model=get_model(agent_name),
        )
        result = await Runner.run(agent, prompt)
        return result.final_output
    except Exception:
        logger.exception("Agent %s content generation failed", agent_name)
        return None


# ---------------------------------------------------------------------------
# Main autopilot execution
# ---------------------------------------------------------------------------


async def execute_autopilot(project_id: int) -> list[dict]:
    """Execute autopilot for a project: turn pending insights into approval items.

    Returns list of created approval summaries.
    """
    # Check if autopilot is enabled
    if not await storage.is_project_autopilot_enabled(project_id):
        logger.debug("Autopilot disabled for project %d", project_id)
        return []

    # Rate limit: max N approvals per day
    recent_count = await storage.count_recent_autopilot_approvals(project_id)
    if recent_count >= MAX_AUTOPILOT_PER_DAY:
        logger.info("Autopilot rate limit reached for project %d (%d/%d)", project_id, recent_count, MAX_AUTOPILOT_PER_DAY)
        return []

    remaining = MAX_AUTOPILOT_PER_DAY - recent_count

    # Get pending actionable insights
    insights = await storage.get_pending_actionable_insights(project_id, limit=remaining)
    if not insights:
        logger.debug("No actionable insights for project %d", project_id)
        return []

    # Get project info for prompt templates
    project = await storage.get_project(project_id)
    if not project:
        return []

    brand = project["brand_name"]
    category = project["category"]

    # Snapshot metrics before taking action
    pre_metrics = await storage.snapshot_project_metrics(project_id)
    pre_metrics_json = json.dumps(pre_metrics, ensure_ascii=False)

    created_approvals = []

    for insight in insights:
        insight_type = insight["insight_type"]
        actions = INSIGHT_TO_ACTIONS.get(insight_type)
        if not actions:
            await storage.update_insight_execution(insight["id"], "skipped")
            continue

        # Mark as generating
        await storage.update_insight_execution(insight["id"], "generating")

        # Extract keyword from insight title if available
        keyword = ""
        title = insight.get("title", "")
        if "'" in title:
            parts = title.split("'")
            if len(parts) >= 2:
                keyword = parts[1]

        for action in actions:
            prompt = action["prompt"].format(
                brand=brand,
                category=category,
                keyword=keyword or category,
                summary=insight["summary"],
            )

            # Generate content
            content = await _generate_content_with_agent(action["agent"], prompt)
            if not content:
                await storage.update_insight_execution(insight["id"], "failed")
                continue

            # Build approval payload
            payload = {
                "body": content,
                "title": f"[Autopilot] {insight['title']}",
                "project_id": project_id,
            }
            preview = {
                "content_preview": content[:500],
                "insight_type": insight_type,
                "insight_summary": insight["summary"],
                "why_this": f"Triggered by: {insight['title']}",
                "why_now": f"Detected at {insight['created_at']}",
                "why_here": f"Best channel: {action['channel']}",
            }

            # Create approval with source tracking
            approval = await storage.create_approval_with_source(
                project_id=project_id,
                channel=action["channel"],
                approval_type=action["approval_type"],
                content=content,
                payload=payload,
                preview=preview,
                title=f"[Autopilot] {insight['title']}",
                agent_name=action["agent"],
                source_insight_id=insight["id"],
                pre_metrics_json=pre_metrics_json,
            )

            # Update insight execution status
            await storage.update_insight_execution(
                insight["id"],
                "executed",
                approval_id=approval["id"] if approval else None,
                context=json.dumps({
                    "channel": action["channel"],
                    "agent": action["agent"],
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                }, ensure_ascii=False),
            )

            created_approvals.append({
                "approval_id": approval["id"] if approval else None,
                "insight_id": insight["id"],
                "insight_type": insight_type,
                "channel": action["channel"],
                "title": insight["title"],
            })

            logger.info(
                "Autopilot: created approval for project %d — %s via %s",
                project_id, insight["title"], action["channel"],
            )

            # Only generate for the first action per insight in MVP
            break

    if created_approvals:
        logger.info(
            "Autopilot: generated %d approvals for project %d",
            len(created_approvals), project_id,
        )

    return created_approvals
