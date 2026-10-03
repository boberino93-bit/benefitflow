import pytest

from benefitflow_coordination.artifacts import ArtifactStore
from benefitflow_coordination.constants import (
    FRAMEWORK_VERSION, PACKAGE_VERSION, PROJECT_VERSION, PROTOCOL_VERSION,
    REPOSITORY_IDENTITY,
)
from benefitflow_coordination.identity import ProjectScopeError, make_primary_binding
from benefitflow_coordination.packages import validate_agent_package_manifest


def test_artifact_version_is_immutable(tmp_path):
    binding = make_primary_binding(tmp_path)
    store = ArtifactStore(tmp_path / "artifacts", binding)
    meta = {
        "artifact_id": "latest-analysis",
        "project_id": "benefitflow",
        "creator_agent_id": binding.agent_id,
        "task_id": "task-001",
        "artifact_type": "research",
        "version": 1,
        "source": "unit-test",
    }
    store.publish(meta, {"claim": "A"})
    with pytest.raises(FileExistsError):
        store.publish(meta, {"claim": "B"})


def test_foreign_artifact_write_denied(tmp_path):
    binding = make_primary_binding(tmp_path)
    store = ArtifactStore(tmp_path / "artifacts", binding)
    meta = {
        "artifact_id": "x", "project_id": "duo-open", "creator_agent_id": binding.agent_id,
        "task_id": "task", "artifact_type": "research", "version": 1, "source": "test",
    }
    with pytest.raises(ProjectScopeError):
        store.publish(meta, {})


def manifest(role="RESEARCH", project="benefitflow", protocol=PROTOCOL_VERSION):
    tiers = {"PRIMARY": "ORCHESTRATOR", "MANAGER": "REVIEWER", "RESEARCH": "SPECIALIST"}
    return {
        "schema": "benefitflow/agent-deployment-manifest/v2",
        "project_id": project,
        "repository_identity": REPOSITORY_IDENTITY,
        "deployment_role": role,
        "authority_tier": tiers[role],
        "project_version": PROJECT_VERSION,
        "framework_version": FRAMEWORK_VERSION,
        "protocol_version": protocol,
        "package_version": PACKAGE_VERSION,
        "source_revision": "abc123",
        "built_at": "2026-10-03T00:00:00Z",
        "included_components": ["BOOTSTRAP.md"],
        "component_hashes": {"BOOTSTRAP.md": "deadbeef"},
        "capabilities": [],
    }


def test_package_manifest_accepts_current_role():
    assert validate_agent_package_manifest(manifest())


def test_package_manifest_rejects_foreign_project():
    with pytest.raises(ProjectScopeError):
        validate_agent_package_manifest(manifest(project="duo-open"))


def test_package_manifest_rejects_stale_protocol():
    with pytest.raises(ValueError, match="Stale"):
        validate_agent_package_manifest(manifest(protocol="1.0.0"))
