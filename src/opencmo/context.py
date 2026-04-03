"""Unified project context builder — graph-aware context for all agent interactions."""

from __future__ import annotations

from opencmo import storage


async def build_project_context(project_id: int, depth: str = "brief") -> str:
    """Build project context from the knowledge graph.

    Args:
        project_id: Project ID.
        depth: "brief" (~200 chars, for chat injection) or "full" (~800 chars, for research brief).

    Returns:
        Markdown-formatted context string, or empty string if project not found.
    """
    project = await storage.get_project(project_id)
    if not project:
        return ""

    graph = await storage.get_graph_data(project_id)
    nodes = graph.get("nodes", [])
    links = graph.get("links", [])

    # Classify nodes
    competitors = [n for n in nodes if n.get("type") == "competitor"]
    keywords = [n for n in nodes if n.get("type") == "keyword"]
    serp_nodes = [n for n in nodes if n.get("type") == "serp"]
    discussions = [n for n in nodes if n.get("type") == "discussion"]
    comp_keywords = [n for n in nodes if n.get("type") == "competitor_keyword"]
    overlaps = [lnk for lnk in links if lnk.get("type") == "keyword_overlap"]

    # Frontier: unexplored high-priority nodes
    frontier = [n for n in nodes if not n.get("explored", True) and n.get("depth", 0) > 0]

    parts = [f"# {project['brand_name']} ({project['category']})"]
    parts.append(f"URL: {project['url']}")

    # Always include keyword list — agents need concrete terms
    if keywords:
        kw_labels = [n["label"] for n in keywords[:15]]
        parts.append(f"Keywords: {', '.join(kw_labels)}")

    if depth == "brief":
        parts.append(
            f"Competitors: {len(competitors)} | Keywords: {len(keywords)} "
            f"| Overlaps: {len(overlaps)} | Discussions: {len(discussions)}"
        )
        if serp_nodes:
            top10 = [n for n in serp_nodes if (n.get("position") or 999) <= 10]
            parts.append(f"SERP: {len(top10)} in top 10, {len(serp_nodes)} tracked")
        # Top keyword gaps (competitor keywords not in brand keywords)
        brand_kw_labels = {n["label"].lower() for n in keywords}
        gaps = [n for n in comp_keywords if n["label"].lower() not in brand_kw_labels]
        if gaps:
            gap_labels = [g["label"] for g in gaps[:3]]
            parts.append(f"Keyword gaps: {', '.join(gap_labels)}")
        if frontier:
            parts.append(f"Unexplored frontier: {len(frontier)} nodes")

        latest = await storage.get_latest_scans(project_id)
        geo = latest.get("geo")
        if geo and geo.get("score") is not None:
            parts.append(f"GEO: {geo['score']}/100")
    else:
        # ---- Latest scan scores ----
        latest = await storage.get_latest_scans(project_id)
        seo = latest.get("seo")
        geo = latest.get("geo")
        community = latest.get("community")
        serp_data = latest.get("serp", [])
        score_parts = []
        if seo and seo.get("score") is not None:
            score_parts.append(f"SEO {seo['score']}/100")
        if geo and geo.get("score") is not None:
            score_parts.append(f"GEO {geo['score']}/100")
        if community:
            score_parts.append(f"Community {community.get('total_hits', 0)} hits")
        if serp_data:
            top10 = sum(1 for s in serp_data if (s.get("position") or 999) <= 10)
            score_parts.append(f"SERP {top10}/{len(serp_data)} in top 10")
        if score_parts:
            parts.append(f"Scores: {' | '.join(score_parts)}")

        # ---- Latest findings (scan insights) ----
        try:
            findings_rows = await storage.get_task_findings_by_project(project_id, limit=6)
        except Exception:
            findings_rows = []
        if findings_rows:
            parts.append("\n## Recent Findings")
            for f in findings_rows:
                parts.append(f"- [{f.get('severity', 'info')}] {f.get('title', '')}")

        # ---- Full competitive landscape ----
        if competitors:
            parts.append("\n## Competitive Landscape")
            # Build competitor -> keywords mapping via links
            comp_kw_map: dict[str, list[str]] = {}
            for lnk in links:
                if lnk.get("type") == "comp_keyword":
                    src = lnk["source"]
                    tgt_node = next((n for n in nodes if n["id"] == lnk["target"]), None)
                    if tgt_node:
                        comp_kw_map.setdefault(src, []).append(tgt_node["label"])
            for comp in competitors[:8]:
                kws = comp_kw_map.get(comp["id"], [])
                kw_str = f" — keywords: {', '.join(kws[:4])}" if kws else ""
                parts.append(f"- **{comp['label']}**{kw_str}")

        if overlaps:
            parts.append(f"\n## Keyword Overlaps ({len(overlaps)} shared)")
            overlap_kws: set[str] = set()
            for lnk in overlaps:
                src_node = next((n for n in nodes if n["id"] == lnk["source"]), None)
                if src_node:
                    overlap_kws.add(src_node["label"])
            if overlap_kws:
                parts.append(f"Shared: {', '.join(list(overlap_kws)[:10])}")

        # Keyword gaps
        brand_kw_labels = {n["label"].lower() for n in keywords}
        gaps = [n for n in comp_keywords if n["label"].lower() not in brand_kw_labels]
        if gaps:
            parts.append(f"\n## Keyword Gaps ({len(gaps)} uncovered)")
            for g in gaps[:8]:
                parts.append(f"- {g['label']}")

        if serp_nodes:
            parts.append("\n## SERP Rankings")
            for s in sorted(serp_nodes, key=lambda x: x.get("position", 999))[:10]:
                parts.append(f"- #{s.get('position', '?')} {s['label']}")

        # Expansion state
        expansion = graph.get("expansion")
        if expansion:
            parts.append(
                f"\n## Graph Expansion"
                f"\nState: {expansion['runtime_state']} | Wave: {expansion['current_wave']}"
                f" | Discovered: {expansion['nodes_discovered']} | Explored: {expansion['nodes_explored']}"
            )
        if frontier:
            parts.append(f"Frontier: {len(frontier)} unexplored nodes")

    # Append Brand Kit guidelines if available
    brand_prompt = await storage.build_brand_kit_prompt(project_id)
    if brand_prompt:
        parts.append(f"\n{brand_prompt}")

    return "\n".join(parts)


async def resolve_chat_project(body: dict) -> int | None:
    """Infer project_id from a chat request body.

    Priority:
    1. Explicit project_id in body
    2. Auto-detect when only one project exists (common for indie devs)
    """
    pid = body.get("project_id")
    if pid:
        try:
            return int(pid)
        except (ValueError, TypeError):
            pass
    projects = await storage.list_projects()
    if len(projects) == 1:
        return projects[0]["id"]
    return None
