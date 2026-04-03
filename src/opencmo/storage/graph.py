"""Knowledge graph expansion and graph data building."""

from __future__ import annotations

from opencmo.storage._db import get_db
from opencmo.storage.competitors import list_competitor_keywords, list_competitors
from opencmo.storage.discussions import get_tracked_discussions
from opencmo.storage.projects import get_project
from opencmo.storage.serp import get_all_serp_latest, list_tracked_keywords

# --- Graph expansion state ---


def _expansion_row_to_dict(row) -> dict:
    return {
        "id": row[0], "project_id": row[1],
        "desired_state": row[2], "runtime_state": row[3],
        "current_wave": row[4], "nodes_discovered": row[5],
        "nodes_explored": row[6], "heartbeat_at": row[7],
        "created_at": row[8], "updated_at": row[9],
    }


async def get_or_create_expansion(project_id: int) -> dict:
    """Return the expansion row for a project, creating it if absent."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, project_id, desired_state, runtime_state, current_wave, "
            "nodes_discovered, nodes_explored, heartbeat_at, created_at, updated_at "
            "FROM graph_expansions WHERE project_id = ?",
            (project_id,),
        )
        row = await cursor.fetchone()
        if row:
            return _expansion_row_to_dict(row)
        await db.execute(
            "INSERT INTO graph_expansions (project_id) VALUES (?)", (project_id,),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT id, project_id, desired_state, runtime_state, current_wave, "
            "nodes_discovered, nodes_explored, heartbeat_at, created_at, updated_at "
            "FROM graph_expansions WHERE project_id = ?",
            (project_id,),
        )
        row = await cursor.fetchone()
        return _expansion_row_to_dict(row)
    finally:
        await db.close()


async def get_expansion(project_id: int) -> dict | None:
    """Read current expansion state. Returns None if no expansion exists."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, project_id, desired_state, runtime_state, current_wave, "
            "nodes_discovered, nodes_explored, heartbeat_at, created_at, updated_at "
            "FROM graph_expansions WHERE project_id = ?",
            (project_id,),
        )
        row = await cursor.fetchone()
        return _expansion_row_to_dict(row) if row else None
    finally:
        await db.close()


async def update_expansion(project_id: int, **kwargs) -> None:
    """Update expansion fields. Accepts: desired_state, runtime_state, current_wave,
    nodes_discovered, nodes_explored, heartbeat_at."""
    allowed = {"desired_state", "runtime_state", "current_wave",
               "nodes_discovered", "nodes_explored", "heartbeat_at"}
    sets = {k: v for k, v in kwargs.items() if k in allowed}
    if not sets:
        return
    sets["updated_at"] = "datetime('now')"
    clauses = []
    values = []
    for k, v in sets.items():
        if v == "datetime('now')":
            clauses.append(f"{k} = datetime('now')")
        else:
            clauses.append(f"{k} = ?")
            values.append(v)
    values.append(project_id)
    db = await get_db()
    try:
        await db.execute(
            f"UPDATE graph_expansions SET {', '.join(clauses)} WHERE project_id = ?",
            tuple(values),
        )
        await db.commit()
    finally:
        await db.close()


