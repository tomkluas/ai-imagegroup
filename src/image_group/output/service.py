from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path


class OutputService:
    def __init__(self, output_root: Path, person_names: dict[str, str]):
        self.output_root = Path(output_root).resolve(); self.person_names = dict(person_names)
    def task_root(self, task_id: str) -> Path: return self.output_root / task_id
    def person_dir(self, task_id: str, person_id: str) -> Path: return self.task_root(task_id) / self.person_names[person_id]
    def materialize(self, task_id: str, source: Path, person_ids: list[str]) -> list[Path]:
        source = Path(source).resolve(strict=True); content = self._sha(source); results = []
        for person_id in dict.fromkeys(person_ids):
            folder = self.person_dir(task_id, person_id); folder.mkdir(parents=True, exist_ok=True)
            target = folder / source.name
            if target.exists() and self._sha(target) != content: target = folder / f"{source.stem}_{content[:8]}{source.suffix.lower()}"
            if not target.exists(): self._atomic_copy(source, target)
            results.append(target)
        return results
    def remove_assignment(self, task_id: str, person_id: str, output_path: Path) -> None:
        path = Path(output_path).resolve(); root = self.person_dir(task_id, person_id).resolve()
        if not path.is_relative_to(root): raise ValueError("输出路径超出任务目录")
        path.unlink(missing_ok=True)
    def add_assignment(self, task_id: str, source: Path, person_id: str) -> Path:
        return self.materialize(task_id, source, [person_id])[0]
    @staticmethod
    def _sha(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""): digest.update(block)
        return digest.hexdigest()
    @staticmethod
    def _atomic_copy(source: Path, target: Path) -> None:
        part = target.with_suffix(target.suffix + ".part")
        shutil.copyfile(source, part)
        with part.open("r+b") as stream: os.fsync(stream.fileno())
        if part.stat().st_size != source.stat().st_size: part.unlink(missing_ok=True); raise OSError("复制大小校验失败")
        part.replace(target)
