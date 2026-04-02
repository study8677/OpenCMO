"""Executor for graph expansion tasks."""

from __future__ import annotations

import asyncio

from opencmo import storage


async def run_graph_expansion_executor(ctx) -> None:
    from opencmo.graph_expansion import run_expansion

    task = ctx.task
    project_id = task["payload"]["project_id"]
    event_tasks: list[asyncio.Task] = []

    def on_progress(event: dict) -> None:
        event_tasks.append(
            asyncio.create_task(
                ctx.emit(
                    event_type="progress",
                    phase=event.get("stage", ""),
                    status=event.get("status", ""),
                    summary=event.get("summary", ""),
                    payload=event,
                )
            )
        )

    try:
        await run_expansion(project_id, on_progress=on_progress)
    finally:
        if event_tasks:
            await asyncio.gather(*event_tasks, return_exceptions=True)

    expansion = await storage.get_expansion(project_id)
    runtime_state = expansion["runtime_state"] if expansion else "idle"
    if runtime_state == "paused":
        summary = "Graph expansion paused"
    elif runtime_state == "idle":
        summary = "Graph expansion completed"
    else:
        summary = f"Graph expansion ended with state {runtime_state}"

    await ctx.complete(
        {
            "project_id": project_id,
            "summary": summary,
            "runtime_state": runtime_state,
            "current_wave": expansion["current_wave"] if expansion else 0,
            "nodes_discovered": expansion["nodes_discovered"] if expansion else 0,
            "nodes_explored": expansion["nodes_explored"] if expansion else 0,
        }
    )
