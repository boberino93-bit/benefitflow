from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
import re
import uuid

from .constants import PROJECT_ID, PROTOCOL_VERSION, PACKAGE_VERSION, REPOSITORY_IDENTITY


class ProjectScopeError(PermissionError):
    pass


class AgentState(str, Enum):
    CREATED = "CREATED"
    UNBOUND = "UNBOUND"
    PROJECT_RESOLUTION = "PROJECT_RESOLUTION"
    BOUND = "BOUND"
    INITIALIZED = "INITIALIZED"
    ACTIVE = "ACTIVE"
    DRAINING = "DRAINING"
    PAUSED = "PAUSED"
    TERMINATED = "TERMINATED"


MUTATION_STATES = {AgentState.BOUND, AgentState.INITIALIZED, AgentState.ACTIVE}


def require_project_id(project_id: str) -> str:
    if not isinstance(project_id, str) or not project_id.strip():
        raise ProjectScopeError("project_id is required")
    return project_id.strip()


def _safe(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value)).strip("-") or "resource"


def qualify(project_id: str, resource_id: str) -> str:
    return f"{_safe(require_project_id(project_id))}::{_safe(resource_id)}"


def new_instance_id(project_id: str, agent_id: str) -> str:
    return qualify(project_id, f"{agent_id}-{uuid.uuid4().hex}")


def require_same_project(requester_project_id: str, target_project_id: str, *, operation: str) -> None:
    requester = require_project_id(requester_project_id)
    target = require_project_id(target_project_id)
    if requester != target:
        raise ProjectScopeError(
            f"{operation} denied: requester project {requester!r} does not own target project {target!r}"
        )


def require_project_path(project_root: str | Path, candidate: str | Path) -> Path:
    root = Path(project_root).resolve()
    target = Path(candidate).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ProjectScopeError(f"Path escapes project root: {target}") from exc
    return target


@dataclass(frozen=True)
class UnboundAgentSession:
    agent_id: str
    agent_instance_id: str
    state: AgentState = AgentState.UNBOUND

    @classmethod
    def create(cls, agent_id: str):
        return cls(agent_id=agent_id, agent_instance_id=f"unbound::{agent_id}-{uuid.uuid4().hex}")

    def assert_mutation_allowed(self):
        raise ProjectScopeError("UNBOUND agents may not perform mutating operations")

    def bind(self, *, project_id: str, repository_identity: str, project_root: str | Path,
             protocol_version: str = PROTOCOL_VERSION, package_version: str = PACKAGE_VERSION):
        if project_id != PROJECT_ID:
            raise ProjectScopeError("BenefitFlow agent cannot bind to a foreign project")
        if repository_identity != REPOSITORY_IDENTITY:
            raise ProjectScopeError("BenefitFlow agent cannot bind to a foreign repository")
        return ProjectBinding(
            project_id=project_id, repository_identity=repository_identity,
            project_root=str(Path(project_root).resolve()), agent_id=self.agent_id,
            agent_instance_id=new_instance_id(project_id, self.agent_id),
            protocol_version=protocol_version, package_version=package_version,
            state=AgentState.BOUND, root_agent_id=self.agent_id,
        )


@dataclass(frozen=True)
class ProjectBinding:
    project_id: str
    repository_identity: str
    project_root: str
    agent_id: str
    agent_instance_id: str
    protocol_version: str = PROTOCOL_VERSION
    package_version: str = PACKAGE_VERSION
    state: AgentState = AgentState.BOUND
    parent_agent_id: str | None = None
    root_agent_id: str | None = None
    task_id: str | None = None

    def __post_init__(self):
        require_project_id(self.project_id)
        if not self.agent_id or not self.agent_instance_id:
            raise ValueError("agent_id and agent_instance_id are required")
        if self.state in MUTATION_STATES and self.project_id != PROJECT_ID:
            raise ProjectScopeError("BenefitFlow package cannot bind to a foreign project")
        if self.repository_identity != REPOSITORY_IDENTITY:
            raise ProjectScopeError("BenefitFlow package cannot bind to a foreign repository")

    def assert_mutation_allowed(self) -> None:
        if self.state not in MUTATION_STATES:
            raise ProjectScopeError(f"Mutations denied while agent state is {self.state}")

    def assert_project(self, target_project_id: str, operation: str = "operation") -> None:
        self.assert_mutation_allowed()
        require_same_project(self.project_id, target_project_id, operation=operation)

    def assert_repository(self, repository_identity: str) -> None:
        self.assert_mutation_allowed()
        if repository_identity != self.repository_identity:
            raise ProjectScopeError(
                f"Repository mutation denied: expected {self.repository_identity!r}, got {repository_identity!r}"
            )

    def assert_path(self, candidate: str | Path) -> Path:
        self.assert_mutation_allowed()
        return require_project_path(self.project_root, candidate)

    def activate(self):
        return replace(self, state=AgentState.ACTIVE)


def make_primary_binding(project_root: str | Path, *, agent_id: str = "primary") -> ProjectBinding:
    instance = new_instance_id(PROJECT_ID, agent_id)
    return ProjectBinding(
        project_id=PROJECT_ID,
        repository_identity=REPOSITORY_IDENTITY,
        project_root=str(Path(project_root).resolve()),
        agent_id=agent_id,
        agent_instance_id=instance,
        root_agent_id=agent_id,
    )


def spawn_child(parent: ProjectBinding, *, agent_id: str, task_id: str) -> ProjectBinding:
    parent.assert_mutation_allowed()
    if parent.project_id != PROJECT_ID or parent.repository_identity != REPOSITORY_IDENTITY:
        raise ProjectScopeError("Parent binding is not a valid BenefitFlow binding")
    return ProjectBinding(
        project_id=parent.project_id,
        repository_identity=parent.repository_identity,
        project_root=parent.project_root,
        agent_id=agent_id,
        agent_instance_id=new_instance_id(parent.project_id, agent_id),
        protocol_version=parent.protocol_version,
        package_version=parent.package_version,
        state=AgentState.BOUND,
        parent_agent_id=parent.agent_id,
        root_agent_id=parent.root_agent_id or parent.agent_id,
        task_id=task_id,
    )
