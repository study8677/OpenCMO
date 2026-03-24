"""Research brief generator — creates a shared context document for multi-channel campaigns."""

from __future__ import annotations

from agents import function_tool

from opencmo import storage


@function_tool
async def generate_research_brief(
    project_id: int,
    goal: str,
    product_analysis: str,
    channels: str,
) -> str:
    """Generate a research brief that all channel experts will share as context.

    This creates a campaign run and produces a structured brief containing the
    product's core messaging, target audience, key angles, and channel-specific
    guidelines. All subsequent channel drafts in this campaign will reference
    this brief for consistency.

    Args:
        project_id: The project ID to create a campaign for.
        goal: The campaign goal (e.g., "launch announcement", "feature update", "community growth").
        product_analysis: Your analysis of the product (one-liner, selling points, target audience).
        channels: Comma-separated list of target channels (e.g., "twitter,reddit,zhihu,xiaohongshu").
    """
    channel_list = [c.strip() for c in channels.split(",") if c.strip()]

    # Create campaign run
    run = await storage.create_campaign_run(project_id, goal, channel_list)
    run_id = run["id"]

    # Gather existing project intelligence for the brief
    project = await storage.get_project(project_id)
    latest = await storage.get_latest_scans(project_id)
    competitors = await storage.list_competitors(project_id)
    discussions = await storage.get_tracked_discussions(project_id)

    # Build context sections
    sections = [
        f"# Research Brief — Campaign #{run_id}",
        f"**Goal**: {goal}",
        f"**Brand**: {project['brand_name']} ({project['url']})",
        f"**Category**: {project['category']}",
        f"**Target Channels**: {', '.join(channel_list)}",
        "",
        "## Product Analysis",
        product_analysis,
        "",
    ]

    # Add competitive intelligence if available
    if competitors:
        sections.append("## Competitive Landscape")
        for comp in competitors[:5]:
            sections.append(f"- **{comp['name']}** ({comp.get('url', 'N/A')})")
        sections.append("")

    # Add community signals if available
    hot_discussions = [d for d in discussions if d.get("engagement_score", 0) > 5][:5]
    if hot_discussions:
        sections.append("## Active Community Discussions")
        for d in hot_discussions:
            sections.append(f"- [{d['platform']}] {d['title']} (engagement: {d.get('engagement_score', 0)})")
        sections.append("")

    # Add SEO/GEO signals if available
    if latest.get("seo") and latest["seo"].get("score") is not None:
        sections.append(f"## SEO Status: {int(latest['seo']['score'] * 100)}% performance score")
    if latest.get("geo") and latest["geo"].get("score") is not None:
        sections.append(f"## GEO Status: {latest['geo']['score']}/100 AI visibility score")
    if latest.get("serp"):
        ranked = [s for s in latest["serp"] if s.get("position")]
        if ranked:
            kws = ", ".join(f"{s['keyword']} (#{s['position']})" for s in ranked[:5])
            sections.append(f"## SERP Rankings: {kws}")

    sections.extend([
        "",
        "## Channel Guidelines",
        "Each channel expert should:",
        "1. Reference this brief for consistent messaging",
        "2. Adapt the core angles to their platform's style and audience",
        "3. Maintain the same key claims and value propositions",
        "4. Cross-reference competitor positioning when relevant",
        "",
        f"**Campaign Run ID**: {run_id} (use this to track all artifacts)",
    ])

    brief_content = "\n".join(sections)

    # Store the brief as the first artifact
    await storage.add_campaign_artifact(
        run_id, "research_brief", brief_content, title="Research Brief",
    )

    return brief_content
