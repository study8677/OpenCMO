"""Server-Sent Events router for real-time task progress streaming."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter
from starlette.responses import StreamingResponse

from opencmo.web import task_registry

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
    record = task_registry.get_task(task_id)
    if record is None:
        return StreamingResponse(
            iter([f"data: {json.dumps({'type': 'error', 'message': 'Task not found'})}\n\n"]),
            media_type="text/event-stream",
            status_code=404,
        )

    async def _event_stream():
        cursor = 0  # how many progress items we already sent

        # Catch-up: replay all existing events
        while cursor < len(record.progress):
            event = record.progress[cursor]
            yield f"data: {json.dumps({'type': 'progress', **event}, ensure_ascii=False)}\n\n"
            cursor += 1

        # Stream new events until task finishes
        while record.status in ("pending", "running"):
            await asyncio.sleep(0.5)

            # Emit any new events that appeared since last check
            while cursor < len(record.progress):
                event = record.progress[cursor]
                yield f"data: {json.dumps({'type': 'progress', **event}, ensure_ascii=False)}\n\n"
                cursor += 1

        # Drain any remaining events produced after loop exit
        while cursor < len(record.progress):
            event = record.progress[cursor]
            yield f"data: {json.dumps({'type': 'progress', **event}, ensure_ascii=False)}\n\n"
            cursor += 1

        # Final "done" event with task summary
        done_payload = {
            "type": "done",
            "status": record.status,
            "summary": record.summary,
            "run_id": record.run_id,
            "findings_count": record.findings_count,
            "recommendations_count": record.recommendations_count,
            "error": record.error,
        }
        yield f"data: {json.dumps(done_payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
