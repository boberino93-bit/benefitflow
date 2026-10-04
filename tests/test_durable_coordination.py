from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from benefitflow_beta.coordination import AgentIdentity, AuthorizationError, ConflictError, ProjectMode
from benefitflow_beta.durable_coordination import DurableCoordinationStore


def primary(instance: str = "primary-i") -> AgentIdentity:
    return AgentIdentity("benefitflow", "primary", instance, "PRIMARY")


def manager(instance: str = "manager-i") -> AgentIdentity:
    return AgentIdentity("benefitflow", "manager", instance, "MANAGER")


def test_atomic_state_audit_outbox_and_retry_survive_restart(tmp_path):
    database = tmp_path / "coord.sqlite"
    store = DurableCoordinationStore(database)
    first = store.apply_state_mutation(actor=manager(),resource_id="task-1",expected_version=0,value={"status":"accepted"},correlation_id="corr-1",causation_id="human-1",idempotency_key="idem-1",outbox_topic="task.changed")
    restarted = DurableCoordinationStore(database)
    replay = restarted.apply_state_mutation(actor=manager("other-instance"),resource_id="task-1",expected_version=0,value={"status":"must-not-overwrite"},correlation_id="corr-1",causation_id="human-1",idempotency_key="idem-1",outbox_topic="task.changed")
    assert first["duplicate"] is False
    assert replay["duplicate"] is True
    assert restarted.read_state("task-1") == (1, {"status":"accepted"})
    assert len(restarted.audit_records()) == 1
    assert len(restarted.pending_outbox()) == 1
    assert restarted.verify_integrity()["valid"] is True


def test_stale_state_write_rolls_back_idempotency_and_audit(tmp_path):
    store = DurableCoordinationStore(tmp_path / "coord.sqlite")
    store.apply_state_mutation(actor=manager(),resource_id="state-1",expected_version=0,value=1,correlation_id="c1",causation_id="h1",idempotency_key="first")
    with pytest.raises(ConflictError):
        store.apply_state_mutation(actor=manager("m2"),resource_id="state-1",expected_version=0,value=2,correlation_id="c2",causation_id="h2",idempotency_key="stale")
    assert store.read_state("state-1") == (1, 1)
    assert len(store.audit_records()) == 1


def test_lease_is_instance_owned_and_recoverable_after_expiry(tmp_path):
    store = DurableCoordinationStore(tmp_path / "coord.sqlite")
    now = datetime(2026, 10, 4, tzinfo=timezone.utc)
    first = store.claim_lease(actor=manager("holder-a"),resource_id="task",ttl_seconds=5,correlation_id="c1",causation_id="h1",idempotency_key="claim-a",now=now)
    assert first["holder_instance_id"] == "holder-a"
    with pytest.raises(ConflictError):
        store.claim_lease(actor=manager("holder-b"),resource_id="task",ttl_seconds=5,correlation_id="c2",causation_id="h2",idempotency_key="claim-b-early",now=now+timedelta(seconds=1))
    recovered = store.claim_lease(actor=manager("holder-b"),resource_id="task",ttl_seconds=5,correlation_id="c3",causation_id="h3",idempotency_key="claim-b-late",now=now+timedelta(seconds=6))
    assert recovered["holder_instance_id"] == "holder-b"


def test_project_pause_is_durable_and_blocks_mutation(tmp_path):
    database = tmp_path / "coord.sqlite"; store = DurableCoordinationStore(database); mode, version = store.mode(); assert mode == ProjectMode.ACTIVE
    store.set_project_mode(requester=primary(),mode=ProjectMode.PAUSED,expected_version=version,human_approved=True,correlation_id="pause",causation_id="human",idempotency_key="pause-1")
    assert DurableCoordinationStore(database).mode()[0] == ProjectMode.PAUSED
    with pytest.raises(AuthorizationError):
        store.apply_state_mutation(actor=manager(),resource_id="blocked",expected_version=0,value=True,correlation_id="c",causation_id="h",idempotency_key="blocked")


def test_only_primary_with_human_approval_can_change_durable_mode(tmp_path):
    store = DurableCoordinationStore(tmp_path / "coord.sqlite"); _, version = store.mode()
    with pytest.raises(AuthorizationError):
        store.set_project_mode(requester=manager(),mode=ProjectMode.PAUSED,expected_version=version,human_approved=True,correlation_id="c",causation_id="h",idempotency_key="manager-pause")
    with pytest.raises(AuthorizationError):
        store.set_project_mode(requester=primary(),mode=ProjectMode.PAUSED,expected_version=version,human_approved=False,correlation_id="c",causation_id="h",idempotency_key="unapproved-pause")


def test_audit_and_outbox_are_append_only(tmp_path):
    database = tmp_path / "coord.sqlite"; store = DurableCoordinationStore(database)
    result = store.apply_state_mutation(actor=manager(),resource_id="x",expected_version=0,value={"x":1},correlation_id="c",causation_id="h",idempotency_key="append-only",outbox_topic="x.changed")
    conn = sqlite3.connect(database)
    try:
        with pytest.raises(sqlite3.IntegrityError): conn.execute("UPDATE audit_log SET outcome='tampered' WHERE project_id='benefitflow'")
        with pytest.raises(sqlite3.IntegrityError): conn.execute("DELETE FROM audit_log WHERE project_id='benefitflow'")
        with pytest.raises(sqlite3.IntegrityError): conn.execute("UPDATE outbox SET topic='tampered' WHERE project_id='benefitflow'")
    finally: conn.close()
    assert store.verify_integrity()["valid"] is True
    assert store.acknowledge_outbox(event_id=result["event_id"],consumer_id="consumer") is True
    assert store.acknowledge_outbox(event_id=result["event_id"],consumer_id="consumer") is False


def test_foreign_rows_cannot_collide_with_benefitflow_reads(tmp_path):
    database = tmp_path / "coord.sqlite"; store = DurableCoordinationStore(database)
    store.apply_state_mutation(actor=manager(),resource_id="same-id",expected_version=0,value={"project":"benefitflow"},correlation_id="c",causation_id="h",idempotency_key="same-key")
    conn = sqlite3.connect(database)
    try:
        conn.execute("INSERT INTO versioned_state(project_id,resource_id,version,value_json,updated_at) VALUES('project-c','same-id',99,'{\"project\":\"c\"}','2026-10-04T00:00:00+00:00')")
        conn.commit()
    finally: conn.close()
    assert store.read_state("same-id") == (1, {"project":"benefitflow"})
    assert store.foreign_row_counts()["versioned_state"] == 1


def test_outbox_delivery_receipt_does_not_mutate_original_event(tmp_path):
    store = DurableCoordinationStore(tmp_path / "coord.sqlite")
    result = store.apply_state_mutation(actor=manager(),resource_id="event",expected_version=0,value=1,correlation_id="c",causation_id="h",idempotency_key="outbox",outbox_topic="event.changed")
    pending = store.pending_outbox(); assert pending[0]["event_id"] == result["event_id"]
    assert store.acknowledge_outbox(event_id=result["event_id"],consumer_id="worker-1")
    assert store.pending_outbox() == []
    assert store.verify_integrity()["outbox_records"] == 1
