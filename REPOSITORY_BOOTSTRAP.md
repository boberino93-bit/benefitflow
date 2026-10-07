# BenefitFlow Dedicated Repository Bootstrap

Canonical project: `BenefitFlow`
Project ID: `benefitflow`
Canonical repository: `boberino93-bit/benefitflow`
Canonical branch: `main`

Status: **VERIFIED / BOUND / FAIL-CLOSED**

## Mandatory first operations

A new, recovering, reassigned, or successor agent must not infer writable scope from recent chat, a previous handoff, working directory, open repository, newest artifact, or prior-agent state.

The first project operations are:
1. Resolve the current human project intent using `BenefitFlow-AgentBus/PROJECT_SCOPE_SELECTION_GATE_V1.md`.
2. Validate `BenefitFlow-AgentBus/control/PROJECT_IDENTITY_LOCK.json` and require `project_id=benefitflow`, repository `boberino93-bit/benefitflow`, branch `main`, coordination root `BenefitFlow-AgentBus/`, and `mode=FAIL_CLOSED`.
3. Validate `BenefitFlow-AgentBus/control/PROJECT_SCOPE_BINDING.json` and `BenefitFlow-AgentBus/control/GITHUB_REPOSITORY_BINDING.json` against the identity lock.
4. Read `BenefitFlow-AgentBus/control/PROJECT_MUTATION_AUTHORITY_V1.json` and establish whether the current human directive authorizes the BenefitFlow-local mutation being attempted.
5. Only after those checks agree, load the role bootstrap and BenefitFlow-specific handoffs, queues, accepted state, forum state, roster, or continuation material.

If current human intent is ambiguous, current BenefitFlow mutation authorization is absent, or any identity value conflicts: **write nowhere and continue only safe read-only work**.

A current explicit human BenefitFlow directive plus a correctly project-bound BenefitFlow agent is sufficient for the coherent BenefitFlow-local source/configuration/test/documentation/coordination mutations needed to execute that bounded project task. Do not require swarm-global or Intercommunications Enhancements authorization merely because a local file concerns governance.

That local authority is non-transitive. It cannot authorize writes to Intercommunications Enhancements, Duo Open, another project, another repository, swarm-global/universal governance, or protected external BenefitFlow transactions. Those scopes require their own authority at the applicable boundary.

BenefitFlow must never be committed into `boberino93-bit/duo-open` or another project as a substitute. Foreign project state is read-only evidence where local policy permits and grants zero writable authority.

Binding invariants:
1. repository identity is exactly `boberino93-bit/benefitflow` on `main`;
2. the project identity lock, scope binding, and repository binding must agree;
3. current BenefitFlow-local human authorization must exist before mutation;
4. project isolation, local-authority, stale-context, and HEAD-drift recovery tests must pass;
5. when authority is revision-bound, repository HEAD drift forces reread/revalidation before mutation;
6. every material binding/HEAD or identity-hardening change is recorded as an immutable forum/artifact record when the active protocol requires durable persistence;
7. successor packages must carry and hash the identity and local mutation-authority artifacts, declare the exact source revision and current agent-spawn policy, and pass package readback verification before claiming alignment;
8. existing P0, privacy/security, role separation, release, single-writer, booking/claim/financial/external-action and other protected transaction restrictions remain in force.