async def seed_expansion_nodes(project_id: int) -> int:
    """Insert existing keywords and competitors as wave-0 unexplored nodes. Idempotent.

    Assigns priority scores so the expansion engine explores the most valuable
    nodes first:
      - competitors: 90 (high value — discovering competitor landscape)
      - keywords without SERP data: 80 (need ranking info)
      - keywords with low SERP position: 70 (opportunity gaps)
      - keywords with good SERP position: 40 (already performing)
      - competitor_keywords: 60 (moderate — cross-reference value)
    """
    db = await get_db()
    try:
        count = 0
        # Keywords — prioritize those without SERP data or with low rankings
        cursor = await db.execute(
            """SELECT k.id, ss.position FROM tracked_keywords k
               LEFT JOIN (
                   SELECT keyword, position, ROW_NUMBER() OVER (
                       PARTITION BY keyword ORDER BY checked_at DESC
                   ) AS rn FROM serp_snapshots WHERE project_id = ?
               ) ss ON ss.keyword = k.keyword AND ss.rn = 1
               WHERE k.project_id = ?""",
            (project_id, project_id),
        )
        for row in await cursor.fetchall():
            kw_id, position = row[0], row[1]
            if position is None:
                priority = 80  # No SERP data — needs exploration
                reason = "no_serp_data"
            elif position > 10:
                priority = 70  # Low ranking — opportunity gap
                reason = f"low_rank_{position}"
            else:
                priority = 40  # Already ranking well
                reason = f"ranking_{position}"
            r = await db.execute(
                "INSERT OR IGNORE INTO graph_expansion_nodes "
                "(project_id, node_type, db_row_id, wave_discovered, explored, priority, reason) "
                "VALUES (?, 'keyword', ?, 0, 0, ?, ?)",
                (project_id, kw_id, priority, reason),
            )
            count += r.rowcount

        # Competitors — always high priority
        cursor = await db.execute(
            "SELECT id FROM competitors WHERE project_id = ?", (project_id,),
        )
        for row in await cursor.fetchall():
            r = await db.execute(
                "INSERT OR IGNORE INTO graph_expansion_nodes "
                "(project_id, node_type, db_row_id, wave_discovered, explored, priority, reason) "
                "VALUES (?, 'competitor', ?, 0, 0, 90, 'competitor_discovery')",
                (project_id, row[0]),
            )
            count += r.rowcount

        # Competitor keywords — moderate priority
        cursor = await db.execute(
            "SELECT ck.id FROM competitor_keywords ck "
            "JOIN competitors c ON c.id = ck.competitor_id "
            "WHERE c.project_id = ?",
            (project_id,),
        )
        for row in await cursor.fetchall():
            r = await db.execute(
                "INSERT OR IGNORE INTO graph_expansion_nodes "
                "(project_id, node_type, db_row_id, wave_discovered, explored, priority, reason) "
                "VALUES (?, 'competitor_keyword', ?, 0, 0, 60, 'comp_kw_cross_ref')",
                (project_id, row[0]),
            )
            count += r.rowcount
        await db.commit()
        return count
    finally:
        await db.close()


async def get_min_unexplored_wave(project_id: int) -> int | None:
    """Return the lowest wave number that has unexplored nodes, or None."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT MIN(wave_discovered) FROM graph_expansion_nodes "
            "WHERE project_id = ? AND explored = 0",
            (project_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row and row[0] is not None else None
    finally:
        await db.close()


async def get_frontier_nodes(project_id: int, wave: int) -> list[dict]:
    """Return unexplored nodes for exactly the given wave, ordered by priority (highest first)."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, node_type, db_row_id, wave_discovered, priority, reason "
            "FROM graph_expansion_nodes "
            "WHERE project_id = ? AND explored = 0 AND wave_discovered = ? "
            "ORDER BY priority DESC, id",
            (project_id, wave),
        )
        rows = await cursor.fetchall()
        return [{"id": r[0], "node_type": r[1], "db_row_id": r[2],
                 "wave_discovered": r[3], "priority": r[4], "reason": r[5]} for r in rows]
    finally:
        await db.close()


async def mark_node_explored(project_id: int, node_type: str, db_row_id: int) -> None:
    db = await get_db()
    try:
        await db.execute(
            "UPDATE graph_expansion_nodes SET explored = 1 "
            "WHERE project_id = ? AND node_type = ? AND db_row_id = ?",
            (project_id, node_type, db_row_id),
        )
        await db.commit()
    finally:
        await db.close()


async def add_expansion_node(
    project_id: int, node_type: str, db_row_id: int, wave: int,
    priority: int = 50, reason: str = "",
) -> bool:
    """Insert an expansion node. Returns True if newly inserted."""
    db = await get_db()
    try:
        r = await db.execute(
            "INSERT OR IGNORE INTO graph_expansion_nodes "
            "(project_id, node_type, db_row_id, wave_discovered, explored, priority, reason) "
            "VALUES (?, ?, ?, ?, 0, ?, ?)",
            (project_id, node_type, db_row_id, wave, priority, reason),
        )
        await db.commit()
        return r.rowcount > 0
    finally:
        await db.close()


async def add_expansion_edge(
    project_id: int,
    source_type: str, source_db_id: int,
    target_type: str, target_db_id: int,
    relation: str, wave: int,
) -> None:
    """Record a discovery edge. INSERT OR IGNORE (unique on target)."""
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR IGNORE INTO graph_expansion_edges "
            "(project_id, source_type, source_db_id, target_type, target_db_id, relation, wave) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (project_id, source_type, source_db_id, target_type, target_db_id, relation, wave),
        )
        await db.commit()
    finally:
        await db.close()


