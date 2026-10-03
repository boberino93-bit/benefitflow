import pytest
from benefitflow_beta.project_guard import ProjectScopeError, WriteIntent, validate_write_intent

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
