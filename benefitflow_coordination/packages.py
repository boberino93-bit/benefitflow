from .constants import (
    DEPLOYMENT_ROLES, FRAMEWORK_VERSION, PACKAGE_VERSION, PROJECT_ID,
    PROJECT_VERSION, PROTOCOL_VERSION, REPOSITORY_IDENTITY,
)
from .identity import ProjectScopeError


REQUIRED = {
    "schema", "project_id", "repository_identity", "deployment_role", "authority_tier",
    "project_version", "framework_version", "protocol_version", "package_version",
    "source_revision", "built_at", "included_components", "component_hashes", "capabilities",
}


def validate_agent_package_manifest(manifest: dict, *, expected_source_revision: str | None = None):
    missing = REQUIRED - set(manifest)
    if missing:
        raise ValueError(f"Agent package manifest missing fields: {sorted(missing)}")
    if manifest["project_id"] != PROJECT_ID:
        raise ProjectScopeError("Foreign deployment package")
    if manifest["repository_identity"] != REPOSITORY_IDENTITY:
        raise ProjectScopeError("Foreign repository deployment package")
    role = manifest["deployment_role"]
    if role not in DEPLOYMENT_ROLES:
        raise ValueError("Unsupported deployment role")
    if manifest["authority_tier"] != DEPLOYMENT_ROLES[role]["authority_tier"]:
        raise ValueError("Deployment role/authority mismatch")
    if manifest["project_version"] != PROJECT_VERSION:
        raise ValueError("Deployment package project version mismatch")
    if manifest["framework_version"] != FRAMEWORK_VERSION:
        raise ValueError("Deployment package framework version mismatch")
    if manifest["protocol_version"] != PROTOCOL_VERSION:
        raise ValueError("Stale or incompatible deployment package protocol")
    if manifest["package_version"] != PACKAGE_VERSION:
        raise ValueError("Deployment package generation mismatch")
    if expected_source_revision is not None and manifest["source_revision"] != expected_source_revision:
        raise ValueError("Deployment package source revision mismatch")
    if not manifest["source_revision"] or manifest["source_revision"] == "UNKNOWN":
        raise ValueError("Deployment package source revision must be explicit")
    return True
