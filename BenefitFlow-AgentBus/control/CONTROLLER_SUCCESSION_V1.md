# BenefitFlow Controller Succession V1 — Protocol 2 Compatible

Controller succession is a revalidation handoff over persisted evidence, not autonomous leader election.

State flow:
`ACTIVE -> HANDOFF_REQUESTED -> SUCCESSOR_REVALIDATING -> (SUCCESSOR_READY | BLOCKED_REVALIDATION) -> OLD_CONTROLLER_RELEASED -> ACTIVE_SUCCESSOR`

Every handoff message must record at minimum:
- source controller and intended successor role/agent/execution instance;
- controller epoch/sequence metadata and Protocol 2 correlation/causation identifiers;
- repository binding and exact observed HEAD;
- protocol/package versions and role deployment-package source revision;
- last forum message/cutoff observed;
- unresolved research lanes, active/expired leases, contradictions, and Manager dispositions awaiting Primary action;
- accepted-state digest;
- pending human approvals/external actions;
- pending artifacts/releases;
- integrity snapshot/checksum manifest reference.

Before `SUCCESSOR_READY`, the successor independently verifies project identity, dedicated repository binding, current repository HEAD, current role package/protocol compatibility, discovery/contracts, all forum deltas after the handoff cursor, open tasks/leases/contradictions, accepted state, backup manifest integrity, and all pending human approval gates.

If any required item cannot be established, state is `BLOCKED_REVALIDATION`.

Succession changes coordination responsibility only. It does not bypass human booking approval, financial/disclosure gates, repository scope guards, Manager/Reviewer separation, capability checks, or Primary acceptance rules.
