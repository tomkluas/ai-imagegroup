from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol
@dataclass(frozen=True, slots=True)
class TaskItem: id: str; path: Path
@dataclass(frozen=True, slots=True)
class ProgressEvent: task_id: str; completed: int; total: int; state: str
class Processor(Protocol):
    def recognize(self, path: Path) -> list[str]: ...
class ResultOutput(Protocol):
    def materialize(self, task_id: str, source: Path, person_ids: list[str]) -> list[Path]: ...
class TaskRunner:
    def __init__(self, processor: Processor, output: ResultOutput, on_progress: Callable[[ProgressEvent], None] | None = None):
        self.processor, self.output, self.on_progress = processor, output, on_progress or (lambda event: None)
        self._tasks = {}
    def create(self, task_id: str, items: list[TaskItem]):
        self._tasks[task_id] = {"items": items, "recognized": {}, "copied": set(), "state": "created", "cancel": False}
    def cancel(self, task_id: str): self._tasks[task_id]["cancel"] = True
    def state(self, task_id: str): return self._tasks[task_id]["state"]
    def recognized_count(self, task_id: str): return len(self._tasks[task_id]["recognized"])
    def start(self, task_id: str):
        task = self._tasks[task_id]
        if task["cancel"]: task["state"] = "cancelled"; return
        task["state"] = "running"
        for item in task["items"]:
            if task["cancel"]: task["state"] = "cancelled"; return
            people = task["recognized"].setdefault(item.id, self.processor.recognize(item.path))
            try: self.output.materialize(task_id, item.path, people); task["copied"].add(item.id)
            except OSError as exc:
                if getattr(exc, "errno", None) == 28: task["state"] = "copy_paused"; return
                raise
            self.on_progress(ProgressEvent(task_id, len(task["copied"]), len(task["items"]), "running"))
        task["state"] = "completed"
    def resume(self, task_id: str):
        task = self._tasks[task_id]; task["state"] = "running"
        for item in task["items"]:
            if item.id in task["copied"]: continue
            try: self.output.materialize(task_id, item.path, task["recognized"][item.id]); task["copied"].add(item.id)
            except OSError as exc:
                if getattr(exc, "errno", None) == 28: task["state"] = "copy_paused"; return
                raise
        task["state"] = "completed"
