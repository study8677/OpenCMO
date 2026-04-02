"""Chat API router (SSE streaming)."""

from __future__ import annotations

import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.responses import StreamingResponse

from opencmo import storage

router = APIRouter(prefix="/api/v1")


@router.get("/chat/context/{project_id}")
async def api_v1_chat_context(project_id: int):
    """Return structured project context for the Chat UI."""
    project = await storage.get_project(project_id)
    if not project:
        return JSONResponse({"error": "Project not found"}, status_code=404)

    # Latest scan scores
    latest = await storage.get_latest_scans(project_id)

    # Graph data for competitors, keywords, gaps
    graph = await storage.get_graph_data(project_id)
    nodes = graph.get("nodes", [])
    links = graph.get("links", [])

    competitors = [
        {"label": n["label"], "url": n.get("url", "")}
        for n in nodes if n.get("type") == "competitor"
    ][:6]

    keywords = [
        n["label"]
        for n in nodes if n.get("type") == "keyword"
    ][:10]

    brand_kw_set = {n["label"].lower() for n in nodes if n.get("type") == "keyword"}
    keyword_gaps = [
        n["label"]
        for n in nodes
        if n.get("type") == "competitor_keyword" and n["label"].lower() not in brand_kw_set
    ][:5]

    # Latest findings from most recent scan run
    from opencmo.storage._db import get_db
    findings = []
    try:
        db = await get_db()
        cursor = await db.execute(
            """SELECT f.domain, f.severity, f.title
               FROM scan_findings f
               JOIN scan_runs r ON r.id = f.run_id
               WHERE r.project_id = ?
               ORDER BY r.id DESC, f.id
               LIMIT 4""",
            (project_id,),
        )
        rows = await cursor.fetchall()
        findings = [
            {"domain": row[0], "severity": row[1], "title": row[2]}
            for row in rows
        ]
        await db.close()
    except Exception:
        pass


    # Scores
    seo = latest.get("seo")
    geo = latest.get("geo")
    community = latest.get("community")
    serp = latest.get("serp", [])

    ctx = {
        "project": {
            "id": project["id"],
            "brand_name": project["brand_name"],
            "url": project["url"],
            "category": project["category"],
        },
        "scores": {
            "seo": seo.get("score") if seo else None,
            "geo": geo.get("score") if geo else None,
            "community_hits": community.get("total_hits") if community else None,
            "serp_tracked": len(serp),
            "serp_top10": sum(1 for s in serp if (s.get("position") or 999) <= 10),
        },
        "keywords": keywords,
        "competitors": competitors,
        "keyword_gaps": keyword_gaps,
        "findings": findings,
    }
    return JSONResponse(ctx)


def _get_item_name(item) -> str:
    """Safely extract tool/handoff name from a RunItem."""
    raw = getattr(item, "raw_item", None)
    if raw is not None and hasattr(raw, "name"):
        return raw.name
    return getattr(item, "title", None) or "unknown"


@router.post("/chat/sessions")
async def api_v1_chat_session_create(request: Request):
    from opencmo.web import chat_sessions
    body_bytes = await request.body()
    try:
        body = json.loads(body_bytes) if body_bytes else {}
    except json.JSONDecodeError:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    raw_project_id = body.get("project_id")
    project_id: int | None = None
    if raw_project_id is not None:
        try:
            project_id = int(raw_project_id)
        except (TypeError, ValueError):
            return JSONResponse({"error": "project_id must be an integer"}, status_code=400)
        project = await storage.get_project(project_id)
        if not project:
            return JSONResponse({"error": "Project not found"}, status_code=404)

    session_id = await chat_sessions.create_session(project_id=project_id)
    return JSONResponse({"session_id": session_id, "project_id": project_id}, status_code=201)


@router.get("/chat/sessions")
async def api_v1_chat_sessions_list():
    from opencmo.web import chat_sessions
    sessions = await chat_sessions.list_sessions()
    return JSONResponse(sessions)


@router.get("/chat/sessions/{session_id}/messages")
async def api_v1_chat_session_messages(session_id: str):
    from opencmo.web import chat_sessions
    messages = await chat_sessions.get_session_messages(session_id)
    if messages is None:
        return JSONResponse({"error": "Session not found"}, status_code=404)
    return JSONResponse(messages)


