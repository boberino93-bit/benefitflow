from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import json
import os
import time
import uuid

from .identity import ProjectBinding


class StaleWriteError(RuntimeError):
    pass


class StateLockTimeout(TimeoutError):
    pass


@contextmanager
def _resource_lock(lock_path: Path, *, attempts: int = 200, delay: float = 0.01):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = None
    for _ in range(attempts):
        try:
            fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            break
        except FileExistsError:
            time.sleep(delay)
    if fd is None:
        raise StateLockTimeout(f"Could not acquire lock: {lock_path}")
    try:
        os.write(fd, str(os.getpid()).encode("ascii", errors="ignore"))
        os.fsync(fd)
        yield
    finally:
        os.close(fd)
        lock_path.unlink(missing_ok=True)


class AtomicVersionedState:
    def __init__(self, root: str | Path, binding: ProjectBinding):
        self.root = binding.assert_path(root)
        self.binding = binding

    def _path(self, resource_id: str) -> Path:
        safe = "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in resource_id)
        return self.root / self.binding.project_id / f"{safe}.json"

    def read(self, resource_id: str):
        path = self._path(resource_id)
        if not path.exists():
            return {"project_id": self.binding.project_id, "version": 0, "value": None}
        return json.loads(path.read_text(encoding="utf-8"))

    def compare_and_set(self, resource_id: str, *, expected_version: int, value):
        self.binding.assert_mutation_allowed()
        path = self._path(resource_id)
        lock_path = path.with_suffix(path.suffix + ".lock")
        with _resource_lock(lock_path):
            current = self.read(resource_id)
            if current["project_id"] != self.binding.project_id:
                raise StaleWriteError("State ownership mismatch")
            if current["version"] != expected_version:
                raise StaleWriteError(
                    f"STALE_WRITE expected_version={expected_version} current_version={current['version']}"
                )
            next_record = {
                "project_id": self.binding.project_id,
                "version": expected_version + 1,
                "value": value,
            }
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.with_name(path.name + f".{uuid.uuid4().hex}.tmp")
            with temp.open("w", encoding="utf-8") as handle:
                json.dump(next_record, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, path)
            return next_record
