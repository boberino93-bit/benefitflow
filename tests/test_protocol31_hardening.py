from datetime import datetime, timedelta, timezone
import threading
import pytest

from benefitflow_beta.project_guard import ProjectScopeError, WriteIntent, validate_write_intent

from benefitflow_beta.coordination import (
    AgentIdentity, AgentLifecycle, AgentSession, AuthorizationError, ConflictError,
    IdempotencyLedger, IdentityError, LeaseRegistry, LifecycleError, PROJECT_ID,
    PROTOCOL_VERSION, ProjectControl, ProjectMode, VersionedProjectState,
    accept_cross_project_import, build_cross_project_export,
    canonical_payload_hash, spawn_child, validate_message,
)

def message(*, sender_project="benefitflow", dest_project="benefitflow", task_project="benefitflow",
            channel="/project/benefitflow/status", artifact_refs=None, expires_delta=60):
    now = datetime(2026, 10, 3, 23, 30, tzinfo=timezone.utc)
    payload = {"work": "safe"}
    return {
        "protocol_version": PROTOCOL_VERSION,
        "message_id": "msg-benefitflow-0123456789abcdef",
        "correlation_id": "corr-benefitflow-0123456789",
        "causation_id": "human-0123456789",
        "idempotency_key": "idem-0123456789abcdef",
        "sender": {"project_id": sender_project, "agent_id": "manager-01", "agent_instance_id": "manager-01-instance-a", "role": "MANAGER"},
        "destination": {"project_id": dest_project, "agent_id": "primary", "channel": channel},
        "task": {"project_id": task_project, "task_id": "task-001", "parent_task_id": None},
        "message_type": "status", "sequence": 1,
        "created_at": now.isoformat(), "expires_at": (now + timedelta(seconds=expires_delta)).isoformat(),
        "priority": "normal", "capabilities_required": ["publish_message"],
        "artifact_refs": [] if artifact_refs is None else artifact_refs, "payload": payload,
        "integrity": {"payload_hash": canonical_payload_hash(payload)},
    }, now

def active_primary():
    s = AgentSession()
    s.mark_unbound()
    s.begin_project_resolution()
    s.bind(AgentIdentity(PROJECT_ID, "primary", "p-1", "PRIMARY"))
    s.initialize()
    s.activate()
    return s

def test_lifecycle_blocks_mutation_until_active():
    s = AgentSession()
    with pytest.raises(LifecycleError):
        s.assert_mutation_allowed()
    s.mark_unbound()
    s.begin_project_resolution()
    s.bind(AgentIdentity(PROJECT_ID, "manager", "m-1", "MANAGER"))
    with pytest.raises(LifecycleError):
        s.assert_mutation_allowed()
    s.initialize()
    s.activate()
    assert s.assert_mutation_allowed().project_id == PROJECT_ID

def test_child_inherits_parent_project_and_conflict_fails_closed():
    parent = active_primary()
    child = spawn_child(parent, agent_id="manager-01", agent_instance_id="m-1", role="MANAGER")
    assert child.state == AgentLifecycle.BOUND
    assert child.identity.project_id == PROJECT_ID
    assert child.parent_agent_instance_id == "p-1"
    with pytest.raises(IdentityError):
        spawn_child(parent, agent_id="manager-02", agent_instance_id="m-2", role="MANAGER", requested_project_id="duo-open")

def test_message_requires_project_owned_task_and_project_qualified_channel():
    msg, now = message()
    sender = AgentIdentity(PROJECT_ID, "manager-01", "manager-01-instance-a", "MANAGER")
    assert validate_message(msg, now=now, registered_sender=sender).outcome == "ACCEPTED"
    msg["task"]["project_id"] = "duo-open"
    assert validate_message(msg, now=now).outcome == "UNAUTHORIZED"
    msg, now = message(channel="/research")
    assert validate_message(msg, now=now).outcome == "UNAUTHORIZED"

def test_foreign_artifact_reference_is_denied():
    msg, now = message(artifact_refs=[{"project_id": "duo-open", "artifact_id": "latest-analysis"}])
    assert validate_message(msg, now=now).outcome == "UNAUTHORIZED"

