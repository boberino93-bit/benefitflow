import json
from pathlib import Path

import pytest

from benefitflow_beta.project_guard import (
    MutationAuthority,
    MutationAuthorizationRequired,
    ProjectIntentRequired,
    ProjectScopeError,
    WriteIntent,
    authorize_project_write,
    authorize_recovery_write,
    resolve_human_project_intent,
    validate_write_intent,
)

ROOT = Path(__file__).resolve().parents[1]


def local_authority(**overrides):
    values = {
        "project_id": "benefitflow",
        "human_authorized": True,
    }
    values.update(overrides)
    return MutationAuthority(**values)


def test_accepts_local_non_repo_write_shape():
    validate_write_intent(WriteIntent(project_id="benefitflow", target_path="BenefitFlow-AgentBus/forum/messages/new.json"))


def test_rejects_duo_project_id():
    with pytest.raises(ProjectScopeError):
        validate_write_intent(WriteIntent(project_id="duo-open", target_path="DuoOpen-AgentBus/messages/x.json"))


def test_rejects_foreign_agentbus():
    with pytest.raises(ProjectScopeError):
        validate_write_intent(WriteIntent(project_id="benefitflow", target_path="DuoOpen-AgentBus/messages/x.json"))


def test_exact_benefitflow_repository_is_accepted_as_target_shape():
    validate_write_intent(WriteIntent(project_id="benefitflow", target_repository="boberino93-bit/benefitflow"))


def test_duo_repository_is_never_accepted():
    with pytest.raises(ProjectScopeError):
        validate_write_intent(WriteIntent(project_id="benefitflow", target_repository="boberino93-bit/duo-open"))


def test_local_repo_mutation_requires_current_human_authority():
    intent = WriteIntent(project_id="benefitflow", target_repository="boberino93-bit/benefitflow")
    with pytest.raises(MutationAuthorizationRequired):
        authorize_project_write("benefitflow", intent, None)
    with pytest.raises(MutationAuthorizationRequired):
        authorize_project_write("benefitflow", intent, local_authority(human_authorized=False))


def test_current_human_directive_plus_project_binding_authorizes_local_repo_mutation():
    authorize_project_write(
        "benefitflow",
        WriteIntent(
            project_id="benefitflow",
            target_repository="boberino93-bit/benefitflow",
            target_repository_id=1403645790,
            target_path="AGENT_BOOTSTRAP.md",
        ),
        local_authority(),
    )


def test_local_authority_never_expands_to_cross_project_swarm_or_transaction_actions():
    authority = local_authority()
    for intent in (
        WriteIntent(project_id="benefitflow", target_repository="boberino93-bit/benefitflow", cross_project=True),
        WriteIntent(project_id="benefitflow", target_repository="boberino93-bit/benefitflow", swarm_global=True),
        WriteIntent(project_id="benefitflow", protected_external_action=True),
    ):
        with pytest.raises(ProjectScopeError):
            authorize_project_write("benefitflow", intent, authority)


def test_revision_bound_authority_fails_closed_on_head_drift():
    authority = local_authority(expected_repository_head="abc123")
    intent = WriteIntent(project_id="benefitflow", target_repository="boberino93-bit/benefitflow")
    authorize_project_write("benefitflow", intent, authority, current_repository_head="abc123")
    with pytest.raises(MutationAuthorizationRequired):
        authorize_project_write("benefitflow", intent, authority, current_repository_head="def456")
    with pytest.raises(MutationAuthorizationRequired):
        authorize_project_write("benefitflow", intent, authority)


def test_wrong_authority_source_or_scope_is_rejected():
    intent = WriteIntent(project_id="benefitflow", target_repository="boberino93-bit/benefitflow")
    with pytest.raises(MutationAuthorizationRequired):
        authorize_project_write("benefitflow", intent, local_authority(source="PRIOR_SESSION"))
    with pytest.raises(MutationAuthorizationRequired):
        authorize_project_write("benefitflow", intent, local_authority(scope="SWARM_GLOBAL"))


def test_stale_other_project_context_cannot_override_current_human_intent():
    # Simulate the incident: recent context points to another project and may
    # even contain a newer handoff. It is evidence only, never project authority.
    recent_context_project = "duo-open"
    recent_handoff_sequence = 999999
    assert recent_context_project != "benefitflow"
    assert recent_handoff_sequence > 0

    assert resolve_human_project_intent("benefitflow") == "benefitflow"
    authorize_recovery_write(
        "benefitflow",
        WriteIntent(
            project_id="benefitflow",
            target_repository="boberino93-bit/benefitflow",
            target_path="BenefitFlow-AgentBus/artifactory/primary/recovery-checkpoint.json",
        ),
        local_authority(),
    )

    with pytest.raises(ProjectScopeError):
        authorize_recovery_write(
            "benefitflow",
            WriteIntent(project_id="duo-open", target_repository="boberino93-bit/duo-open"),
            local_authority(),
        )


def test_ambiguous_human_intent_fails_closed_and_writes_nowhere():
    with pytest.raises(ProjectIntentRequired):
        resolve_human_project_intent(None)
    with pytest.raises(ProjectIntentRequired):
        authorize_recovery_write(
            None,
            WriteIntent(project_id="benefitflow", target_repository="boberino93-bit/benefitflow"),
            local_authority(),
        )


def test_machine_identity_lock_and_discovery_order_are_consistent():
    lock = json.loads((ROOT / "BenefitFlow-AgentBus/control/PROJECT_IDENTITY_LOCK.json").read_text(encoding="utf-8"))
    discovery = json.loads((ROOT / "BenefitFlow-AgentBus/discovery/AGENT_DISCOVERY.json").read_text(encoding="utf-8"))

    assert lock["project_id"] == "benefitflow"
    assert lock["writable_repository"] == "boberino93-bit/benefitflow"
    assert lock["coordination_root"] == "BenefitFlow-AgentBus/"
    assert lock["mode"] == "FAIL_CLOSED"
    assert lock["cross_project_write_policy"] == "DENY"
    assert discovery["bootstrap_order"][:2] == [
        "../PROJECT_SCOPE_SELECTION_GATE_V1.md",
        "../control/PROJECT_IDENTITY_LOCK.json",
    ]
