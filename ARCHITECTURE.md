# BenefitFlow Alpha Architecture

## Identity and isolation

Canonical identity is `BenefitFlow` / `project_id=benefitflow`; repository is exactly `boberino93-bit/benefitflow`, stable ID `1403645790`. Protocol `3.1.0` treats project identity as a security boundary. `project_guard.py` enforces repository/path binding; `coordination.py` enforces lifecycle, message validation, task/artifact ownership, capabilities, local test primitives, project controls, and explicit bridging.

Root `AGENT_BOOTSTRAP.json` communication-awareness policy and `NEW_PROJECT_BOOTSTRAP.json` project-factory pointer are shared package dependencies. Visibility defaults to `PARTIAL_UNLESS_PROVEN`; a mirror/handoff is not proof of complete forum visibility, and a visibility conflict blocks mutation. New-project work receives its own identity and does not inherit BenefitFlow writable scope.

## Lifecycle, authority, and communication

Agents follow `CREATED -> UNBOUND -> PROJECT_RESOLUTION -> BOUND -> INITIALIZED -> ACTIVE`; only active bound agents mutate. Children inherit parent project identity; logical agent and execution instance identities are separate. Authority remains `Human -> Primary -> Manager -> Research`.

`MESSAGE_ENVELOPE_SCHEMA.json` requires sender/destination project identity, project-qualified channel, task/artifact ownership, correlation/causation/idempotency, sequence, TTL, capabilities, and payload hash. Foreign/malformed records are rejected/quarantined, not heuristically repaired.

## Durable coordination and concurrency

`BenefitFlow-AgentBus/control/DURABLE_COORDINATION_V1.md` is the authoritative multi-process coordination contract. `benefitflow_beta/durable_store.py` + `benefitflow_beta/durable_coordination.py` persists project mode, idempotency, expiring instance leases, versioned state, audit, outbox, and delivery receipts in a SQLite/WAL transactional store.

A state mutation atomically reserves its idempotency key, validates expected version/project mode, changes state, appends a hash-linked audit event, optionally appends an outbox event, records the result, and commits once. Retried completed commands replay the recorded result rather than repeating the side effect. Stale or unauthorized attempts roll back the entire transaction.

Audit/outbox tables are append-only at the database level. Audit records form a SHA-256 chain; outbox payloads are hashed and delivery is represented by an append-only receipt rather than by editing the original event.

SQLite/WAL is the alpha durable backend for multiple processes sharing a local filesystem. Multi-host production deployment requires a sanctioned transactional database service rather than assuming arbitrary network-filesystem SQLite safety.

`tools/prove_multi_project_isolation.py` is a release gate. It races eight BenefitFlow processes, injects a disposable Project-C fixture with identical human-readable IDs, simulates a crashed lease, pauses BenefitFlow while Project-C progresses, restarts the store, and verifies audit/outbox integrity.

## Cross-project exchange and enhancement

Foreign repositories are read-only by default. Ordinary channels never carry cross-project commands. A real exchange is `human-approved Primary -> capability check -> sanitized copy-by-value snapshot -> provenance/integrity -> target validation`. Shared mutable cross-project memory and transitive trust are prohibited. Recursive enhancement remains a read-only foreign-source scan followed by BenefitFlow-local Manager review, Primary disposition, testing, package parity, recovery sync, and cursor advancement.

## Repository write security

`GITHUB_WRITE_SECURITY_POLICY.json` requires exact repository full-name and stable-ID validation plus repository-scoped or equivalently least-privileged runtime credentials. CI requires only `contents: read`. BenefitFlow code cannot itself guarantee the installation-wide scope of the external GitHub App or configure branch protection through a connection that lacks administration access, so those remain server-side account controls in addition to—not instead of—the runtime fail-closed guard.

## Recovery and deployment packages

Recursive backup snapshots include root bootstrap/communication-awareness/project-factory state, project/repository identity, durable-coordination policy/runtime, message schema, GitHub write-security policy, role bootstraps, and other required controls. PRIMARY/MANAGER/RESEARCH form one release set. The dependency map, generator, verifier, and CI proving step detect stale identity/protocol/runtime/package state and require exact source revision traceability.

## Product safety

The P0 architecture gate remains active. Multi-agent hardening does not authorize real member data, live credentials, claims submission, live booking adapters, financial action, or protected external transactions.
