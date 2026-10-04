# BenefitFlow Alpha Architecture

## Identity and isolation

Canonical identity is `BenefitFlow` / `project_id=benefitflow`; repository is exactly `boberino93-bit/benefitflow`, stable ID `1403645790`. Protocol `3.1.0` treats project identity as a security boundary. `project_guard.py` enforces repository/path binding; `coordination.py` enforces lifecycle, message validation, task/artifact ownership, capabilities, leases, idempotency, stale-write protection, project controls, and explicit bridging.

Root `AGENT_BOOTSTRAP.json` communication-awareness policy is a shared package dependency. Visibility defaults to `PARTIAL_UNLESS_PROVEN`; a mirror/handoff is not proof of complete forum visibility, and a visibility conflict blocks mutation.

## Lifecycle, authority, and communication

Agents follow `CREATED -> UNBOUND -> PROJECT_RESOLUTION -> BOUND -> INITIALIZED -> ACTIVE`; only active bound agents mutate. Children inherit parent project identity; logical agent and execution instance identities are separate. Authority remains `Human -> Primary -> Manager -> Research`.

`MESSAGE_ENVELOPE_SCHEMA.json` requires sender/destination project identity, project-qualified channel, task/artifact ownership, correlation/causation/idempotency, sequence, TTL, capabilities, and payload hash. Foreign/malformed records are rejected/quarantined, not heuristically repaired.

Claimable work uses project-scoped expiring instance leases; retries use idempotency; version-sensitive state uses expected-version compare-and-set. BenefitFlow may be independently paused/degraded without stopping unrelated projects.

## Cross-project exchange and enhancement

Foreign repositories are read-only by default. Ordinary channels never carry cross-project commands. A real exchange is `human-approved Primary -> capability check -> sanitized copy-by-value snapshot -> provenance/integrity -> target validation`. Shared mutable cross-project memory and transitive trust are prohibited. Recursive enhancement remains a read-only foreign-source scan followed by BenefitFlow-local Manager review, Primary disposition, testing, package parity, recovery sync, and cursor advancement.

## Recovery and deployment packages

Recursive backup snapshots now include root bootstrap/communication-awareness state, project/repository identity, message schema, coordination runtime, project guard, role bootstraps, and other required controls. PRIMARY/MANAGER/RESEARCH form one release set. The dependency map, generator, and verifier detect stale identity/protocol/runtime/package state and require exact source revision traceability.

## Product safety

The P0 architecture gate remains active. Multi-agent hardening does not authorize real member data, live credentials, claims submission, live booking adapters, financial action, or protected external transactions.
