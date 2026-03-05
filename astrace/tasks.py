from __future__ import annotations

import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

from .engine import ResearchEngine


@dataclass
class ResearchTaskState:
    task_id: str
    created_at: float
    status: str = "queued"
    result: dict[str, Any] | None = None
    error: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


class ResearchTaskManager:
    def __init__(self, engine: ResearchEngine, max_workers: int = 2) -> None:
        self.engine = engine
        self.pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="astrace")
        self._lock = threading.Lock()
        self._tasks: dict[str, ResearchTaskState] = {}

    def start(self, **kwargs: Any) -> str:
        task_id = uuid.uuid4().hex
        state = ResearchTaskState(
            task_id=task_id,
            created_at=time.time(),
            status="queued",
            params=kwargs,
        )
        with self._lock:
            self._tasks[task_id] = state

        self.pool.submit(self._run_task, task_id, kwargs)
        return task_id

    def get_status(self, task_id: str) -> dict[str, Any]:
        state = self._tasks.get(task_id)
        if not state:
            return {"task_id": task_id, "status": "not_found"}
        return {
            "task_id": state.task_id,
            "status": state.status,
            "created_at": state.created_at,
            "error": state.error,
        }

    def get_result(self, task_id: str) -> dict[str, Any]:
        state = self._tasks.get(task_id)
        if not state:
            return {"task_id": task_id, "status": "not_found"}
        return {
            "task_id": state.task_id,
            "status": state.status,
            "error": state.error,
            "result": state.result,
        }

    def _run_task(self, task_id: str, kwargs: dict[str, Any]) -> None:
        self._update(task_id, status="running")
        try:
            result = self.engine.run(**kwargs)
            self._update(task_id, status="done", result=result)
        except Exception as exc:
            self._update(task_id, status="failed", error=str(exc))

    def _update(
        self,
        task_id: str,
        *,
        status: str | None = None,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        with self._lock:
            state = self._tasks[task_id]
            if status:
                state.status = status
            if result is not None:
                state.result = result
            if error is not None:
                state.error = error

