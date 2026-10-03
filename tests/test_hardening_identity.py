from pathlib import Path
import pytest

from benefitflow_coordination.constants import PROJECT_ID, REPOSITORY_IDENTITY
from benefitflow_coordination.identity import (
    AgentState, ProjectBinding, ProjectScopeError, UnboundAgentSession, make_primary_binding, spawn_child,
)


def test_primary_binding_is_benefitflow(tmp_path):
    binding = make_primary_binding(tmp_path)
    assert binding.project_id == PROJECT_ID
    assert binding.repository_identity == REPOSITORY_IDENTITY
    binding.assert_repository(REPOSITORY_IDENTITY)


def test_foreign_repository_fails_closed(tmp_path):
    with pytest.raises(ProjectScopeError):
        ProjectBinding(
            project_id="benefitflow",
            repository_identity="boberino93-bit/duo-open",
            project_root=str(tmp_path),
            agent_id="research",
            agent_instance_id="benefitflow::research-1",
        )


def test_unbound_agent_cannot_mutate(tmp_path):
    binding = ProjectBinding(
        project_id="benefitflow",
        repository_identity=REPOSITORY_IDENTITY,
        project_root=str(tmp_path),
        agent_id="agent",
        agent_instance_id="benefitflow::agent-1",
        state=AgentState.UNBOUND,
    )
    with pytest.raises(ProjectScopeError):
        binding.assert_mutation_allowed()


def test_child_inherits_project_and_repository(tmp_path):
    parent = make_primary_binding(tmp_path)
    child = spawn_child(parent, agent_id="researcher-01", task_id="task-001")
    assert child.project_id == parent.project_id
    assert child.repository_identity == parent.repository_identity
    assert child.parent_agent_id == parent.agent_id
    assert child.task_id == "task-001"


def test_path_escape_fails_closed(tmp_path):
    binding = make_primary_binding(tmp_path)
    with pytest.raises(ProjectScopeError):
        binding.assert_path(tmp_path.parent / "duo-open")


def test_true_unbound_session_has_no_project_and_cannot_mutate(tmp_path):
    session = UnboundAgentSession.create("new-agent")
    assert session.state == AgentState.UNBOUND
    with pytest.raises(ProjectScopeError):
        session.assert_mutation_allowed()
    binding = session.bind(project_id="benefitflow", repository_identity=REPOSITORY_IDENTITY, project_root=tmp_path)
    assert binding.project_id == "benefitflow"


def test_unbound_session_cannot_bind_foreign_project(tmp_path):
    session = UnboundAgentSession.create("new-agent")
    with pytest.raises(ProjectScopeError):
        session.bind(project_id="duo-open", repository_identity="boberino93-bit/duo-open", project_root=tmp_path)