async def reset_expansion(project_id: int) -> None:
    """Clear all expansion tracking for a project."""
    db = await get_db()
    try:
        await db.execute("DELETE FROM graph_expansion_edges WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM graph_expansion_nodes WHERE project_id = ?", (project_id,))
        await db.execute(
            "UPDATE graph_expansions SET desired_state='idle', runtime_state='idle', "
            "current_wave=0, nodes_discovered=0, nodes_explored=0, "
            "heartbeat_at=NULL, updated_at=datetime('now') WHERE project_id = ?",
            (project_id,),
        )
        await db.commit()
    finally:
        await db.close()


async def seed_node_if_expansion_exists(
    project_id: int, node_type: str, db_row_id: int,
    priority: int = 50, reason: str = "auto-seeded",
) -> None:
    """Seed a node into graph_expansion_nodes if an expansion row exists for this project.

    Called after adding keywords/competitors via service.py or web/app.py to keep
    the graph frontier in sync with newly added entities.
    Does nothing if no expansion has been created for the project.
    """
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id FROM graph_expansions WHERE project_id = ?", (project_id,),
        )
        if not await cursor.fetchone():
            return  # No expansion exists, skip seeding
        await db.execute(
            "INSERT OR IGNORE INTO graph_expansion_nodes "
            "(project_id, node_type, db_row_id, wave_discovered, explored, priority, reason) "
            "VALUES (?, ?, ?, 0, 0, ?, ?)",
            (project_id, node_type, db_row_id, priority, reason),
        )
        await db.commit()
    finally:
        await db.close()


async def fix_stale_expansions(timeout_seconds: int = 60) -> int:
    """Mark expansions with stale heartbeats as interrupted. Called on startup."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "UPDATE graph_expansions "
            "SET runtime_state = 'interrupted', desired_state = 'paused', "
            "updated_at = datetime('now') "
            "WHERE runtime_state = 'running' "
            "AND (heartbeat_at IS NULL OR heartbeat_at < datetime('now', ? || ' seconds'))",
            (f"-{timeout_seconds}",),
        )
        await db.commit()
        return cursor.rowcount
    finally:
        await db.close()


async def _get_expansion_edge_lookup(project_id: int) -> dict[tuple[str, int], tuple[str, int]]:
    """Return {(target_type, target_db_id): (source_type, source_db_id)} for expansion edges."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT source_type, source_db_id, target_type, target_db_id "
            "FROM graph_expansion_edges WHERE project_id = ?",
            (project_id,),
        )
        rows = await cursor.fetchall()
        return {(r[2], r[3]): (r[0], r[1]) for r in rows}
    finally:
        await db.close()


