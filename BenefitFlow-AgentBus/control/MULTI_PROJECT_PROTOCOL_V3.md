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

## Repository and concurrency

All source mutations validate project identity, exact repository name, stable repository ID when supplied, canonical path, and AgentBus namespace through `benefitflow_beta/project_guard.py`. Retryable work uses project-scoped idempotency. Claimable work uses project-scoped expiring leases tied to `agent_instance_id`, with holder-only renewal/release and crashed-instance cleanup. Version-sensitive writes use expected-version compare-and-set; stale writes fail.

## Capabilities, project control, and governance

Primary, Manager, and Research have distinct least-privilege capabilities. Research produces evidence; Manager reviews/recommends; Primary integrates accepted truth. Protected external/financial actions, sensitive identifier disclosure, deployment, material booking-term changes, project-control changes, and cross-project exchange remain behind explicit human approval where applicable. BenefitFlow can be independently `ACTIVE`, `PAUSED`, or `DEGRADED_READ_ONLY` without stopping unrelated projects.

## Packages and release gate

PRIMARY, MANAGER, and RESEARCH are one coordinated release set. Packages embed/hash the current project/repository identity controls, root routing/communication-awareness bootstrap, this protocol, message schema, coordination/project-guard runtime, role bootstrap, recursive backup snapshot, and required enhancement/kernel context. `tools/verify_role_package_enhancement_sync.py` verifies source parity, embedded hashes, protocol/project/package versions, exact source revision, repository ID, lifecycle/child-inheritance/ownership flags, communication-awareness contract, and foreign-write denial. Relevant control-plane changes are incomplete while an affected package remains stale.

## BenefitFlow governance preserved

The P0 architecture gate remains authoritative. Multi-agent hardening does not authorize real member data, credentials, claims submission, live booking adapters, financial actions, or protected external transactions.
