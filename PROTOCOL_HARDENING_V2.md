# BenefitFlow Protocol 2 Hardening

BenefitFlow treats `project_id` as an authorization boundary, not descriptive metadata.

## Canonical operation identity

`organization -> project_id -> repository/workspace -> agent_id -> agent_instance_id -> task/lease -> resource`

Human-readable aliases can repeat across projects; canonical identity cannot.

## Agent lifecycle

`CREATED -> UNBOUND -> PROJECT_RESOLUTION -> BOUND(project_id) -> INITIALIZED -> ACTIVE -> DRAINING/PAUSED -> TERMINATED`

UNBOUND agents may inspect only identity-resolution metadata and may not mutate repositories, messages, tasks, artifacts, state, leases, packages, approvals, or external systems.

## Internal messages

Protocol `2.0.0-alpha.1` requires explicit sender/destination/task project identity, execution-instance identity, task lineage, correlation/causation, idempotency, sequence, TTL, capability requirements, project-owned artifact references, and payload integrity hash. Internal BenefitFlow routing cannot cross project boundaries.

Malformed, expired, foreign, unauthorized, ambiguous, or protocol-incompatible messages are rejected or quarantined with evidence preserved.

## Concurrency and recovery

- Message publication uses project-scoped atomic idempotency claims.
- Mutable state uses compare-and-set version checks plus atomic replacement.
- Work ownership uses project-scoped expiring leases tied to agent execution instance.
- Expired leases are recoverable; restarted agents do not automatically inherit prior instance leases.
- Artifact versions are immutable and project-owned.
- Recursive AgentBus backup/controller succession remains in force.

## Cross-project exchange

Cross-project exchange never uses ordinary AgentBus routing. It requires an explicit exchange request and a trusted project-owned grant bound to agent execution instance, source/destination, artifact scope, allowed use, approval identity, and expiry. Data crosses by value with provenance.

## BenefitFlow-specific governance

Research and planning remain distinct from recommendation and transaction execution. PRIMARY/MANAGER/RESEARCH role packages do not receive `external_action`, `cross_project_exchange`, or `deploy` by default. Live booking, financial action, claims submission, or full member identifier disclosure cannot be authorized merely by an internal message.

## Deployment integrity

PRIMARY, MANAGER, and RESEARCH ZIPs are built as one coordinated release set from an exact Git commit SHA. Each ZIP contains a machine-readable deployment manifest, component hashes, shared current protocol/runtime files, and only its role-specific bootstrap contract. CI validates project/role/protocol/framework/package/source-revision consistency and prohibited foreign-project content.
