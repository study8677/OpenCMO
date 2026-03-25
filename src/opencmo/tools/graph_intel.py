"""Graph intelligence tool — on-demand competitive landscape query for CMO agent."""

from __future__ import annotations

from agents import function_tool

from opencmo.context import build_project_context


@function_tool
async def get_competitive_landscape(project_id: int) -> str:
    """Get the full competitive landscape intelligence from the knowledge graph.

    Returns a structured report including:
    - All known competitors and their keywords
    - Keyword overlap matrix (keywords both brand and competitors rank for)
    - SERP ranking distribution
    - Keyword gaps (competitor keywords the brand doesn't cover)
    - Graph expansion state and unexplored frontier nodes

    Call this tool when the user asks about competitor analysis, keyword strategy,
    content positioning, market landscape, or competitive intelligence.

    Args:
        project_id: The project ID to query.
    """
    ctx = await build_project_context(project_id, depth="full")
    if not ctx:
        return "No project found or no graph data available. Run a graph expansion first."
    return ctx
