from datetime import datetime, timezone
from pathlib import Path
import json
import os
import re
import uuid

from .identity import ProjectBinding


def _safe(value):
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value)).strip("-") or "event"


def append_audit_event(root: str | Path, binding: ProjectBinding, *, operation: str, result: str,
                       resource: str, task_id: str | None = None, message_id: str | None = None,
                       before_version=None, after_version=None, detail=None):
    binding.assert_mutation_allowed()
    root = binding.assert_path(root)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    event_id = f"{binding.project_id}::{uuid.uuid4().hex}"
    record = {
        "project_id": binding.project_id,
        "event_id": event_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "agent_id": binding.agent_id,
        "agent_instance_id": binding.agent_instance_id,
        "task_id": task_id,
        "message_id": message_id,
        "operation": operation,
        "result": result,
        "resource": resource,
        "before_version": before_version,
        "after_version": after_version,
        "detail": detail,
    }
    path = root / binding.project_id / f"{stamp}__{_safe(operation)}__{event_id.split('::')[-1]}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return path
