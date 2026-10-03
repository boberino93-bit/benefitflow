# BenefitFlow Controller Succession V1

Controller succession is a revalidation handoff over persisted evidence, not autonomous leader election and not inherited writable authority.

**RECENT CONTEXT IS NOT PROJECT AUTHORITY.** A successor must not make a handoff, queue, forum message, working directory, prior controller state, or newer foreign-project artifact actionable until the current human project intent and BenefitFlow identity lock have been revalidated.

State flow:
`ACTIVE -> HANDOFF_REQUESTED -> SUCCESSOR_REVALIDATING -> (SUCCESSOR_READY | BLOCKED_REVALIDATION) -> OLD_CONTROLLER_RELEASED -> ACTIVE_SUCCESSOR`

The first succession operations are always:
1. resolve current human project intent with `../PROJECT_SCOPE_SELECTION_GATE_V1.md`;
2. validate `PROJECT_IDENTITY_LOCK.json` (`project_id=benefitflow`, repository `boberino93-bit/benefitflow`, coordination root `BenefitFlow-AgentBus/`, `mode=FAIL_CLOSED`);
3. validate project/repository bindings against the lock;
4. only then load or act on the BenefitFlow handoff and persisted project state.

Ambiguous human intent, identity conflict, repository mismatch, coordination-namespace mismatch, or missing identity artifacts yields `BLOCKED_REVALIDATION`: **write nowhere and ask the human which project is intended**.

Every handoff message must record at minimum:
- source controller and intended successor role/agent;
- controller epoch/sequence metadata;
- repository binding and exact observed BenefitFlow HEAD;
- project identity-lock digest;
- last forum message/cutoff observed;
- unresolved research lanes and contradictions;
- Manager dispositions awaiting Primary action;
- accepted-state digest;
- recursive enhancement protocol/registry/cursor references and last registered source observations;
- pending enhancement candidates or graft verification/package-parity work;
- pending human approvals/external actions;
- pending artifacts/releases;
- current agent-spawn policy;
- integrity snapshot/checksum manifest reference.

Before `SUCCESSOR_READY`, the successor independently verifies project identity, dedicated repository binding, current BenefitFlow HEAD, discovery/bootstrap order, all forum deltas after the handoff cursor, open lanes/contradictions, accepted state, recursive enhancement state, backup manifest integrity, package identity hashes, current agent-spawn restrictions, and all pending human approval gates.

For recursive enhancement specifically, the successor must:
- confirm all foreign source repositories remain reference-only and read-only;
- reconcile current registered source HEADs against the packaged local enhancement cursor without writing to the foreign sources;
- preserve unresolved candidate provenance and compatibility state;
- verify its role bootstrap carries the correct Research/Manager/Primary enhancement authority;
- verify package parity/recovery work is complete for any accepted control-plane graft.

If any required item cannot be established, state is `BLOCKED_REVALIDATION`.

Succession changes coordination responsibility only. It does not bypass human booking approval, financial/disclosure gates, repository scope guards, Manager/Research separation, Primary acceptance rules, current no-new-researcher restrictions, the P0 architecture gate, or the foreign-repository read-only invariant.
