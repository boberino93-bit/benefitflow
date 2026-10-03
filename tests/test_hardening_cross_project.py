from datetime import datetime, timedelta, timezone
import json
import pytest

from benefitflow_coordination.cross_project import CapabilityRegistry
from benefitflow_coordination.identity import ProjectScopeError, make_primary_binding


def z(dt):
    return dt.isoformat().replace("+00:00", "Z")


def test_cross_project_denied_without_trusted_grant(tmp_path):
    binding = make_primary_binding(tmp_path)
    registry = CapabilityRegistry(tmp_path / "grants", binding)
    now = datetime.now(timezone.utc)
    exchange = {
        "schema": "benefitflow/cross-project-exchange/v1",
        "exchange_id": "x-1",
        "source_project_id": "benefitflow",
        "destination_project_id": "intercommunicationsenhancements",
        "requesting_agent_instance_id": binding.agent_instance_id,
        "purpose": "share sanitized protocol finding",
        "data_classification": "INTERNAL_DESIGN",
        "requested_artifacts": ["protocol-note"],
        "allowed_use": "protocol-review",
        "created_at": z(now),
        "expires_at": z(now + timedelta(minutes=5)),
        "correlation_id": "benefitflow::corr-1",
        "capability_grant_id": "grant-1",
    }
    with pytest.raises(ProjectScopeError, match="not found"):
        registry.authorize(exchange)


def test_bounded_approved_grant_authorizes_only_declared_scope(tmp_path):
    binding = make_primary_binding(tmp_path)
    grants = tmp_path / "grants"
    grants.mkdir()
    now = datetime.now(timezone.utc)
    grant = {
        "schema": "benefitflow/capability-grant/v1",
        "grant_id": "grant-1",
        "subject_agent_instance_id": binding.agent_instance_id,
        "source_project_id": "benefitflow",
        "destination_project_id": "intercommunicationsenhancements",
        "capabilities": ["cross_project_exchange"],
        "artifact_scope": ["protocol-note"],
        "allowed_use": "protocol-review",
        "issued_at": z(now),
        "expires_at": z(now + timedelta(minutes=10)),
        "approval": {"status": "APPROVED", "approved_by": "human-owner"},
        "status": "ACTIVE",
    }
    (grants / "grant-1.json").write_text(json.dumps(grant))
    registry = CapabilityRegistry(grants, binding)
    exchange = {
        "schema": "benefitflow/cross-project-exchange/v1",
        "exchange_id": "x-1",
        "source_project_id": "benefitflow",
        "destination_project_id": "intercommunicationsenhancements",
        "requesting_agent_instance_id": binding.agent_instance_id,
        "purpose": "share sanitized protocol finding",
        "data_classification": "INTERNAL_DESIGN",
        "requested_artifacts": ["protocol-note"],
        "allowed_use": "protocol-review",
        "created_at": z(now),
        "expires_at": z(now + timedelta(minutes=5)),
        "correlation_id": "benefitflow::corr-1",
        "capability_grant_id": "grant-1",
    }
    assert registry.authorize(exchange)
    exchange["requested_artifacts"] = ["member-health-record"]
    with pytest.raises(ProjectScopeError, match="outside capability scope"):
        registry.authorize(exchange)
