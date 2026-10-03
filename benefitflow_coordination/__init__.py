"""BenefitFlow project-scoped coordination and deployment safety layer."""

from .constants import (
    PROJECT_ID, PROJECT_NAME, PROJECT_VERSION, FRAMEWORK_VERSION,
    PROTOCOL_VERSION, PACKAGE_VERSION, REPOSITORY_IDENTITY,
)
from .identity import ProjectBinding, ProjectScopeError, AgentState, UnboundAgentSession, make_primary_binding, spawn_child

__all__ = [
    "PROJECT_ID", "PROJECT_NAME", "PROJECT_VERSION", "FRAMEWORK_VERSION",
    "PROTOCOL_VERSION", "PACKAGE_VERSION", "REPOSITORY_IDENTITY",
    "ProjectBinding", "ProjectScopeError", "AgentState", "UnboundAgentSession", "make_primary_binding", "spawn_child",
]
