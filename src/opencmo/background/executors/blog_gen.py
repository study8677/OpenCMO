"""Executor for promotional blog generation tasks."""

from __future__ import annotations

import asyncio


async def run_blog_generation_executor(ctx) -> None:
    task = ctx.task
    payload = task["payload"]
    event_tasks: list[asyncio.Task] = []

    # Restore BYOK keys saved at enqueue time.
    from opencmo import llm
    user_keys: dict = payload.get("__user_keys") or {}
    llm_token = llm.set_request_keys(user_keys) if user_keys else None

    def on_progress(event: dict) -> None:
        event_tasks.append(
            asyncio.create_task(
                ctx.emit(
                    event_type="progress",
                    phase=event.get("phase", ""),
                    status=event.get("status", ""),
                    summary=event.get("summary", ""),
                    payload=event,
                )
            )
        )

    try:
        from opencmo.services.blog_generation import generate_promotional_blog

        result = await generate_promotional_blog(
            project_id=payload["project_id"],
            style=payload.get("style", "launch"),
            bilingual=payload.get("bilingual", False),
            task_id=task["task_id"],
            on_progress=on_progress,
        )
    finally:
        if event_tasks:
            await asyncio.gather(*event_tasks, return_exceptions=True)
        if llm_token is not None:
            llm.reset_request_keys(llm_token)

    await ctx.complete(result)
