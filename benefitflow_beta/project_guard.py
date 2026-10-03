from __future__ import annotations
from dataclasses import dataclass
from pathlib import PurePosixPath

PROJECT_ID = "benefitflow"
AGENTBUS_ROOT = PurePosixPath("BenefitFlow-AgentBus")
REPOSITORY_TARGET = "boberino93-bit/benefitflow"
REPOSITORY_BINDING_ACTIVE = True

class ProjectScopeError(RuntimeError):
    pass

@dataclass(frozen=True)
class WriteIntent:
    project_id: str
    target_repository: str | None = None
    target_path: str | None = None

def validate_write_intent(intent: WriteIntent) -> None:
    if intent.project_id != PROJECT_ID:
        raise ProjectScopeError(f"project mismatch: expected {PROJECT_ID}, got {intent.project_id}")
    if intent.target_repository:
        if not REPOSITORY_BINDING_ACTIVE:
            raise ProjectScopeError("BenefitFlow GitHub repository binding is inactive; all GitHub writes are blocked")
        if intent.target_repository != REPOSITORY_TARGET:
            raise ProjectScopeError(f"repository mismatch: expected {REPOSITORY_TARGET}, got {intent.target_repository}")
    if intent.target_path:
        p=PurePosixPath(intent.target_path)
        if p.is_absolute() or ".." in p.parts:
            raise ProjectScopeError("unsafe path")
        if "AgentBus" in intent.target_path and not str(p).startswith(str(AGENTBUS_ROOT)):
            raise ProjectScopeError("AgentBus namespace mismatch")
