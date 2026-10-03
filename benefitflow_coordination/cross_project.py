from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import re

from .identity import ProjectBinding, ProjectScopeError


REQUIRED_EXCHANGE_FIELDS = {
    "schema", "exchange_id", "source_project_id", "destination_project_id", "requesting_agent_instance_id",
    "purpose", "data_classification", "requested_artifacts", "allowed_use", "created_at", "expires_at",
    "correlation_id", "capability_grant_id",
}

REQUIRED_GRANT_FIELDS = {
    "schema", "grant_id", "subject_agent_instance_id", "source_project_id", "destination_project_id",
    "capabilities", "artifact_scope", "allowed_use", "issued_at", "expires_at", "approval", "status",
}


def _safe(value):
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value)).strip("-")


def _parse(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class CapabilityRegistry:
    """Loads grants only from a project-owned control directory.

    A caller cannot authorize itself by passing an arbitrary in-memory grant.
    """
    def __init__(self, root: str | Path, binding: ProjectBinding):
        self.root = binding.assert_path(root)
        self.binding = binding

    def _load(self, grant_id: str):
        path = self.root / f"{_safe(grant_id)}.json"
        if not path.exists():
            raise ProjectScopeError("Cross-project capability grant not found")
        grant = json.loads(path.read_text(encoding="utf-8"))
        missing = REQUIRED_GRANT_FIELDS - set(grant)
        if missing:
            raise ProjectScopeError(f"Invalid capability grant: missing {sorted(missing)}")
        return grant

    def authorize(self, exchange: dict, *, now=None):
        missing = REQUIRED_EXCHANGE_FIELDS - set(exchange)
        if missing:
            raise ProjectScopeError(f"Invalid exchange request: missing {sorted(missing)}")
        if exchange["source_project_id"] == exchange["destination_project_id"]:
            raise ProjectScopeError("Cross-project exchange requires distinct projects")
        if exchange["source_project_id"] != self.binding.project_id:
            raise ProjectScopeError("Source project does not match bound agent")
        if exchange["requesting_agent_instance_id"] != self.binding.agent_instance_id:
            raise ProjectScopeError("Requesting instance does not match bound execution identity")

        grant = self._load(exchange["capability_grant_id"])
        if grant["grant_id"] != exchange["capability_grant_id"]:
            raise ProjectScopeError("Capability grant identity mismatch")
        if grant["status"] != "ACTIVE":
            raise ProjectScopeError("Capability grant is not active")
        if "cross_project_exchange" not in grant["capabilities"]:
            raise ProjectScopeError("Capability does not permit cross-project exchange")
        if grant["subject_agent_instance_id"] != self.binding.agent_instance_id:
            raise ProjectScopeError("Capability subject mismatch")
        if grant["source_project_id"] != exchange["source_project_id"]:
            raise ProjectScopeError("Capability source mismatch")
        if grant["destination_project_id"] != exchange["destination_project_id"]:
            raise ProjectScopeError("Capability destination mismatch")
        if grant["allowed_use"] != exchange["allowed_use"]:
            raise ProjectScopeError("Capability allowed_use mismatch")
        if grant["approval"].get("status") != "APPROVED" or not grant["approval"].get("approved_by"):
            raise ProjectScopeError("Cross-project exchange lacks explicit approval")
        allowed_artifacts = set(grant["artifact_scope"])
        if any(item not in allowed_artifacts for item in exchange["requested_artifacts"]):
            raise ProjectScopeError("Requested artifact is outside capability scope")

        now = now or datetime.now(timezone.utc)
        if _parse(grant["expires_at"]) <= now or _parse(exchange["expires_at"]) <= now:
            raise ProjectScopeError("Cross-project exchange capability/request expired")
        return True
