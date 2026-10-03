from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

PROJECT_ID = "benefitflow"
PROTOCOL_VERSION = "3.0.0"
PROJECT_VERSION = "alpha-0.4.0"
PACKAGE_VERSION = "0.4.0-h1"

ROLE_CAPABILITIES = {
    "PRIMARY": frozenset({"read_source", "write_source", "read_artifacts", "write_artifacts", "publish_message", "claim_task", "review_change", "approve_change", "build_package", "replace_package"}),
    "MANAGER": frozenset({"read_source", "read_artifacts", "write_artifacts", "publish_message", "claim_task", "review_change"}),
    "RESEARCH": frozenset({"read_source", "read_artifacts", "write_artifacts", "publish_message", "claim_task"}),
}
HUMAN_APPROVAL_CAPABILITIES = frozenset({"deploy", "external_action", "financial_action", "member_identifier_disclosure", "material_booking_term_change"})

class CoordinationError(RuntimeError): pass
class IdentityError(CoordinationError): pass
class AuthorizationError(CoordinationError): pass
class ConflictError(CoordinationError): pass

@dataclass(frozen=True)
class AgentIdentity:
    project_id: str
    agent_id: str
    agent_instance_id: str
    role: str

    def __post_init__(self) -> None:
        if self.project_id != PROJECT_ID:
            raise IdentityError("foreign project identity")
        if not self.agent_id or not self.agent_instance_id:
            raise IdentityError("agent and instance identity required")
        role = self.role.upper()
        if role not in ROLE_CAPABILITIES:
            raise IdentityError("unsupported role")
        object.__setattr__(self, "role", role)

    @property
    def capabilities(self) -> frozenset[str]:
        return ROLE_CAPABILITIES[self.role]

@dataclass(frozen=True)
class ValidationResult:
    outcome: str
    reason: str


def canonical_payload_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _utc(value: str) -> datetime:
    value = value[:-1] + "+00:00" if value.endswith("Z") else value
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError("timezone required")
    return result.astimezone(timezone.utc)


def namespace(kind: str, local_id: str, project_id: str = PROJECT_ID) -> str:
    if project_id != PROJECT_ID:
        raise IdentityError("foreign namespace denied")
    if not kind or not local_id or "/" in kind or local_id.startswith("/"):
        raise ValueError("invalid namespace")
    return f"/project/{PROJECT_ID}/{kind}/{local_id}"


def authorize_capability(agent: AgentIdentity, capability: str, *, target_project_id: str = PROJECT_ID, human_approved: bool = False) -> None:
    if target_project_id != agent.project_id:
        raise AuthorizationError("cross-project operation denied")
    if capability in HUMAN_APPROVAL_CAPABILITIES:
        if not human_approved:
            raise AuthorizationError("explicit human approval required")
        return
    if capability not in agent.capabilities:
        raise AuthorizationError("role capability denied")


def validate_message(envelope: dict[str, Any], *, now: datetime | None = None, registered_sender: AgentIdentity | None = None) -> ValidationResult:
    required = {"protocol_version", "message_id", "correlation_id", "causation_id", "idempotency_key", "sender", "destination", "task", "message_type", "sequence", "created_at", "expires_at", "priority", "capabilities_required", "artifact_refs", "payload", "integrity"}
    missing = sorted(required - envelope.keys())
    if missing:
        return ValidationResult("REJECTED", "missing: " + ", ".join(missing))
    if envelope["protocol_version"] != PROTOCOL_VERSION:
        return ValidationResult("PROTOCOL_MISMATCH", "unsupported protocol")
    sender, destination, task, integrity = envelope["sender"], envelope["destination"], envelope["task"], envelope["integrity"]
    if not all(isinstance(x, dict) for x in (sender, destination, task, integrity)):
        return ValidationResult("REJECTED", "invalid structured fields")
    if not all(sender.get(k) for k in ("project_id", "agent_id", "agent_instance_id", "role")):
        return ValidationResult("REJECTED", "incomplete sender identity")
    if not destination.get("project_id") or not destination.get("channel"):
        return ValidationResult("REJECTED", "incomplete destination identity")
    if sender["project_id"] != PROJECT_ID or destination["project_id"] != PROJECT_ID:
        return ValidationResult("UNAUTHORIZED", "ordinary cross-project routing denied")
    if registered_sender is not None:
        claimed = (sender["project_id"], sender["agent_id"], sender["agent_instance_id"], str(sender["role"]).upper())
        actual = (registered_sender.project_id, registered_sender.agent_id, registered_sender.agent_instance_id, registered_sender.role)
        if claimed != actual:
            return ValidationResult("UNAUTHORIZED", "sender/session mismatch")
        for capability in envelope["capabilities_required"]:
            try:
                authorize_capability(registered_sender, str(capability))
            except AuthorizationError:
                return ValidationResult("UNAUTHORIZED", "required capability denied")
    if not isinstance(envelope["capabilities_required"], list) or not isinstance(envelope["sequence"], int) or envelope["sequence"] < 0:
        return ValidationResult("REJECTED", "invalid capabilities or sequence")
    if not task.get("task_id"):
        return ValidationResult("REJECTED", "task identity required")
    try:
        created, expires = _utc(str(envelope["created_at"])), _utc(str(envelope["expires_at"]))
    except (TypeError, ValueError):
        return ValidationResult("REJECTED", "invalid timestamp")
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if expires <= created:
        return ValidationResult("REJECTED", "invalid TTL")
    if now > expires:
        return ValidationResult("EXPIRED", "message expired")
    if created > now + timedelta(minutes=5):
        return ValidationResult("REJECTED", "future timestamp")
    if integrity.get("payload_hash") != canonical_payload_hash(envelope["payload"]):
        return ValidationResult("QUARANTINED", "payload hash mismatch")
    return ValidationResult("ACCEPTED", "message accepted")


class IdempotencyLedger:
    def __init__(self) -> None:
        self._lock, self._seen = threading.Lock(), {}

    def reserve_or_replay(self, project_id: str, key: str, result: Any = None) -> tuple[bool, Any]:
        if project_id != PROJECT_ID:
            raise AuthorizationError("foreign idempotency namespace")
        with self._lock:
            token = (project_id, key)
            if token in self._seen:
                return False, self._seen[token]
            self._seen[token] = result
            return True, result


class LeaseRegistry:
    def __init__(self) -> None:
        self._lock, self._leases = threading.Lock(), {}

    def claim(self, *, project_id: str, resource_id: str, holder_agent_instance_id: str, ttl_seconds: int, now: datetime | None = None):
        if project_id != PROJECT_ID:
            raise AuthorizationError("foreign lease namespace")
        if ttl_seconds <= 0:
            raise ValueError("positive TTL required")
        now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        key = (project_id, resource_id)
        with self._lock:
            current = self._leases.get(key)
            if current and current[1] > now and current[0] != holder_agent_instance_id:
                raise ConflictError("active lease exists")
            lease = (holder_agent_instance_id, now + timedelta(seconds=ttl_seconds))
            self._leases[key] = lease
            return lease


class VersionedProjectState:
    def __init__(self) -> None:
        self._lock, self._state = threading.Lock(), {}

    def write(self, *, project_id: str, resource_id: str, expected_version: int, value: Any) -> int:
        if project_id != PROJECT_ID:
            raise AuthorizationError("foreign state mutation")
        key = (project_id, resource_id)
        with self._lock:
            current = self._state.get(key, (0, None))[0]
            if expected_version != current:
                raise ConflictError("stale write")
            self._state[key] = (current + 1, value)
            return current + 1
