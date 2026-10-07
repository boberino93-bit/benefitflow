from __future__ import annotations
from dataclasses import dataclass
from pathlib import PurePosixPath

PROJECT_ID = "benefitflow"
AGENTBUS_ROOT = PurePosixPath("BenefitFlow-AgentBus")
REPOSITORY_TARGET = "boberino93-bit/benefitflow"
REPOSITORY_ID = 1403645790
REPOSITORY_BINDING_ACTIVE = True

LOCAL_AUTHORITY_SCOPE = "BENEFITFLOW_LOCAL"
CURRENT_HUMAN_DIRECTIVE = "CURRENT_HUMAN_PROJECT_DIRECTIVE"


class ProjectScopeError(RuntimeError):
    pass


class ProjectIntentRequired(ProjectScopeError):
    pass


class MutationAuthorizationRequired(ProjectScopeError):
    pass


@dataclass(frozen=True)
class WriteIntent:
    project_id: str
    target_repository: str | None = None
    target_repository_id: int | None = None
    target_path: str | None = None
    cross_project: bool = False
    swarm_global: bool = False
    protected_external_action: bool = False


@dataclass(frozen=True)
class MutationAuthority:
    """Bounded BenefitFlow-local mutation authority.

    A current explicit human directive plus a correctly project-bound BenefitFlow
    agent is sufficient for BenefitFlow-local source/configuration/coordination
    mutation. This object never conveys cross-project, swarm-global, root-governance,
    or protected external/transaction authority.
    """

    project_id: str
    human_authorized: bool
    source: str = CURRENT_HUMAN_DIRECTIVE
    scope: str = LOCAL_AUTHORITY_SCOPE
    repository_write_allowed: bool = True
    expected_repository_head: str | None = None


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


def validate_mutation_authority(
    authority: MutationAuthority | None,
    intent: WriteIntent,
    *,
    current_repository_head: str | None = None,
) -> None:
    if authority is None:
        raise MutationAuthorizationRequired("explicit current BenefitFlow mutation authority is required")
    if not authority.human_authorized:
        raise MutationAuthorizationRequired("current human authorization is required for BenefitFlow mutation")
    if authority.project_id != PROJECT_ID or authority.project_id != intent.project_id:
        raise ProjectScopeError("mutation authority is not bound to the current BenefitFlow project")
    if authority.source != CURRENT_HUMAN_DIRECTIVE:
        raise MutationAuthorizationRequired("mutation authority must come from a current human project directive")
    if authority.scope != LOCAL_AUTHORITY_SCOPE:
        raise MutationAuthorizationRequired("only BenefitFlow-local mutation authority is recognized by this guard")
    if intent.cross_project:
        raise ProjectScopeError("BenefitFlow-local authority cannot authorize cross-project mutation")
    if intent.swarm_global:
        raise ProjectScopeError("BenefitFlow-local authority cannot authorize swarm-global mutation")
    if intent.protected_external_action:
        raise ProjectScopeError("BenefitFlow-local repository authority cannot authorize protected external/transaction actions")
    if (intent.target_repository or intent.target_repository_id is not None) and not authority.repository_write_allowed:
        raise MutationAuthorizationRequired("repository mutation is outside the granted BenefitFlow-local authority")
    if authority.expected_repository_head is not None:
        if current_repository_head is None:
            raise MutationAuthorizationRequired("current repository HEAD is required for revision-bound mutation authority")
        if current_repository_head != authority.expected_repository_head:
            raise MutationAuthorizationRequired(
                "repository HEAD changed after authority was bound; reread state and obtain/derive a fresh current directive scope"
            )


def authorize_project_write(
    current_human_project_id: str | None,
    intent: WriteIntent,
    authority: MutationAuthority | None,
    *,
    current_repository_head: str | None = None,
) -> None:
    resolved = resolve_human_project_intent(current_human_project_id)
    if intent.project_id != resolved:
        raise ProjectScopeError(
            f"write intent project {intent.project_id} does not match resolved human intent {resolved}"
        )
    validate_write_intent(intent)
    validate_mutation_authority(authority, intent, current_repository_head=current_repository_head)


def authorize_recovery_write(
    current_human_project_id: str | None,
    intent: WriteIntent,
    authority: MutationAuthority | None = None,
    *,
    current_repository_head: str | None = None,
) -> None:
    """Backward-compatible entry point; recovery writes use the same local authority gate."""

    authorize_project_write(
        current_human_project_id,
        intent,
        authority,
        current_repository_head=current_repository_head,
    )