def test_cross_project_bridge_is_primary_human_approved_copy_by_value():
    primary = active_primary().identity
    payload = {"finding": {"value": 1}}
    with pytest.raises(AuthorizationError):
        build_cross_project_export(primary, target_project_id="duo-open", payload=payload, provenance={"source": "local"}, human_approved=False)
    snapshot = build_cross_project_export(primary, target_project_id="duo-open", payload=payload, provenance={"source": "local"}, human_approved=True)
    payload["finding"]["value"] = 2
    assert snapshot["payload"]["finding"]["value"] == 1

def test_cross_project_import_rejects_wrong_target_and_requires_primary():
    primary = active_primary().identity
    foreign_snapshot = {
        "schema": "benefitflow/cross-project-export/v1",
        "protocol_version": PROTOCOL_VERSION,
        "source_project_id": "duo-open",
        "target_project_id": PROJECT_ID,
        "mode": "COPY_BY_VALUE",
        "provenance": {"source": "duo-open"},
        "payload": {"x": 1},
        "integrity": {"payload_hash": canonical_payload_hash({"x": 1})},
    }
    assert accept_cross_project_import(primary, foreign_snapshot, human_approved=True) == {"x": 1}
    manager = AgentIdentity(PROJECT_ID, "manager", "m-1", "MANAGER")
    with pytest.raises(AuthorizationError):
        accept_cross_project_import(manager, foreign_snapshot, human_approved=True)

def test_project_pause_and_degraded_mode_disable_mutation():
    primary = active_primary().identity
    control = ProjectControl()
    control.assert_mutation_allowed()
    control.set_mode(primary, ProjectMode.PAUSED, human_approved=True)
    with pytest.raises(AuthorizationError):
        control.assert_mutation_allowed()
    control.set_mode(primary, ProjectMode.ACTIVE, human_approved=True)
    control.assert_mutation_allowed()
    control.set_mode(primary, ProjectMode.DEGRADED_READ_ONLY, human_approved=True)
    with pytest.raises(AuthorizationError):
        control.assert_mutation_allowed()

def test_lease_renew_release_and_crash_cleanup_are_instance_scoped():
    leases = LeaseRegistry()
    now = datetime(2026, 10, 3, tzinfo=timezone.utc)
    leases.claim(project_id=PROJECT_ID, resource_id="task-1", holder_agent_instance_id="i-1", ttl_seconds=5, now=now)
    renewed = leases.renew(project_id=PROJECT_ID, resource_id="task-1", holder_agent_instance_id="i-1", ttl_seconds=10, now=now + timedelta(seconds=1))
    assert renewed[0] == "i-1"
    with pytest.raises(AuthorizationError):
        leases.release(project_id=PROJECT_ID, resource_id="task-1", holder_agent_instance_id="i-2")
    assert leases.expire_for_instance(project_id=PROJECT_ID, holder_agent_instance_id="i-1") == 1

def test_duplicate_command_has_one_effective_reservation_under_concurrency():
    ledger, results = IdempotencyLedger(), []
    barrier = threading.Barrier(8)
    def worker():
        barrier.wait()
        results.append(ledger.reserve_or_replay(PROJECT_ID, "same-command")[0])
    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads: thread.start()
    for thread in threads: thread.join()
    assert results.count(True) == 1
    assert results.count(False) == 7

def test_stale_version_cannot_overwrite_newer_state():
    state = VersionedProjectState()
    assert state.write(project_id=PROJECT_ID, resource_id="accepted-state", expected_version=0, value="a") == 1
    with pytest.raises(ConflictError):
        state.write(project_id=PROJECT_ID, resource_id="accepted-state", expected_version=0, value="stale")

def test_repository_binding_validates_stable_github_id():
    validate_write_intent(WriteIntent(
        project_id=PROJECT_ID,
        target_repository="boberino93-bit/benefitflow",
        target_repository_id=1403645790,
    ))
    with pytest.raises(ProjectScopeError):
        validate_write_intent(WriteIntent(
            project_id=PROJECT_ID,
            target_repository="boberino93-bit/benefitflow",
            target_repository_id=999,
        ))
