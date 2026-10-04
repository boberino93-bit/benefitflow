from __future__ import annotations
from dataclasses import dataclass
from pathlib import PurePosixPath

PROJECT_ID = "benefitflow"
AGENTBUS_ROOT = PurePosixPath("BenefitFlow-AgentBus")
REPOSITORY_TARGET = "boberino93-bit/benefitflow"
REPOSITORY_ID = 1403645790
REPOSITORY_BINDING_ACTIVE = True

class ProjectScopeError(RuntimeError):
    pass

class ProjectIntentRequired(ProjectScopeError):
    pass

@dataclass(frozen=True)
class WriteIntent:
    project_id: str
    target_repository: str | None = None
    target_repository_id: int | None = None
    target_path: str | None = None

def resolve_human_project_intent(current_human_project_id: str | None) -> str:
    if current_human_project_id is None or not current_human_project_id.strip():
        raise ProjectIntentRequired("current human project intent is required before any project write")
    project_id = current_human_project_id.strip().lower()
    if project_id != PROJECT_ID:
        raise ProjectScopeError(f"project mismatch: expected {PROJECT_ID}, got {project_id}")
    return PROJECT_ID

def validate_write_intent(intent: WriteIntent) -> None:
    if intent.project_id != PROJECT_ID:
        raise ProjectScopeError(f"project mismatch: expected {PROJECT_ID}, got {intent.project_id}")
    if intent.target_repository or intent.target_repository_id is not None:
        if not REPOSITORY_BINDING_ACTIVE:
            raise ProjectScopeError("BenefitFlow GitHub repository binding is inactive; all GitHub writes are blocked")
        if intent.target_repository and intent.target_repository != REPOSITORY_TARGET:
            raise ProjectScopeError(f"repository mismatch: expected {REPOSITORY_TARGET}, got {intent.target_repository}")
        if intent.target_repository_id is not None and intent.target_repository_id != REPOSITORY_ID:
            raise ProjectScopeError(f"repository id mismatch: expected {REPOSITORY_ID}, got {intent.target_repository_id}")
    if intent.target_path:
        p = PurePosixPath(intent.target_path)
        if p.is_absolute() or ".." in p.parts or "." in p.parts:
            raise ProjectScopeError("unsafe path")
        normalized = str(p)
        if "AgentBus" in normalized and not normalized.startswith(str(AGENTBUS_ROOT) + "/"):
            raise ProjectScopeError("AgentBus namespace mismatch")

def authorize_recovery_write(current_human_project_id: str | None, intent: WriteIntent) -> None:
    resolved = resolve_human_project_intent(current_human_project_id)
    if intent.project_id != resolved:
        raise ProjectScopeError(
            f"write intent project {intent.project_id} does not match resolved human intent {resolved}"
        )
    validate_write_intent(intent)
