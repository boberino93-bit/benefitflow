from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from hashlib import sha256
import json
import os
import re

from .identity import ProjectBinding, ProjectScopeError


def _safe(value):
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value)).strip("-") or "artifact"


class ArtifactStore:
    def __init__(self, root: str | Path, binding: ProjectBinding):
        self.root = binding.assert_path(root)
        self.binding = binding

    def publish(self, metadata: dict, payload) -> Path:
        self.binding.assert_mutation_allowed()
        required = {"artifact_id", "project_id", "creator_agent_id", "task_id", "artifact_type", "version", "source"}
        missing = required - set(metadata)
        if missing:
            raise ValueError(f"Artifact metadata missing: {sorted(missing)}")
        if metadata["project_id"] != self.binding.project_id:
            raise ProjectScopeError("Foreign artifact write denied")
        if metadata["creator_agent_id"] != self.binding.agent_id:
            raise ProjectScopeError("Artifact creator does not match bound agent")
        if not isinstance(metadata["version"], int) or metadata["version"] < 1:
            raise ValueError("Artifact version must be a positive integer")
        record = {
            **metadata,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "payload": payload,
        }
        record["integrity"] = {
            "record_sha256": sha256(json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        }
        path = (
            self.root / self.binding.project_id / _safe(metadata["artifact_id"]) /
            f"v{metadata['version']:06d}.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        return path
