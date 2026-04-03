"""In-process worker for unified background tasks.

Concurrency is bounded by *max_concurrency* (total in-flight tasks) and
optional per-kind limits via *kind_concurrency*.  Claim uses an atomic
``BEGIN IMMEDIATE`` transaction in storage so multi-process deployments
remain safe.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Awaitable, Callable

from opencmo.background import service as bg_service
from opencmo.background.types import make_worker_id

Executor = Callable[["ExecutorContext"], Awaitable[None]]
logger = logging.getLogger(__name__)


class ExecutorContext:
    def __init__(self, task: dict):
        self.task = task

    async def emit(
        self,
        *,
        event_type: str = "progress",
        phase: str = "",
        status: str = "",
        summary: str = "",
        payload: dict | None = None,
    ) -> None:
        await bg_service.append_event(
            self.task["task_id"],
            event_type=event_type,
            phase=phase,
            status=status,
            summary=summary,
            payload=payload or {},
        )

    async def complete(self, result: dict) -> None:
        await bg_service.complete_task(self.task["task_id"], result=result)

    async def fail(self, error: dict) -> None:
        await bg_service.fail_task(self.task["task_id"], error=error)


class BackgroundWorker:
    """Polls for queued tasks and dispatches them to registered executors.

    Parameters
    ----------
    max_concurrency:
        Global upper bound on in-flight tasks across all kinds.
    kind_concurrency:
        Per-kind upper bound (e.g. ``{"scan": 2, "report": 1}``).
        Kinds not listed fall back to *max_concurrency*.
    """

    def __init__(
        self,
        *,
        poll_interval: float = 0.5,
        stale_after_seconds: int = 90,
        max_concurrency: int = 4,
        kind_concurrency: dict[str, int] | None = None,
    ):
        self.poll_interval = poll_interval
        self.stale_after_seconds = stale_after_seconds
        self.worker_id = make_worker_id()
        self.max_concurrency = max_concurrency
        self._loop_task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self._executors: dict[str, Executor] = {}
        self._running_tasks: set[asyncio.Task] = set()
        # Concurrency gates — created lazily on first start()
        self._global_sem: asyncio.Semaphore | None = None
        self._kind_limits = kind_concurrency or {}
        self._kind_sems: dict[str, asyncio.Semaphore] = {}

    def _get_kind_sem(self, kind: str) -> asyncio.Semaphore | None:
        if kind not in self._kind_limits:
            return None
        if kind not in self._kind_sems:
            self._kind_sems[kind] = asyncio.Semaphore(self._kind_limits[kind])
        return self._kind_sems[kind]

    def register_executor(self, kind: str, executor: Executor) -> None:
        self._executors[kind] = executor

    async def start(self) -> None:
        if self._loop_task is not None:
            return
        self._stop.clear()
        self._global_sem = asyncio.Semaphore(self.max_concurrency)
        self._kind_sems.clear()
        self._loop_task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        if self._loop_task is None:
            return
        self._stop.set()
        await self._loop_task
        self._loop_task = None
        if self._running_tasks:
            for task in list(self._running_tasks):
                task.cancel()
            await asyncio.gather(*self._running_tasks, return_exceptions=True)

    async def _run_loop(self) -> None:
        while not self._stop.is_set():
            await bg_service.recover_stale_tasks(stale_after_seconds=self.stale_after_seconds)

            # Back-pressure: wait until at least one concurrency slot is free
            # before attempting to claim, to avoid unnecessary DB round-trips.
            if self._global_sem is not None and self._global_sem._value == 0:
                await asyncio.sleep(self.poll_interval)
                continue

            task = await bg_service.claim_next_task(worker_id=self.worker_id)
            if task is None:
                await asyncio.sleep(self.poll_interval)
                continue

            execution = asyncio.create_task(self._run_claimed_task(task))
            self._running_tasks.add(execution)
            execution.add_done_callback(self._running_tasks.discard)

    async def _run_claimed_task(self, task: dict) -> None:
        kind = task["kind"]
        kind_sem = self._get_kind_sem(kind)

        # Acquire global + per-kind semaphores before executing
        async with self._global_sem:
            if kind_sem is not None:
                await kind_sem.acquire()
            try:
                await self._execute_task(task)
            finally:
                if kind_sem is not None:
                    kind_sem.release()

    async def _execute_task(self, task: dict) -> None:
        heartbeat_task = asyncio.create_task(self._heartbeat_loop(task["task_id"]))
        try:
            executor = self._executors[task["kind"]]
            await bg_service.mark_task_running(task["task_id"], worker_id=self.worker_id)
            fresh = await bg_service.get_task(task["task_id"])
            await executor(ExecutorContext(fresh))
        except Exception as exc:
            await bg_service.fail_task(task["task_id"], error={"message": str(exc)})
        finally:
            heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await heartbeat_task

    async def _heartbeat_loop(self, task_id: str) -> None:
        while True:
            await asyncio.sleep(5)
            await bg_service.heartbeat(task_id, worker_id=self.worker_id)


_default_worker: BackgroundWorker | None = None


def get_background_worker() -> BackgroundWorker:
    global _default_worker
    if _default_worker is None:
        _default_worker = BackgroundWorker(
            max_concurrency=4,
            kind_concurrency={"scan": 1, "report": 1, "graph_expansion": 1},
        )
    return _default_worker
