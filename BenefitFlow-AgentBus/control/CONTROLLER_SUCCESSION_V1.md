# BenefitFlow Controller Succession V1

Controller succession is a revalidation handoff over persisted evidence, not autonomous leader election.

State flow:
`ACTIVE -> HANDOFF_REQUESTED -> SUCCESSOR_REVALIDATING -> (SUCCESSOR_READY | BLOCKED_REVALIDATION) -> OLD_CONTROLLER_RELEASED -> ACTIVE_SUCCESSOR`

Every handoff message must record at minimum:
- source controller and intended successor role/agent;
- controller epoch/sequence metadata;
- repository binding and exact observed BenefitFlow HEAD;
- last forum message/cutoff observed;
- unresolved research lanes and contradictions;
- Manager dispositions awaiting Primary action;
- accepted-state digest;
- recursive enhancement protocol/registry/cursor references and last registered source observations;
- pending enhancement candidates or graft verification/package-parity work;
- pending human approvals/external actions;
- pending artifacts/releases;
- integrity snapshot/checksum manifest reference.

Before `SUCCESSOR_READY`, the successor independently verifies project identity, dedicated repository binding, current BenefitFlow HEAD, discovery/contracts, all forum deltas after the handoff cursor, open lanes/contradictions, accepted state, recursive enhancement state, backup manifest integrity, and all pending human approval gates.

For recursive enhancement specifically, the successor must:
- confirm all foreign source repositories remain reference-only and read-only;
- reconcile current registered source HEADs against the packaged local enhancement cursor without writing to the foreign sources;
- preserve unresolved candidate provenance and compatibility state;
- verify its role bootstrap carries the correct Research/Manager/Primary enhancement authority;
- verify package parity/recovery work is complete for any accepted control-plane graft.

If any required item cannot be established, state is `BLOCKED_REVALIDATION`.

Succession changes coordination responsibility only. It does not bypass human booking approval, financial/disclosure gates, repository scope guards, Manager/Research separation, Primary acceptance rules, the P0 architecture gate, or the foreign-repository read-only invariant.
