"""Server-Sent Events router for real-time task progress streaming."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter
from starlette.responses import StreamingResponse

from opencmo.background import service as bg_service
from opencmo.web.routers.tasks import serialize_background_task

router = APIRouter(prefix="/api/v1")


@router.get("/tasks/{task_id}/events")
async def api_v1_task_events(task_id: str):
    """Stream task progress events via Server-Sent Events (SSE).

    Behaviour:
    1. Immediately replays all existing progress events (catch-up).
    2. Then polls for new events every 500ms until the task completes.
    3. Sends a ``done`` event with the final task state and closes.

    If the task is already complete when the request arrives, the full
    history + done event is sent in one batch (no long-poll).
    """
    record = await bg_service.get_task(task_id)
    if record is not None:
        async def _background_event_stream():
            cursor = 0

            while True:
                events = await bg_service.list_task_events(task_id)
                while cursor < len(events):
                    event = events[cursor]
                    cursor += 1
                    if event["event_type"] != "progress":
                        continue
                    payload = event["payload"] or {
                        "stage": event["phase"],
                        "status": event["status"],
                        "summary": event["summary"],
                    }
                    yield f"data: {json.dumps({'type': 'progress', **payload}, ensure_ascii=False)}\n\n"

                current = await bg_service.get_task(task_id)
                if current is None:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Task not found'}, ensure_ascii=False)}\n\n"
                    return

                if current["status"] in {"completed", "failed", "cancelled"}:
                    detail = await serialize_background_task(current)
                    done_payload = {
                        "type": "done",
                        "status": detail["status"],
                        "summary": detail["summary"],
                        "run_id": detail["run_id"],
                        "findings_count": detail["findings_count"],
                        "recommendations_count": detail["recommendations_count"],
                        "error": detail["error"],
                    }
                    yield f"data: {json.dumps(done_payload, ensure_ascii=False)}\n\n"
                    return

                await asyncio.sleep(0.5)

        return StreamingResponse(
            _background_event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    return StreamingResponse(
        iter([f"data: {json.dumps({'type': 'error', 'message': 'Task not found'})}\n\n"]),
        media_type="text/event-stream",
        status_code=404,
    )
