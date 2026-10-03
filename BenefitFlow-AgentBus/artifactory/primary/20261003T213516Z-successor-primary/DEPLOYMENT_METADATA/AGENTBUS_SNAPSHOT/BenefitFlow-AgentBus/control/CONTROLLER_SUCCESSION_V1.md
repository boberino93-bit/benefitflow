# BenefitFlow Controller Succession V1

Controller succession is a revalidation handoff over persisted evidence, not autonomous leader election.

State flow:
`ACTIVE -> HANDOFF_REQUESTED -> SUCCESSOR_REVALIDATING -> (SUCCESSOR_READY | BLOCKED_REVALIDATION) -> OLD_CONTROLLER_RELEASED -> ACTIVE_SUCCESSOR`

Every handoff message must record at minimum:
- source controller and intended successor role/agent;
- controller epoch/sequence metadata;
- repository binding and exact observed HEAD when a repository exists;
- last forum message/cutoff observed;
- unresolved research lanes and contradictions;
- reviewer dispositions awaiting Primary action;
- accepted-state digest;
- pending human approvals/external actions;
- pending artifacts/releases;
- integrity snapshot/checksum manifest reference.

Before `SUCCESSOR_READY`, the successor independently verifies project identity, dedicated repository binding, current repository HEAD, discovery/contracts, all forum deltas after the handoff cursor, open lanes/contradictions, accepted state, backup manifest integrity, and all pending human approval gates.

If any required item cannot be established, state is `BLOCKED_REVALIDATION`.

Succession changes coordination responsibility only. It does not bypass human booking approval, financial/disclosure gates, repository scope guards, reviewer separation, or Primary acceptance rules.
