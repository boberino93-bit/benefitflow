# BenefitFlow Beta Architecture — Protocol 2 Hardening

## Product boundary

BenefitFlow converts a user's extended-benefits package, priorities, and annual out-of-pocket budget into an evidence-backed utilization plan, provider verification workflow, exact booking proposal, and **user-approved** transaction handoff.

`benefits input -> evidence-backed parsing -> normalized coverage rules -> budget/priorities -> optimizer -> provider research -> provider/direct-billing verification -> exact booking proposal -> user approval -> bounded transaction adapter`

The communications/control-plane upgrade does not expand product transaction authority.

## Canonical project identity

Canonical project identity is `project_id=benefitflow`; canonical repository is exactly `boberino93-bit/benefitflow`. `PROJECT_MANIFEST.json` is the root identity/version manifest. Project-specific communications, evidence, artifacts, control records, leases, tasks, audit, and recovery data remain BenefitFlow-owned.

Project identity is an authorization boundary. No mutable operation may rely on inferred or ambient project context.

## Agent binding

Agents follow:

`CREATED -> UNBOUND -> PROJECT_RESOLUTION -> BOUND(benefitflow) -> INITIALIZED -> ACTIVE -> DRAINING/PAUSED -> TERMINATED`

UNBOUND agents cannot mutate. Child agents inherit parent project/repository/protocol/package identity and receive a fresh execution-instance ID. A restarted agent therefore does not silently inherit stale instance-owned leases.

## Internal AgentBus Protocol 2

Every internal message carries explicit sender/destination/task project identity, execution-instance identity, correlation/causation, idempotency key, sequence, TTL, capability requirements, artifact references, and payload integrity hash.

Ordinary AgentBus messages are intra-project only. Foreign project routing, foreign artifacts, expired commands, malformed envelopes, ambiguous identity, and protocol mismatches are rejected or quarantined rather than repaired by inference.

Acknowledgement state distinguishes delivery from execution: `RECEIVED`, `ACCEPTED`, `STARTED`, `COMPLETED`, `FAILED`, `REJECTED`, plus safety outcomes such as `QUARANTINED`, `EXPIRED`, `DUPLICATE`, `UNAUTHORIZED`, and `PROTOCOL_MISMATCH`.

## Concurrency

- Atomic project-scoped idempotency claims prevent duplicate message execution.
- Expiring leases bind work ownership to `agent_instance_id`; expired work is recoverable.
- Compare-and-set state mutation rejects stale writes.
- Artifact versions are immutable records with project ownership and provenance.
- Project/resource paths are canonicalized before authorization.

## Cross-project exchange

Cross-project communication is not a mode of the ordinary bus. It is a separate deny-by-default exchange boundary. A request requires a trusted project-owned capability grant bound to the requesting execution instance, source/destination projects, purpose/allowed use, artifact scope, approval identity, and expiry. Imports are copy-by-value and preserve provenance.

The Intercommunications Enhancements repository is an upstream protocol reference only. BenefitFlow does not write to it.

## Authority chain

`Human -> Primary -> Manager/Reviewer -> Research/Specialist`

PRIMARY is ORCHESTRATOR; MANAGER is REVIEWER; RESEARCH is SPECIALIST. Role naming never self-elevates authority.

Research and planning remain distinct from recommendation and transactional action. No packaged role receives `external_action`, `cross_project_exchange`, or `deploy` by default. Explicit user confirmation remains mandatory before booking, financial action, claims submission, or disclosure of full member/plan identifiers outside the approved transaction scope.

## Deployment packages

PRIMARY, MANAGER, and RESEARCH deployment ZIPs are generated from the exact same Git source revision as one coordinated release set. They share current protocol/runtime files but carry distinct role bootstraps and capability sets. Each ZIP declares project/repository/role/authority/project/framework/protocol/package/source versions plus component hashes.

CI runs product and hardening tests, retained framework tests, package build, package validation, foreign-project-content checks, and release-set consistency before uploading the three ZIPs and `RELEASE_SET.json`.

## Recursive recovery

Existing BenefitFlow recursive recovery remains authoritative for controller continuation: append-only message persistence, complete AgentBus snapshots, SHA-256 manifests, successor revalidation, and live-delta reconciliation. Protocol 2 adds project-scoped leases/state/message safety; it does not replace persisted-truth recovery with autonomous leader election.

## Research boundary

The R&D round is active by explicit user instruction. The gate remains authoritative. Protocol 2 uses a non-destructive migration: v1 agents already holding claims may finish those claims and publish immutable legacy evidence, but new agents/new claims after cutover require current Protocol 2 packages. Legacy findings must be reviewed/normalized before promotion into Protocol 2 accepted state.
