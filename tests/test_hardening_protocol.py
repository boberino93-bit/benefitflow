from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
import copy
import json
import pytest

from benefitflow_coordination.identity import make_primary_binding, ProjectScopeError
from benefitflow_coordination.protocol import (
    DuplicateOperation, ImmutableMessageStore, MessageValidationError,
    canonical_payload_hash, validate_message,
)


def message_for(binding, *, key="idem-1", message_id="msg-1", destination_project="benefitflow", expires=None):
    now = datetime.now(timezone.utc)
    payload = {"finding": "example"}
    return {
        "schema": "benefitflow/agentbus-message/v2",
        "protocol_version": "2.0.0-alpha.1",
        "message_id": message_id,
        "correlation_id": "benefitflow::corr-1",
        "causation_id": None,
        "idempotency_key": key,
        "sender": {
            "project_id": "benefitflow",
            "agent_id": binding.agent_id,
            "agent_instance_id": binding.agent_instance_id,
            "role": "PRIMARY",
        },
        "destination": {
            "project_id": destination_project,
            "agent_id": "manager-01",
            "channel": "/project/benefitflow/review",
        },
        "task": {"project_id": "benefitflow", "task_id": "task-001", "parent_task_id": None},
        "message_type": "FINDING",
        "sequence": 1,
        "created_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": (expires or (now + timedelta(minutes=5))).isoformat().replace("+00:00", "Z"),
        "priority": "normal",
        "capabilities_required": [],
        "artifact_refs": [],
        "payload": payload,
        "integrity": {"payload_hash": canonical_payload_hash(payload)},
    }


def test_valid_internal_message(tmp_path):
    binding = make_primary_binding(tmp_path)
    assert validate_message(message_for(binding), binding=binding)


def test_cross_project_internal_routing_rejected(tmp_path):
    binding = make_primary_binding(tmp_path)
    with pytest.raises(ProjectScopeError):
        validate_message(message_for(binding, destination_project="duo-open"), binding=binding)


def test_expired_command_rejected(tmp_path):
    binding = make_primary_binding(tmp_path)
    expired = datetime.now(timezone.utc) - timedelta(seconds=1)
    with pytest.raises(MessageValidationError, match="EXPIRED"):
        validate_message(message_for(binding, expires=expired), binding=binding)


def test_foreign_artifact_reference_rejected(tmp_path):
    binding = make_primary_binding(tmp_path)
    msg = message_for(binding)
    msg["artifact_refs"] = [{"project_id": "duo-open", "artifact_id": "latest-analysis"}]
    with pytest.raises(ProjectScopeError):
        validate_message(msg, binding=binding)


def test_payload_tamper_rejected(tmp_path):
    binding = make_primary_binding(tmp_path)
    msg = message_for(binding)
    msg["payload"]["finding"] = "tampered"
    with pytest.raises(MessageValidationError, match="hash"):
        validate_message(msg, binding=binding)


def test_duplicate_command_has_single_effective_publication(tmp_path):
    binding = make_primary_binding(tmp_path)
    store = ImmutableMessageStore(tmp_path / "messages", binding)
    base = message_for(binding, key="same-key", message_id="msg-first")
    paths = []
    errors = []

    def publish(i):
        msg = copy.deepcopy(base)
        msg["message_id"] = f"msg-{i}"
        try:
            paths.append(store.publish(msg))
        except DuplicateOperation as exc:
            errors.append(str(exc))

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(publish, range(8)))

    assert len(paths) == 1
    assert len(errors) == 7
    saved = list((tmp_path / "messages" / "benefitflow").glob("*.json"))
    assert len(saved) == 1


def test_quarantine_preserves_unsafe_payload(tmp_path):
    binding = make_primary_binding(tmp_path)
    store = ImmutableMessageStore(tmp_path / "messages", binding)
    path = store.quarantine({"message_id": "bad-1", "project_id": None}, reason="missing project identity")
    record = json.loads(path.read_text())
    assert record["status"] == "QUARANTINED"
    assert record["payload"]["message_id"] == "bad-1"
