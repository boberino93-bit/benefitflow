# BenefitFlow Mutation Authority Incident — Forensic Hardening V1

Date: 2026-10-07  
Project: `benefitflow`  
Repository: `boberino93-bit/benefitflow`  
Status: **LOCAL REMEDIATION APPLIED / CROSS-PROJECT REVIEW PENDING EXTERNAL AUTHORITY**

## Incident

During a BenefitFlow bootstrap change, an agent interpreted the user's instruction to commit a change as sufficient to perform repository mutations without first preserving the intended distinction between BenefitFlow-local project authority and swarm/cross-project authority.

The user corrected the model twice:

1. repository mutation should have respected the project's authorization boundary rather than treating task intent alone as authority; and
2. the user's current explicit BenefitFlow authorization, combined with an agent correctly bound to BenefitFlow, *is* sufficient for BenefitFlow-local changes. Separate swarm/global or Intercommunications Enhancements authority is not required for purely local BenefitFlow mutations.

The resulting corrected model is therefore not "every local write requires swarm-grade authorization." It is:

`current explicit human BenefitFlow directive + correct BenefitFlow project binding + correct repository/namespace + role authority -> bounded BenefitFlow-local mutation`

with hard denial of scope expansion into:

- Intercommunications Enhancements;
- another project or repository;
- swarm-global/universal governance;
- root authority outside BenefitFlow; or
- BenefitFlow protected external/transactional actions.

## Root cause

The pre-incident system had strong project/repository identity controls but the executable `project_guard.py` only validated *where* a write was going. A correctly targeted BenefitFlow write could pass project isolation without a separate executable representation of the current human authorization scope.

This created a gap between policy language and the write path:

`task intent -> correct BenefitFlow target -> connector write`

rather than:

`task intent -> current human BenefitFlow authorization -> project binding -> target validation -> scope validation -> mutation`

A second contributing factor was over-broad interpretation of upstream swarm authorization rules after the incident. That would have created unnecessary ceremony for ordinary BenefitFlow-local development and would have incorrectly treated Intercommunications Enhancements as the authority source for local project mutations.

## Local remediation applied

### Runtime

`benefitflow_beta/project_guard.py` now defines `MutationAuthority` and requires it at the project-write gate. It verifies:

- current human authorization is present;
- authority is bound to `project_id=benefitflow`;
- authority source is the current human project directive;
- scope is `BENEFITFLOW_LOCAL`;
- repository writes remain inside `boberino93-bit/benefitflow` / repository ID `1403645790`;
- cross-project scope is denied;
- swarm-global scope is denied;
- protected external actions are denied;
- optional revision-bound authority fails closed on HEAD drift.

### Bootstrap and role propagation

The local authority rule is now represented in:

- `AGENT_BOOTSTRAP.md`
- `AGENT_BOOTSTRAP.json`
- `REPOSITORY_BOOTSTRAP.md`
- `AUTHORITY_SECURITY_OVERLAY.json`
- `BenefitFlow-AgentBus/control/PROJECT_MUTATION_AUTHORITY_V1.json`
- `BenefitFlow-AgentBus/control/GITHUB_WRITE_SECURITY_POLICY.json`
- `BenefitFlow-AgentBus/bootstrap/PRIMARY.md`
- `BenefitFlow-AgentBus/bootstrap/MANAGER.md`
- `BenefitFlow-AgentBus/bootstrap/RESEARCH.md`

### Recovery/package propagation

`tools/build_recursive_backup.py` now requires and hashes the local mutation-authority policy and authority overlay so recursive snapshots cannot silently omit the new control.

### Regression coverage

`tests/test_project_isolation.py` now tests missing authority, denied authorization, valid local authority, cross-project escalation, swarm-global escalation, protected external actions, wrong authority source/scope, stale context, and revision drift.

`tests/test_mutation_authority_contract.py` tests policy propagation across root bootstrap, overlay, GitHub write policy, all active roles, repository bootstrap, and recursive backup construction.

## Security properties after remediation

The intended invariant is now:

**Correct repository identity is necessary but not sufficient for mutation.**

A BenefitFlow agent needs current user authorization for the BenefitFlow task and must remain within the local project boundary.

Conversely:

**BenefitFlow-local mutation authority is sufficient for BenefitFlow-local project work and must not be incorrectly escalated into a requirement for swarm/root authorization.**

This preserves productive project autonomy while keeping cross-project and protected external actions fail-closed.

## Known residual risk

GitHub `main` was observed without branch protection during the forensic review. Runtime/project-level controls therefore remain important because a connector with repository write capability can technically reach the branch. Server-side branch protection or an equivalent reviewed-main policy remains recommended defense in depth, but changing account/repository administration settings is outside this BenefitFlow-local remediation unless separately authorized and supported.

A package-generator enhancement to place the local mutation policy in the top-level `IDENTITY_CONTEXT` was attempted but the connector rejected that particular tool call. The recursive deployment snapshot now includes the policy, and tests enforce that inclusion. Future package-generator maintenance should make the policy a first-class identity-context entry as well.

## Cross-project review status

No Intercommunications Enhancements mutation was performed as part of this remediation. A generalized review prompt is stored locally in the BenefitFlow Artifactory as a **pending outbound proposal**. It conveys no authority to the destination project and must be reviewed/routed by an appropriately authorized Primary or Manager there.
