# BenefitFlow Project Identity and Recovery Hardening V1

Status: LOCAL CONTROL-PLANE HARDENING APPLIED
Project: BenefitFlow
Project ID: `benefitflow`
Writable repository: `boberino93-bit/benefitflow`
Canonical branch: `main`
Coordination root: `BenefitFlow-AgentBus/`

## Incident lesson adopted

Recent context is not project authority. A recovering or replacement agent must never select writable project scope from the most recent chat, repository, handoff, task, working directory, forum item, artifact, or previous-agent assumption.

## Enforced recovery sequence

1. Current human project intent -> `PROJECT_SCOPE_SELECTION_GATE_V1.md`.
2. Machine-readable identity validation -> `control/PROJECT_IDENTITY_LOCK.json`.
3. Project/repository binding consistency validation.
4. Role bootstrap.
5. Only then BenefitFlow-specific handoffs, queues, accepted state, roster, forum deltas, prior-agent continuation state, Slack queue items, or work assignments become actionable.

Ambiguous intent or conflicting identity values fail closed: write nowhere and ask the human which project is intended.

## Cross-project boundary

Foreign project repositories are read-only evidence where BenefitFlow policy permits. Cross-project writes are denied by default. Foreign project state, handoffs, accepted truth, task queues, credentials, identifiers, or recency provide zero BenefitFlow writable authority.

## Role propagation

The identity-first rule is embedded in the active Primary, Manager, and Research bootstraps and in controller succession/recovery contracts. Existing authority, P0, privacy/security, human-approval, release, single-writer, and no-new-agent restrictions remain unchanged.

## Package propagation

Recursive backup and successor-package builders now include and hash the identity artifacts. Package manifests declare project/repository/branch/namespaces, exact source revision, role/package type, current agent-spawn policy, and identity hashes. Generated packages must pass readback verification before generation is considered successful.

The deployment snapshot contract requires the same identity-first ordering and rejects absent/inconsistent identity state, wrong-project authority, late scope validation, checksum failure, missing spawn policy, or source-revision mismatch.

## Regression coverage

`tests/test_project_isolation.py` contains the bounded stale-other-project-context recovery scenario and the ambiguous-human-intent scenario. The intended result is BenefitFlow selection from current human intent despite a newer foreign handoff, with any foreign write rejected; ambiguous intent must raise the fail-closed project-intent guard before any write.

## Package/build surfaces hardened

- `tools/build_recursive_backup.py`
- `tools/generate_successor_package.py`
- `tools/generate_all_role_packages.py` (orchestration inspected; it delegates to the hardened generator/verifier)
- `tools/verify_role_package_enhancement_sync.py`
- `.github/workflows/benefitflow-ci.yml` (inspected; it runs verifier, pytest, framework tests, generates/validates PRIMARY/MANAGER/RESEARCH packages, then uploads ZIP artifacts)
- `benefitflow_beta/project_guard.py`
- `tests/test_project_isolation.py`

This checkpoint changes BenefitFlow-owned state only. It does not grant authority over any other project and does not authorize new agents or a new research round.
