from __future__ import annotations

import hashlib
import json
import threading
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

PROJECT_ID = "benefitflow"
PROTOCOL_VERSION = "3.1.0"
PROJECT_VERSION = "alpha-0.4.1"
PACKAGE_VERSION = "0.4.1-h2"

ROLE_CAPABILITIES = {
    "PRIMARY": frozenset({
        "read_source", "write_source", "read_artifacts", "write_artifacts",
        "publish_message", "claim_task", "review_change", "approve_change",
        "build_package", "replace_package", "cross_project_exchange",
    }),
    "MANAGER": frozenset({
        "read_source", "read_artifacts", "write_artifacts", "publish_message",
        "claim_task", "review_change",
    }),
    "RESEARCH": frozenset({
        "read_source", "read_artifacts", "write_artifacts", "publish_message",
        "claim_task",
    }),
}
HUMAN_APPROVAL_CAPABILITIES = frozenset({
    "deploy", "external_action", "financial_action", "member_identifier_disclosure",
    "material_booking_term_change", "cross_project_exchange",
})

class CoordinationError(RuntimeError):
    pass

class IdentityError(CoordinationError):
    pass

class AuthorizationError(CoordinationError):
    pass

class ConflictError(CoordinationError):
    pass

class LifecycleError(CoordinationError):
    pass

class AgentLifecycle(str, Enum):
    CREATED = "CREATED"
    UNBOUND = "UNBOUND"
    PROJECT_RESOLUTION = "PROJECT_RESOLUTION"
    BOUND = "BOUND"
    INITIALIZED = "INITIALIZED"
    ACTIVE = "ACTIVE"
    DRAINING = "DRAINING"
    PAUSED = "PAUSED"
    TERMINATED = "TERMINATED"

