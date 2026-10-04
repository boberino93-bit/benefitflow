from datetime import datetime, timedelta, timezone
import threading
import pytest

from benefitflow_beta.coordination import (
    AgentIdentity, AuthorizationError, ConflictError, IdempotencyLedger,
    LeaseRegistry, PROTOCOL_VERSION, VersionedProjectState,
    authorize_capability, canonical_payload_hash, namespace, validate_message,
)


def message(*, sender_project="benefitflow", dest_project="benefitflow", task_project="benefitflow", expires_delta=60):
    now = datetime(2026, 10, 3, 23, 30, tzinfo=timezone.utc)
    payload = {"work": "safe"}
    return {
        "protocol_version": PROTOCOL_VERSION,
        "message_id": "msg-benefitflow-0123456789abcdef",
        "correlation_id": "corr-benefitflow-0123456789",
        "causation_id": "human-0123456789",
        "idempotency_key": "idem-0123456789abcdef",
        "sender": {"project_id": sender_project, "agent_id": "manager-01", "agent_instance_id": "manager-01-instance-a", "role": "MANAGER"},
        "destination": {"project_id": dest_project, "agent_id": "primary", "channel": "/project/benefitflow/status"},
        "task": {"project_id": task_project, "task_id": "task-001", "parent_task_id": None},
        "message_type": "status", "sequence": 1,
        "created_at": now.isoformat(), "expires_at": (now + timedelta(seconds=expires_delta)).isoformat(),
        "priority": "normal", "capabilities_required": ["publish_message"],
        "artifact_refs": [], "payload": payload,
        "integrity": {"payload_hash": canonical_payload_hash(payload)},
    }, now


def test_agent_binding_rejects_foreign_project():
    with pytest.raises(Exception):
        AgentIdentity("duo-open", "manager-01", "i-1", "MANAGER")


def test_same_human_names_remain_project_qualified():
    assert namespace("tasks", "task-001") == "/project/benefitflow/tasks/task-001"
    with pytest.raises(Exception):
        namespace("tasks", "task-001", project_id="duo-open")


def test_message_accepts_registered_sender():
    msg, now = message()
    sender = AgentIdentity("benefitflow", "manager-01", "manager-01-instance-a", "MANAGER")
    assert validate_message(msg, now=now, registered_sender=sender).outcome == "ACCEPTED"


@pytest.mark.parametrize("sender_project,dest_project", [("duo-open", "benefitflow"), ("benefitflow", "duo-open")])
def test_ordinary_cross_project_message_is_denied(sender_project, dest_project):
    msg, now = message(sender_project=sender_project, dest_project=dest_project)
    assert validate_message(msg, now=now).outcome == "UNAUTHORIZED"


def test_foreign_task_project_is_denied():
    msg, now = message(task_project="duo-open")
    assert validate_message(msg, now=now).outcome == "UNAUTHORIZED"


def test_caller_spoof_is_denied():
    msg, now = message()
    registered = AgentIdentity("benefitflow", "manager-02", "different-instance", "MANAGER")
    assert validate_message(msg, now=now, registered_sender=registered).outcome == "UNAUTHORIZED"


def test_missing_project_identity_is_rejected():
    msg, now = message()
    del msg["sender"]["project_id"]
    assert validate_message(msg, now=now).outcome == "REJECTED"


def test_expired_message_does_not_execute():
    msg, now = message(expires_delta=1)
    assert validate_message(msg, now=now + timedelta(seconds=2)).outcome == "EXPIRED"


def test_tampered_payload_is_quarantined():
    msg, now = message()
    msg["payload"]["work"] = "tampered"
    assert validate_message(msg, now=now).outcome == "QUARANTINED"


def test_protocol_mismatch_is_rejected():
    msg, now = message()
    msg["protocol_version"] = "2.0"
    assert validate_message(msg, now=now).outcome == "PROTOCOL_MISMATCH"


def test_human_approval_boundary_remains_fail_closed():
    agent = AgentIdentity("benefitflow", "primary", "primary-i", "PRIMARY")
    with pytest.raises(AuthorizationError):
        authorize_capability(agent, "financial_action")
    authorize_capability(agent, "financial_action", human_approved=True)


def test_research_role_cannot_approve_changes():
    research = AgentIdentity("benefitflow", "researcher-01", "r-1", "RESEARCH")
    with pytest.raises(AuthorizationError):
        authorize_capability(research, "approve_change")


def test_duplicate_command_has_one_effective_reservation_under_concurrency():
    ledger, results = IdempotencyLedger(), []
    barrier = threading.Barrier(8)
    def worker():
        barrier.wait()
        results.append(ledger.reserve_or_replay("benefitflow", "same-command")[0])
    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads: thread.start()
    for thread in threads: thread.join()
    assert results.count(True) == 1
    assert results.count(False) == 7


def test_lease_blocks_other_holder_and_recovers_after_expiry():
    registry = LeaseRegistry()
    now = datetime(2026, 10, 3, tzinfo=timezone.utc)
    registry.claim(project_id="benefitflow", resource_id="task-001", holder_agent_instance_id="a", ttl_seconds=5, now=now)
    with pytest.raises(ConflictError):
        registry.claim(project_id="benefitflow", resource_id="task-001", holder_agent_instance_id="b", ttl_seconds=5, now=now)
    recovered = registry.claim(project_id="benefitflow", resource_id="task-001", holder_agent_instance_id="b", ttl_seconds=5, now=now + timedelta(seconds=6))
    assert recovered[0] == "b"


def test_stale_version_cannot_overwrite_newer_state():
    state = VersionedProjectState()
    assert state.write(project_id="benefitflow", resource_id="accepted-state", expected_version=0, value="a") == 1
    with pytest.raises(ConflictError):
        state.write(project_id="benefitflow", resource_id="accepted-state", expected_version=0, value="stale")


def test_foreign_state_and_lease_mutations_are_denied():
    state, leases = VersionedProjectState(), LeaseRegistry()
    with pytest.raises(AuthorizationError):
        state.write(project_id="duo-open", resource_id="x", expected_version=0, value=1)
    with pytest.raises(AuthorizationError):
        leases.claim(project_id="duo-open", resource_id="x", holder_agent_instance_id="a", ttl_seconds=5)
