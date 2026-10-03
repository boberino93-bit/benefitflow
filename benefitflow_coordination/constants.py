PROJECT_ID = "benefitflow"
PROJECT_NAME = "BenefitFlow"
REPOSITORY_IDENTITY = "boberino93-bit/benefitflow"
PROJECT_VERSION = "0.4.0-beta.1"
FRAMEWORK_VERSION = "1.1.0-alpha.1"
PROTOCOL_VERSION = "2.0.0-alpha.1"
PACKAGE_VERSION = "0.4.0-beta.1"

DEPLOYMENT_ROLES = {
    "PRIMARY": {"authority_tier": "ORCHESTRATOR"},
    "MANAGER": {"authority_tier": "REVIEWER"},
    "RESEARCH": {"authority_tier": "SPECIALIST"},
}

ROLE_CAPABILITIES = {
    "PRIMARY": [
        "read_source", "write_source", "read_artifacts", "write_artifacts",
        "publish_message", "claim_task", "review_change", "approve_change",
        "build_package", "replace_package",
    ],
    "MANAGER": [
        "read_source", "read_artifacts", "write_artifacts", "publish_message",
        "claim_task", "review_change",
    ],
    "RESEARCH": [
        "read_source", "read_artifacts", "write_artifacts", "publish_message",
        "claim_task",
    ],
}

# Intentionally absent from every packaged role by default. External transactions
# and cross-project exchange require a separately issued, bounded capability.
PRIVILEGED_CAPABILITIES = {"external_action", "cross_project_exchange", "deploy"}

MESSAGE_OUTCOMES = {
    "RECEIVED", "ACCEPTED", "STARTED", "COMPLETED", "FAILED", "REJECTED",
    "QUARANTINED", "EXPIRED", "DUPLICATE", "UNAUTHORIZED", "PROTOCOL_MISMATCH",
}