async def _get_expansion_depth_lookup(project_id: int) -> dict[tuple[str, int], tuple[int, bool]]:
    """Return {(node_type, db_row_id): (wave_discovered, explored)} for expansion nodes."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT node_type, db_row_id, wave_discovered, explored "
            "FROM graph_expansion_nodes WHERE project_id = ?",
            (project_id,),
        )
        rows = await cursor.fetchall()
        return {(r[0], r[1]): (r[2], bool(r[3])) for r in rows}
    finally:
        await db.close()


# --- Knowledge graph data ---


async def get_graph_data(project_id: int) -> dict:
    """Build a force-graph-compatible JSON structure with nodes and links.

    Node types: brand, keyword, discussion, serp, competitor, competitor_keyword
    Link types: has_keyword, has_discussion, serp_rank, competitor_of, comp_keyword,
                keyword_overlap, expanded_from

    Expansion-aware: if expansion edges exist, discovered nodes link to their
    parent (the node that discovered them) instead of to the brand.
    """
    nodes: list[dict] = []
    links: list[dict] = []

    # 1. Brand node (center)
    project = await get_project(project_id)
    if not project:
        return {"nodes": [], "links": []}

    brand_id = f"brand_{project_id}"
    nodes.append({
        "id": brand_id,
        "label": project["brand_name"],
        "type": "brand",
        "url": project["url"],
        "category": project["category"],
        "depth": 0,
        "explored": True,
    })

    # Load expansion lookups
    edge_lookup = await _get_expansion_edge_lookup(project_id)
    depth_lookup = await _get_expansion_depth_lookup(project_id)

    # Helper: resolve graph node ID from (type, db_row_id)
    _type_prefix = {"keyword": "kw", "competitor": "comp", "competitor_keyword": "ckw"}

    def _graph_id(node_type: str, db_id: int) -> str:
        prefix = _type_prefix.get(node_type, node_type)
        return f"{prefix}_{db_id}"

    def _annotate(node: dict, node_type: str, db_id: int) -> dict:
        info = depth_lookup.get((node_type, db_id))
        if info:
            node["depth"] = info[0]
            node["explored"] = info[1]
        else:
            node["depth"] = 0
            node["explored"] = True
        return node

    def _link_source(node_type: str, db_id: int, default_source: str) -> tuple[str, str]:
        """Return (source_graph_id, link_type) using expansion edge if present."""
        parent = edge_lookup.get((node_type, db_id))
        if parent:
            return _graph_id(parent[0], parent[1]), "expanded_from"
        return default_source, None  # None means use default link type

    # 2. Keyword nodes
    keywords = await list_tracked_keywords(project_id)
    kw_name_to_id: dict[str, str] = {}
    for kw in keywords:
        kid = f"kw_{kw['id']}"
        kw_name_to_id[kw["keyword"].lower()] = kid
        nodes.append(_annotate(
            {"id": kid, "label": kw["keyword"], "type": "keyword"},
            "keyword", kw["id"],
        ))
        src, ltype = _link_source("keyword", kw["id"], brand_id)
        links.append({"source": src, "target": kid, "type": ltype or "has_keyword"})

    # 3. SERP ranking nodes (attach to keywords)
    serp_latest = await get_all_serp_latest(project_id)
    for s in serp_latest:
        sid = f"serp_{s['keyword']}"
        position = s.get("position")
        if position is None:
            continue
        provider = s.get("provider", "google")
        nodes.append({
            "id": sid,
            "label": f"#{position} {provider}",
            "type": "serp",
            "position": position,
            "provider": provider,
            "depth": 0,
            "explored": True,
        })
        kw_node = kw_name_to_id.get(s["keyword"].lower())
        links.append({"source": kw_node or brand_id, "target": sid, "type": "serp_rank"})

    # 4. Discussion nodes (no expansion — v1 skip)
    discussions = await get_tracked_discussions(project_id)
    for d in discussions:
        did = f"disc_{d['id']}"
        nodes.append({
            "id": did,
            "label": d["title"][:40] + ("..." if len(d["title"]) > 40 else ""),
            "type": "discussion",
            "platform": d["platform"],
            "url": d["url"],
            "engagement": d.get("engagement_score", 0) or 0,
            "comments": d.get("comments_count", 0) or 0,
            "depth": 0,
            "explored": True,
        })
        links.append({"source": brand_id, "target": did, "type": "has_discussion"})

    # 5. Competitor nodes + their keywords
    competitors = await list_competitors(project_id)
    for comp in competitors:
        cid = f"comp_{comp['id']}"
        nodes.append(_annotate(
            {"id": cid, "label": comp["name"], "type": "competitor", "url": comp.get("url")},
            "competitor", comp["id"],
        ))
        src, ltype = _link_source("competitor", comp["id"], brand_id)
        links.append({"source": src, "target": cid, "type": ltype or "competitor_of"})

        comp_kws = await list_competitor_keywords(comp["id"])
        for ckw in comp_kws:
            ckid = f"ckw_{ckw['id']}"
            nodes.append(_annotate(
                {"id": ckid, "label": ckw["keyword"], "type": "competitor_keyword"},
                "competitor_keyword", ckw["id"],
            ))
            ckw_src, ckw_ltype = _link_source("competitor_keyword", ckw["id"], cid)
            links.append({"source": ckw_src, "target": ckid, "type": ckw_ltype or "comp_keyword"})

            brand_kw_node = kw_name_to_id.get(ckw["keyword"].lower())
            if brand_kw_node:
                links.append({"source": brand_kw_node, "target": ckid, "type": "keyword_overlap"})

    # Expansion metadata
    expansion = await get_expansion(project_id)

    return {
        "nodes": nodes,
        "links": links,
        "expansion": {
            "desired_state": expansion["desired_state"],
            "runtime_state": expansion["runtime_state"],
            "current_wave": expansion["current_wave"],
            "nodes_discovered": expansion["nodes_discovered"],
            "nodes_explored": expansion["nodes_explored"],
        } if expansion else None,
    }