class ProjectMode(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DEGRADED_READ_ONLY = "DEGRADED_READ_ONLY"

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
class TaskRef:
    project_id: str
    task_id: str
    parent_task_id: str | None = None

    def __post_init__(self) -> None:
        if self.project_id != PROJECT_ID:
            raise IdentityError("foreign task ownership")
        if not self.task_id:
            raise IdentityError("task identity required")

@dataclass(frozen=True)
class ArtifactRef:
    project_id: str
    artifact_id: str
    version: str | int | None = None
    provenance: str | None = None

    def __post_init__(self) -> None:
        if self.project_id != PROJECT_ID:
            raise IdentityError("foreign artifact ownership")
        if not self.artifact_id:
            raise IdentityError("artifact identity required")

@dataclass(frozen=True)
class ValidationResult:
    outcome: str
    reason: str

@dataclass
class AgentSession:
    state: AgentLifecycle = AgentLifecycle.CREATED
    identity: AgentIdentity | None = None
    parent_agent_instance_id: str | None = None

    def mark_unbound(self) -> None:
        self._require(AgentLifecycle.CREATED)
        self.state = AgentLifecycle.UNBOUND

    def begin_project_resolution(self) -> None:
        self._require(AgentLifecycle.UNBOUND)
        self.state = AgentLifecycle.PROJECT_RESOLUTION

    def bind(self, identity: AgentIdentity) -> None:
        self._require(AgentLifecycle.PROJECT_RESOLUTION)
        if identity.project_id != PROJECT_ID:
            raise IdentityError("foreign project identity")
        self.identity = identity
        self.state = AgentLifecycle.BOUND

    def initialize(self) -> None:
        self._require(AgentLifecycle.BOUND)
        self.state = AgentLifecycle.INITIALIZED

    def activate(self) -> None:
        self._require(AgentLifecycle.INITIALIZED, AgentLifecycle.PAUSED)
        self.state = AgentLifecycle.ACTIVE

    def pause(self) -> None:
        self._require(AgentLifecycle.ACTIVE, AgentLifecycle.DRAINING)
        self.state = AgentLifecycle.PAUSED

    def drain(self) -> None:
        self._require(AgentLifecycle.ACTIVE)
        self.state = AgentLifecycle.DRAINING

    def terminate(self) -> None:
        if self.state == AgentLifecycle.TERMINATED:
            return
        self.state = AgentLifecycle.TERMINATED

    def assert_mutation_allowed(self, target_project_id: str = PROJECT_ID) -> AgentIdentity:
        if self.state != AgentLifecycle.ACTIVE or self.identity is None:
            raise LifecycleError("agent must be ACTIVE and project-bound before mutation")
        if target_project_id != self.identity.project_id:
            raise AuthorizationError("cross-project mutation denied")
        return self.identity

    def _require(self, *states: AgentLifecycle) -> None:
        if self.state not in states:
            expected = ", ".join(s.value for s in states)
            raise LifecycleError(f"invalid lifecycle transition from {self.state.value}; expected {expected}")

def spawn_child(
    parent: AgentSession,
    *,
    agent_id: str,
    agent_instance_id: str,
    role: str,
    requested_project_id: str | None = None,
) -> AgentSession:
    parent_identity = parent.assert_mutation_allowed()
    if requested_project_id is not None and requested_project_id != parent_identity.project_id:
        raise IdentityError("child project conflicts with parent binding")
    child = AgentSession(parent_agent_instance_id=parent_identity.agent_instance_id)
    child.mark_unbound()
    child.begin_project_resolution()
    child.bind(AgentIdentity(parent_identity.project_id, agent_id, agent_instance_id, role))
    return child

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
    if not kind or not local_id or "/" in kind or local_id.startswith("/") or ".." in local_id.split("/"):
        raise ValueError("invalid namespace")
    return f"/project/{PROJECT_ID}/{kind}/{local_id}"

def authorize_capability(
    agent: AgentIdentity,
    capability: str,
    *,
    target_project_id: str = PROJECT_ID,
    human_approved: bool = False,
) -> None:
    if target_project_id != agent.project_id:
        raise AuthorizationError("cross-project operation denied")
    if capability in HUMAN_APPROVAL_CAPABILITIES:
        if capability == "cross_project_exchange" and capability not in agent.capabilities:
            raise AuthorizationError("role capability denied")
        if not human_approved:
            raise AuthorizationError("explicit human approval required")
        return
    if capability not in agent.capabilities:
        raise AuthorizationError("role capability denied")

def _validate_task(task: dict[str, Any]) -> ValidationResult | None:
    if not task.get("project_id") or not task.get("task_id"):
        return ValidationResult("REJECTED", "task project and identity required")
    if task["project_id"] != PROJECT_ID:
        return ValidationResult("UNAUTHORIZED", "foreign task ownership")
    return None

def _validate_artifacts(artifact_refs: Any) -> ValidationResult | None:
    if not isinstance(artifact_refs, list):
        return ValidationResult("REJECTED", "artifact_refs must be a list")
    for ref in artifact_refs:
        if not isinstance(ref, dict):
            return ValidationResult("REJECTED", "artifact reference must be structured")
        if not ref.get("project_id") or not ref.get("artifact_id"):
            return ValidationResult("REJECTED", "artifact project and identity required")
        if ref["project_id"] != PROJECT_ID:
            return ValidationResult("UNAUTHORIZED", "foreign artifact ownership")
    return None

def validate_message(
    envelope: dict[str, Any],
    *,
    now: datetime | None = None,
    registered_sender: AgentIdentity | None = None,
) -> ValidationResult:
    required = {
        "protocol_version", "message_id", "correlation_id", "causation_id",
        "idempotency_key", "sender", "destination", "task", "message_type",
        "sequence", "created_at", "expires_at", "priority",
        "capabilities_required", "artifact_refs", "payload", "integrity",
    }
    missing = sorted(required - envelope.keys())
    if missing:
        return ValidationResult("REJECTED", "missing: " + ", ".join(missing))
    if envelope["protocol_version"] != PROTOCOL_VERSION:
        return ValidationResult("PROTOCOL_MISMATCH", "unsupported protocol")

    sender, destination, task, integrity = (
        envelope["sender"], envelope["destination"], envelope["task"], envelope["integrity"]
    )
    if not all(isinstance(x, dict) for x in (sender, destination, task, integrity)):
        return ValidationResult("REJECTED", "invalid structured fields")
    if not all(sender.get(k) for k in ("project_id", "agent_id", "agent_instance_id", "role")):
        return ValidationResult("REJECTED", "incomplete sender identity")
    if not destination.get("project_id") or not destination.get("channel"):
        return ValidationResult("REJECTED", "incomplete destination identity")
    if sender["project_id"] != PROJECT_ID or destination["project_id"] != PROJECT_ID:
        return ValidationResult("UNAUTHORIZED", "ordinary cross-project routing denied")
    if not str(destination["channel"]).startswith(f"/project/{PROJECT_ID}/"):
        return ValidationResult("UNAUTHORIZED", "destination channel is not project-qualified")

    task_result = _validate_task(task)
    if task_result:
        return task_result
    artifact_result = _validate_artifacts(envelope["artifact_refs"])
    if artifact_result:
        return artifact_result

    capabilities = envelope["capabilities_required"]
    if not isinstance(capabilities, list) or not all(isinstance(v, str) and v for v in capabilities):
        return ValidationResult("REJECTED", "invalid capabilities")
    if not isinstance(envelope["sequence"], int) or envelope["sequence"] < 0:
        return ValidationResult("REJECTED", "invalid sequence")

    for field in ("message_id", "correlation_id", "causation_id", "idempotency_key", "message_type"):
        if not isinstance(envelope[field], str) or not envelope[field].strip():
            return ValidationResult("REJECTED", f"invalid {field}")

    if registered_sender is not None:
        claimed = (
            sender["project_id"], sender["agent_id"], sender["agent_instance_id"], str(sender["role"]).upper()
        )
        actual = (
            registered_sender.project_id, registered_sender.agent_id,
            registered_sender.agent_instance_id, registered_sender.role
        )
        if claimed != actual:
            return ValidationResult("UNAUTHORIZED", "sender/session mismatch")
        for capability in capabilities:
            try:
                authorize_capability(registered_sender, capability)
            except AuthorizationError:
                return ValidationResult("UNAUTHORIZED", "required capability denied")

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
        if not key:
            raise ValueError("idempotency key required")
        with self._lock:
            token = (project_id, key)
            if token in self._seen:
                return False, self._seen[token]
            self._seen[token] = result
            return True, result

    def complete(self, project_id: str, key: str, result: Any) -> None:
        if project_id != PROJECT_ID:
            raise AuthorizationError("foreign idempotency namespace")
        with self._lock:
            token = (project_id, key)
            if token not in self._seen:
                raise ConflictError("idempotency key was not reserved")
            self._seen[token] = result

class LeaseRegistry:
    def __init__(self) -> None:
        self._lock, self._leases = threading.Lock(), {}

    def claim(
        self, *, project_id: str, resource_id: str, holder_agent_instance_id: str,
        ttl_seconds: int, now: datetime | None = None
    ):
        if project_id != PROJECT_ID:
            raise AuthorizationError("foreign lease namespace")
        if ttl_seconds <= 0:
            raise ValueError("positive TTL required")
        if not resource_id or not holder_agent_instance_id:
            raise ValueError("resource and holder required")
        now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        key = (project_id, resource_id)
        with self._lock:
            current = self._leases.get(key)
            if current and current[1] > now and current[0] != holder_agent_instance_id:
                raise ConflictError("active lease exists")
            lease = (holder_agent_instance_id, now + timedelta(seconds=ttl_seconds))
            self._leases[key] = lease
            return lease

    def renew(
        self, *, project_id: str, resource_id: str, holder_agent_instance_id: str,
        ttl_seconds: int, now: datetime | None = None
    ):
        if ttl_seconds <= 0:
            raise ValueError("positive TTL required")
        now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        key = (project_id, resource_id)
        with self._lock:
            if project_id != PROJECT_ID:
                raise AuthorizationError("foreign lease namespace")
            current = self._leases.get(key)
            if not current or current[0] != holder_agent_instance_id or current[1] <= now:
                raise ConflictError("lease is missing, expired, or held by another instance")
            lease = (holder_agent_instance_id, now + timedelta(seconds=ttl_seconds))
            self._leases[key] = lease
            return lease

    def release(self, *, project_id: str, resource_id: str, holder_agent_instance_id: str) -> bool:
        if project_id != PROJECT_ID:
            raise AuthorizationError("foreign lease namespace")
        key = (project_id, resource_id)
        with self._lock:
            current = self._leases.get(key)
            if not current:
                return False
            if current[0] != holder_agent_instance_id:
                raise AuthorizationError("only the holder instance may release an active lease")
            del self._leases[key]
            return True

    def expire_for_instance(self, *, project_id: str, holder_agent_instance_id: str) -> int:
        if project_id != PROJECT_ID:
            raise AuthorizationError("foreign lease namespace")
        with self._lock:
            keys = [key for key, value in self._leases.items() if value[0] == holder_agent_instance_id]
            for key in keys:
                del self._leases[key]
            return len(keys)

class VersionedProjectState:
    def __init__(self) -> None:
        self._lock, self._state = threading.Lock(), {}

    def read(self, *, project_id: str, resource_id: str) -> tuple[int, Any]:
        if project_id != PROJECT_ID:
            raise AuthorizationError("foreign state read")
        with self._lock:
            return self._state.get((project_id, resource_id), (0, None))

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

class ProjectControl:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._mode = ProjectMode.ACTIVE

    @property
    def mode(self) -> ProjectMode:
        with self._lock:
            return self._mode

    def set_mode(self, requester: AgentIdentity, mode: ProjectMode, *, human_approved: bool) -> ProjectMode:
        if requester.role != "PRIMARY":
            raise AuthorizationError("only Primary may apply project control mode")
        if not human_approved:
            raise AuthorizationError("explicit human approval required for project control mode")
        with self._lock:
            self._mode = ProjectMode(mode)
            return self._mode

    def assert_mutation_allowed(self) -> None:
        with self._lock:
            if self._mode != ProjectMode.ACTIVE:
                raise AuthorizationError(f"project mutations disabled while mode={self._mode.value}")

def build_cross_project_export(
    requester: AgentIdentity,
    *,
    target_project_id: str,
    payload: Any,
    provenance: dict[str, Any],
    human_approved: bool,
) -> dict[str, Any]:
    if not target_project_id or target_project_id == PROJECT_ID:
        raise ValueError("foreign target project required")
    authorize_capability(requester, "cross_project_exchange", human_approved=human_approved)
    if not isinstance(provenance, dict) or not provenance:
        raise ValueError("provenance required")
    copied_payload = deepcopy(payload)
    return {
        "schema": "benefitflow/cross-project-export/v1",
        "protocol_version": PROTOCOL_VERSION,
        "source_project_id": PROJECT_ID,
        "target_project_id": target_project_id,
        "mode": "COPY_BY_VALUE",
        "provenance": deepcopy(provenance),
        "payload": copied_payload,
        "integrity": {"payload_hash": canonical_payload_hash(copied_payload)},
    }

def accept_cross_project_import(
    requester: AgentIdentity,
    snapshot: dict[str, Any],
    *,
    human_approved: bool,
) -> Any:
    if requester.role != "PRIMARY":
        raise AuthorizationError("only Primary may accept cross-project imports")
    if not human_approved:
        raise AuthorizationError("explicit human approval required for cross-project import")
    if snapshot.get("schema") != "benefitflow/cross-project-export/v1":
        raise AuthorizationError("unsupported cross-project bridge schema")
    if snapshot.get("mode") != "COPY_BY_VALUE":
        raise AuthorizationError("shared mutable cross-project state is prohibited")
    if snapshot.get("target_project_id") != PROJECT_ID:
        raise AuthorizationError("cross-project import targets another project")
    if snapshot.get("source_project_id") in (None, "", PROJECT_ID):
        raise AuthorizationError("foreign source project required")
    if not isinstance(snapshot.get("provenance"), dict) or not snapshot["provenance"]:
        raise AuthorizationError("provenance required")
    if snapshot.get("integrity", {}).get("payload_hash") != canonical_payload_hash(snapshot.get("payload")):
        raise AuthorizationError("cross-project payload integrity failure")
    return deepcopy(snapshot["payload"])
