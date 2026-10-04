# BenefitFlow Multi-Project Protocol V3.1

Status: ACTIVE  
Project: `benefitflow`  
Protocol: `3.1.0`

## Security boundary

`project_id` is an authorization boundary. BenefitFlow is bound to `boberino93-bit/benefitflow` (stable repository ID `1403645790`) and `/project/benefitflow/*`. Missing, conflicting, foreign, or ambiguous identity fails closed. Ordinary channels never carry cross-project commands.

Cross-project exchange is denied by default and uses only an explicitly authorized sanitized **copy-by-value** snapshot with source/target project IDs, provenance, and payload integrity. Shared mutable cross-project state is prohibited. Primary plus explicit human approval are required; communication is never authorization.

## Agent lifecycle and binding

Executable lifecycle: `CREATED -> UNBOUND -> PROJECT_RESOLUTION -> BOUND(project_id) -> INITIALIZED -> ACTIVE -> DRAINING/PAUSED -> TERMINATED`. Only an `ACTIVE` project-bound execution may mutate. Child agents inherit the parent's `project_id`; conflicting identity fails closed. Logical `agent_id` and execution `agent_instance_id` are distinct; restarted instances do not inherit instance-owned leases.

## Message, task, and artifact contract

Protocol `3.1.0` executable messages use `control/MESSAGE_ENVELOPE_SCHEMA.json`. They carry globally safe message/correlation/causation/idempotency identities, explicit sender and destination project identity, canonical `/project/benefitflow/...` routing, task `project_id`, artifact `project_id`, sequence, TTL, required capabilities, payload, and SHA-256 integrity. `benefitflow_beta/coordination.py` validates caller/session identity, project/task/artifact ownership, channel namespace, protocol, capabilities, timestamps, and integrity before execution. Malformed/foreign/stale/spoofed records are rejected or quarantined rather than repaired heuristically. Historical V1/V2/V3.0 records remain evidence, not automatically executable commands.

## Repository and credential boundary

All source mutations validate project identity, exact repository name, stable repository ID when supplied, canonical path, and AgentBus namespace through `benefitflow_beta/project_guard.py`. `control/GITHUB_WRITE_SECURITY_POLICY.json` additionally requires repository-scoped or equivalently least-privileged runtime credentials. CI uses `contents: read`; package generation does not require a write token. Server-side installation scope and branch protection are external account controls and do not weaken the runtime fail-closed binding.

## Durable concurrency and recovery

`control/DURABLE_COORDINATION_V1.md` governs mutable coordination shared by multiple processes or required to survive restart/crash. `benefitflow_beta/durable_coordination.py` is the authoritative durable runtime for that state.

The durable backend persists project control, idempotency, expiring `agent_instance_id` leases, versioned state, append-only audit records, append-only outbox events, and append-only delivery receipts. State mutation, idempotency completion, audit, and outbox publication commit atomically. Stale writes and conflicting leases fail rather than overwriting newer state. A completed idempotency key replays the original result without repeating the state transition or publication.

Audit rows form a per-project SHA-256 hash chain. Database triggers reject update/delete on audit/outbox/delivery rows. Delivery is an append-only receipt; downstream systems must consume event IDs idempotently.

The alpha backend is SQLite/WAL for multiple processes sharing a local filesystem. It is not an authorization to use arbitrary network-filesystem SQLite for multi-host production; multi-host deployment requires a sanctioned transactional database service.

## Project control and governance

Primary, Manager, and Research have distinct least-privilege capabilities. Research produces evidence; Manager reviews/recommends; Primary integrates accepted truth. Protected external/financial actions, sensitive identifier disclosure, deployment, material booking-term changes, project-control changes, and cross-project exchange remain behind explicit human approval where applicable.

Durable BenefitFlow project mode is independently `ACTIVE`, `PAUSED`, or `DEGRADED_READ_ONLY`. Only Primary with explicit human approval may change it, using expected-version compare-and-set. Pausing BenefitFlow cannot pause a foreign project.

## Multi-project proving

`tools/prove_multi_project_isolation.py` is a release gate. It deliberately uses colliding task/resource/idempotency identifiers across BenefitFlow and a disposable Project-C fixture in one physical database while racing multiple processes. It must prove duplicate suppression, project-qualified isolation, crash/TTL lease recovery, independent pause behavior, restart durability, and audit/outbox integrity.

The fixture is local test data only. It grants no foreign repository write authority and does not modify Duo Open or another live project.

## Packages and release gate

PRIMARY, MANAGER, and RESEARCH are one coordinated release set. Packages embed/hash the current project/repository identity controls, root routing/communication-awareness/project-factory bootstrap, this protocol, message schema, durable coordination policy/runtime, GitHub write-security policy, proving harness, project guard, role bootstrap, recursive backup snapshot, and required enhancement/kernel context.

`tools/verify_role_package_enhancement_sync.py` verifies source parity, embedded hashes, protocol/project/package versions, exact source revision, repository ID, durable coordination/audit/outbox flags, lifecycle/child-inheritance/ownership flags, communication-awareness/project-factory contracts, and foreign-write denial. Relevant control-plane changes are incomplete while an affected package remains stale or the multi-project proving scenario is red.

## BenefitFlow governance preserved

The P0 architecture gate remains authoritative. Multi-agent hardening does not authorize real member data, credentials, claims submission, live booking adapters, financial actions, or protected external transactions.
