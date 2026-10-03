from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import os
import re

from .constants import PROJECT_ID, PROTOCOL_VERSION, MESSAGE_OUTCOMES
from .identity import ProjectBinding, ProjectScopeError, require_same_project


class DuplicateOperation(RuntimeError):
    pass


class MessageValidationError(ValueError):
    pass


REQUIRED_FIELDS = {
    "schema", "protocol_version", "message_id", "correlation_id", "causation_id",
    "idempotency_key", "sender", "destination", "task", "message_type", "sequence",
    "created_at", "expires_at", "priority", "capabilities_required", "artifact_refs",
    "payload", "integrity",
}


def canonical_payload_hash(payload) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(encoded).hexdigest()


def _parse_time(value: str | None):
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_message(message: dict, *, binding: ProjectBinding, now: datetime | None = None) -> bool:
    missing = sorted(REQUIRED_FIELDS - set(message))
    if missing:
        raise MessageValidationError(f"Message missing fields: {missing}")
    if message["protocol_version"] != PROTOCOL_VERSION:
        raise MessageValidationError("PROTOCOL_MISMATCH")
    if message["schema"] != "benefitflow/agentbus-message/v2":
        raise MessageValidationError("Unsupported message schema")

    sender = message["sender"]
    destination = message["destination"]
    task = message["task"]
    for obj, fields, label in [
        (sender, {"project_id", "agent_id", "agent_instance_id", "role"}, "sender"),
        (destination, {"project_id", "agent_id", "channel"}, "destination"),
        (task, {"project_id", "task_id", "parent_task_id"}, "task"),
    ]:
        missing_nested = fields - set(obj or {})
        if missing_nested:
            raise MessageValidationError(f"{label} missing fields: {sorted(missing_nested)}")

    binding.assert_mutation_allowed()
    require_same_project(binding.project_id, sender["project_id"], operation="message publication")
    if sender["agent_instance_id"] != binding.agent_instance_id:
        raise ProjectScopeError("Sender instance does not match bound execution identity")
    require_same_project(binding.project_id, destination["project_id"], operation="internal routing")
    require_same_project(binding.project_id, task["project_id"], operation="task routing")

    if binding.project_id != PROJECT_ID:
        raise ProjectScopeError("BenefitFlow message publisher is bound to a foreign project")

    if not isinstance(message["sequence"], int) or message["sequence"] < 0:
        raise MessageValidationError("sequence must be a non-negative integer")
    if message["priority"] not in {"normal", "high", "critical"}:
        raise MessageValidationError("Unsupported priority")
    if not isinstance(message["capabilities_required"], list):
        raise MessageValidationError("capabilities_required must be a list")
    if not isinstance(message["artifact_refs"], list):
        raise MessageValidationError("artifact_refs must be a list")
    for artifact in message["artifact_refs"]:
        if artifact.get("project_id") != binding.project_id:
            raise ProjectScopeError("Foreign artifact reference rejected on internal message bus")

    now = now or datetime.now(timezone.utc)
    created = _parse_time(message["created_at"])
    expires = _parse_time(message["expires_at"])
    if created is None or created.tzinfo is None:
        raise MessageValidationError("created_at must be timezone-aware")
    if expires is not None and expires.tzinfo is None:
        raise MessageValidationError("expires_at must be timezone-aware")
    if expires is not None and expires <= now:
        raise MessageValidationError("EXPIRED")

    integrity = message["integrity"] or {}
    if integrity.get("payload_hash") != canonical_payload_hash(message["payload"]):
        raise MessageValidationError("Payload hash mismatch")
    if not message["idempotency_key"]:
        raise MessageValidationError("idempotency_key is required")
    return True


def _safe(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value)).strip("-") or "record"


def _exclusive_write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            path.unlink(missing_ok=True)
        finally:
            raise


class ImmutableMessageStore:
    def __init__(self, root: str | Path, binding: ProjectBinding):
        self.root = binding.assert_path(root)
        self.binding = binding

    def publish(self, message: dict) -> Path:
        validate_message(message, binding=self.binding)
        idem_hash = sha256(message["idempotency_key"].encode("utf-8")).hexdigest()
        claim = self.root / ".idempotency" / self.binding.project_id / f"{idem_hash}.json"
        claim_payload = json.dumps({
            "project_id": self.binding.project_id,
            "idempotency_key": message["idempotency_key"],
            "message_id": message["message_id"],
        }, sort_keys=True) + "\n"
        try:
            _exclusive_write(claim, claim_payload)
        except FileExistsError as exc:
            raise DuplicateOperation("DUPLICATE") from exc

        path = self.root / self.binding.project_id / (
            f"{_safe(message['created_at'])}__{_safe(message['message_id'])}.json"
        )
        try:
            _exclusive_write(path, json.dumps(message, indent=2, sort_keys=True) + "\n")
        except Exception:
            claim.unlink(missing_ok=True)
            raise
        return path

    def quarantine(self, payload: dict, *, reason: str) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        message_id = payload.get("message_id", "unknown")
        path = self.root / "quarantine" / self.binding.project_id / f"{stamp}__{_safe(message_id)}.json"
        record = {
            "project_id": self.binding.project_id,
            "status": "QUARANTINED",
            "reason": reason,
            "payload": payload,
        }
        _exclusive_write(path, json.dumps(record, indent=2, sort_keys=True) + "\n")
        return path

    def acknowledge(self, *, message_id: str, status: str, detail: str = "") -> Path:
        if status not in MESSAGE_OUTCOMES:
            raise ValueError("Unsupported acknowledgement status")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        path = self.root / "acks" / self.binding.project_id / f"{stamp}__{_safe(message_id)}__{status}.json"
        record = {
            "project_id": self.binding.project_id,
            "message_id": message_id,
            "status": status,
            "agent_instance_id": self.binding.agent_instance_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "detail": detail,
        }
        _exclusive_write(path, json.dumps(record, indent=2, sort_keys=True) + "\n")
        return path
