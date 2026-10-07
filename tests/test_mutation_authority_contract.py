import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUS = ROOT / "BenefitFlow-AgentBus"
POLICY = BUS / "control" / "PROJECT_MUTATION_AUTHORITY_V1.json"


def test_local_mutation_authority_policy_is_project_bound_and_non_transitive():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    assert policy["project_id"] == "benefitflow"
    assert policy["repository"]["full_name"] == "boberino93-bit/benefitflow"
    assert policy["authority_model"] == "CURRENT_HUMAN_DIRECTIVE_PLUS_PROJECT_BOUND_AGENT"
    never = set(policy["never_conveyed"])
    assert "CROSS_PROJECT_MUTATION" in never
    assert "INTERCOMMUNICATIONS_ENHANCEMENTS_MUTATION" in never
    assert "SWARM_GLOBAL_OR_UNIVERSAL_POLICY_CHANGE" in never
    assert "BENEFITFLOW_PROTECTED_EXTERNAL_TRANSACTION" in never


def test_root_bootstrap_and_security_overlay_reference_local_authority():
    bootstrap = json.loads((ROOT / "AGENT_BOOTSTRAP.json").read_text(encoding="utf-8"))
    overlay = json.loads((ROOT / "AUTHORITY_SECURITY_OVERLAY.json").read_text(encoding="utf-8"))
    write_security = json.loads((BUS / "control" / "GITHUB_WRITE_SECURITY_POLICY.json").read_text(encoding="utf-8"))

    assert bootstrap["local_mutation_authority"]["policy_path"] == "BenefitFlow-AgentBus/control/PROJECT_MUTATION_AUTHORITY_V1.json"
    assert bootstrap["local_mutation_authority"]["cross_project_write"] == "DENY"
    assert overlay["local_project_authority"]["policy"] == "BenefitFlow-AgentBus/control/PROJECT_MUTATION_AUTHORITY_V1.json"
    assert write_security["runtime_binding"]["project_mutation_authority_policy"] == "BenefitFlow-AgentBus/control/PROJECT_MUTATION_AUTHORITY_V1.json"
    assert write_security["runtime_binding"]["correct_repository_target_alone_is_not_sufficient_authority"] is True


def test_all_active_role_bootstraps_inherit_local_authority_without_role_escalation():
    for role in ("PRIMARY", "MANAGER", "RESEARCH"):
        text = (BUS / "bootstrap" / f"{role}.md").read_text(encoding="utf-8")
        assert "PROJECT_MUTATION_AUTHORITY_V1.json" in text
        assert "BenefitFlow-local mutation authority" in text
        assert "Intercommunications Enhancements" in text


def test_recursive_backup_must_carry_local_authority_controls():
    text = (ROOT / "tools" / "build_recursive_backup.py").read_text(encoding="utf-8")
    assert 'AUTHORITY_SECURITY_OVERLAY.json' in text
    assert 'PROJECT_MUTATION_AUTHORITY_V1.json' in text
    assert 'project_mutation_authority_included' in text


def test_repository_bootstrap_requires_current_local_authority_before_mutation():
    text = (ROOT / "REPOSITORY_BOOTSTRAP.md").read_text(encoding="utf-8")
    assert "PROJECT_MUTATION_AUTHORITY_V1.json" in text
    assert "current BenefitFlow-local human authorization must exist before mutation" in text
