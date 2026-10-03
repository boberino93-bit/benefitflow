import json
from pathlib import Path

import pytest

from benefitflow_beta.project_guard import (
    ProjectIntentRequired,
    ProjectScopeError,
    WriteIntent,
    authorize_recovery_write,
    resolve_human_project_intent,
    validate_write_intent,
)

ROOT = Path(__file__).resolve().parents[1]


def test_accepts_local_non_repo_write():
    validate_write_intent(WriteIntent(project_id="benefitflow", target_path="BenefitFlow-AgentBus/forum/messages/new.json"))


def test_rejects_duo_project_id():
    with pytest.raises(ProjectScopeError):
        validate_write_intent(WriteIntent(project_id="duo-open", target_path="DuoOpen-AgentBus/messages/x.json"))


def test_rejects_foreign_agentbus():
    with pytest.raises(ProjectScopeError):
        validate_write_intent(WriteIntent(project_id="benefitflow", target_path="DuoOpen-AgentBus/messages/x.json"))


def test_exact_benefitflow_repository_is_accepted():
    validate_write_intent(WriteIntent(project_id="benefitflow", target_repository="boberino93-bit/benefitflow"))


def test_duo_repository_is_never_accepted():
    with pytest.raises(ProjectScopeError):
        validate_write_intent(WriteIntent(project_id="benefitflow", target_repository="boberino93-bit/duo-open"))


def test_stale_other_project_context_cannot_override_current_human_intent():
    # Simulate the incident: recent context points to another project and may
    # even contain a newer handoff. It is evidence only, never authorization.
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
    )

    with pytest.raises(ProjectScopeError):
        authorize_recovery_write(
            "benefitflow",
            WriteIntent(project_id="duo-open", target_repository="boberino93-bit/duo-open"),
        )


def test_ambiguous_human_intent_fails_closed_and_writes_nowhere():
    with pytest.raises(ProjectIntentRequired):
        resolve_human_project_intent(None)
    with pytest.raises(ProjectIntentRequired):
        authorize_recovery_write(
            None,
            WriteIntent(project_id="benefitflow", target_repository="boberino93-bit/benefitflow"),
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