@router.delete("/chat/sessions/{session_id}")
async def api_v1_chat_session_delete(session_id: str):
    from opencmo.web import chat_sessions
    ok = await chat_sessions.delete_session(session_id)
    if not ok:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse({"ok": True})


_LOCALE_NAMES = {
    "en": "English",
    "zh": "Chinese (Simplified)",
    "ja": "Japanese",
    "ko": "Korean",
    "es": "Spanish",
}


@router.post("/chat")
async def api_v1_chat(request: Request):
    from opencmo.web import chat_sessions
    body = await request.json()
    session_id = body.get("session_id", "")
    message = body.get("message", "").strip()

    if not message:
        return JSONResponse({"error": "message is required"}, status_code=400)

    session = await storage.get_chat_session(session_id)
    if session is None:
        return JSONResponse({"error": "Invalid session_id"}, status_code=404)
    input_items = json.loads(session["input_items"])

    if body.get("project_id") is None and session.get("project_id") is not None:
        body["project_id"] = session["project_id"]

    context_item = None
    # Inject project context from knowledge graph
    from opencmo.context import resolve_chat_project, build_project_context
    project_id = await resolve_chat_project(body)
    if project_id:
        ctx = await build_project_context(project_id, depth="full")
        if ctx:
            input_items.insert(0, {"role": "system", "content": f"[Project Context]\n{ctx}"})
            context_item = input_items[0]

    # Inject locale-aware system prompt
    locale = body.get("locale", "en")
    lang_name = _LOCALE_NAMES.get(locale, "English")
    locale_prompt = {
        "role": "system",
        "content": f"[Language Preference]\nThe user's interface language is {lang_name}. You MUST respond in {lang_name}. All your output — analysis, recommendations, content drafts, and explanations — should be written in {lang_name}.",
    }
    insert_index = 1 if context_item is not None else 0
    input_items.insert(insert_index, locale_prompt)

    input_items.append({"role": "user", "content": message})

    async def event_stream():
        try:
            from agents import Runner
            from opencmo.agents.cmo import cmo_agent

            result = Runner.run_streamed(cmo_agent, input_items, max_turns=15)

            async for event in result.stream_events():
                if event.type == "raw_response_event":
                    data = event.data
                    if hasattr(data, "type") and data.type == "response.output_text.delta":
                        yield f"data: {json.dumps({'type': 'delta', 'content': data.delta})}\n\n"
                elif event.type == "agent_updated_stream_event":
                    yield f"data: {json.dumps({'type': 'agent', 'name': event.new_agent.name})}\n\n"
                elif event.type == "run_item_stream_event":
                    name = event.name
                    if name == "tool_called":
                        yield f"data: {json.dumps({'type': 'tool_call', 'name': _get_item_name(event.item)})}\n\n"
                    elif name == "tool_output":
                        yield f"data: {json.dumps({'type': 'tool_done'})}\n\n"
                    elif name == "handoff_requested":
                        yield f"data: {json.dumps({'type': 'handoff', 'target': _get_item_name(event.item)})}\n\n"
                    elif name == "handoff_occured":
                        yield f"data: {json.dumps({'type': 'handoff_done'})}\n\n"
                    elif name == "tool_search_called":
                        yield f"data: {json.dumps({'type': 'tool_search'})}\n\n"
                    elif name == "tool_search_output_created":
                        yield f"data: {json.dumps({'type': 'tool_search_done'})}\n\n"
                    elif name == "message_output_created":
                        yield f"data: {json.dumps({'type': 'message_created'})}\n\n"
                    elif name == "reasoning_item_created":
                        yield f"data: {json.dumps({'type': 'reasoning'})}\n\n"

            # Stream finished — persist session state
            updated_items = result.to_input_list()
            # Strip injected system prompts (locale + context) before persisting
            injected_contents = {locale_prompt["content"]}
            if context_item:
                injected_contents.add(context_item["content"])
            while (
                updated_items
                and isinstance(updated_items[0], dict)
                and updated_items[0].get("role") == "system"
                and updated_items[0].get("content") in injected_contents
            ):
                updated_items = updated_items[1:]
            await chat_sessions.update_session(session_id, updated_items)
            agent_name = result.last_agent.name if result.last_agent else "CMO Agent"
            yield f"data: {json.dumps({'type': 'done', 'agent_name': agent_name, 'final_output': result.final_output})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
