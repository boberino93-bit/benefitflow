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
4. Only after those checks agree, load the role bootstrap and BenefitFlow-specific handoffs, queues, accepted state, forum state, roster, or continuation material.

If current human intent is ambiguous or any identity value conflicts: **write nowhere and ask the human which project is intended**.

BenefitFlow must never be committed into `boberino93-bit/duo-open` or another project as a substitute. Foreign project state is read-only evidence where local policy permits and grants zero writable authority.

Binding invariants:
1. repository identity is exactly `boberino93-bit/benefitflow` on `main`;
2. the project identity lock, scope binding, and repository binding must agree;
3. project isolation and stale-context recovery tests must pass;
4. every material binding/HEAD or identity-hardening change is recorded as an immutable forum message;
5. successor packages must carry and hash the identity artifacts, declare the exact source revision and current agent-spawn policy, and pass package readback verification before claiming alignment;
6. existing human approval, P0, privacy/security, role separation, release, single-writer, and no-new-agent restrictions remain in force.
