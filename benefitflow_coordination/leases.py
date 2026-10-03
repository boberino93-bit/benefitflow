from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import os
import uuid

from .identity import ProjectBinding, ProjectScopeError
from .state import _resource_lock, StaleWriteError


class LeaseConflict(RuntimeError):
    pass


def _utc(value=None):
    return value or datetime.now(timezone.utc)


def _parse(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class LeaseStore:
    def __init__(self, root: str | Path, binding: ProjectBinding):
        self.root = binding.assert_path(root)
        self.binding = binding

    def _path(self, resource_id: str):
        safe = "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in resource_id)
        return self.root / self.binding.project_id / f"{safe}.json"

    def _load(self, path: Path):
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def claim(self, resource_id: str, *, ttl_seconds: int, now=None):
        self.binding.assert_mutation_allowed()
        now = _utc(now)
        path = self._path(resource_id)
        with _resource_lock(path.with_suffix(".lock")):
            current = self._load(path)
            if current and _parse(current["expires_at"]) > now:
                raise LeaseConflict("ACTIVE_LEASE")
            version = (current or {}).get("version", 0) + 1
            lease = {
                "project_id": self.binding.project_id,
                "resource_id": resource_id,
                "holder_agent_instance_id": self.binding.agent_instance_id,
                "lease_id": f"{self.binding.project_id}::{uuid.uuid4().hex}",
                "version": version,
                "acquired_at": now.isoformat().replace("+00:00", "Z"),
                "expires_at": (now + timedelta(seconds=ttl_seconds)).isoformat().replace("+00:00", "Z"),
                "renewals": 0,
            }
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(lease, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            os.replace(tmp, path)
            return lease

    def renew(self, resource_id: str, *, lease_id: str, expected_version: int, ttl_seconds: int, now=None):
        self.binding.assert_mutation_allowed()
        now = _utc(now)
        path = self._path(resource_id)
        with _resource_lock(path.with_suffix(".lock")):
            current = self._load(path)
            if not current:
                raise LeaseConflict("LEASE_NOT_FOUND")
            if current["project_id"] != self.binding.project_id:
                raise ProjectScopeError("Foreign lease")
            if current["holder_agent_instance_id"] != self.binding.agent_instance_id or current["lease_id"] != lease_id:
                raise ProjectScopeError("Lease holder mismatch")
            if current["version"] != expected_version:
                raise StaleWriteError("STALE_LEASE_RENEWAL")
            if _parse(current["expires_at"]) <= now:
                raise LeaseConflict("LEASE_EXPIRED")
            current["version"] += 1
            current["renewals"] += 1
            current["expires_at"] = (now + timedelta(seconds=ttl_seconds)).isoformat().replace("+00:00", "Z")
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            os.replace(tmp, path)
            return current

    def release(self, resource_id: str, *, lease_id: str):
        self.binding.assert_mutation_allowed()
        path = self._path(resource_id)
        with _resource_lock(path.with_suffix(".lock")):
            current = self._load(path)
            if not current:
                return False
            if current["holder_agent_instance_id"] != self.binding.agent_instance_id or current["lease_id"] != lease_id:
                raise ProjectScopeError("Lease release denied for non-holder")
            path.unlink()
            return True
