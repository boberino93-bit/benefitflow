# BenefitFlow Multi-Project Protocol V3

Status: ACTIVE
Project: `benefitflow`
Protocol: `3.0.0`

## Security boundary

`project_id` is an authorization boundary, not descriptive metadata. BenefitFlow execution is bound to `boberino93-bit/benefitflow` and `/project/benefitflow/*`. Missing, conflicting, or foreign project identity fails closed. Ordinary AgentBus/forum channels never carry cross-project commands. Any future cross-project exchange must use a separately authorized, sanitized, copy-by-value bridge with provenance.

## Agent binding

An operational agent has a logical `agent_id` and an execution-scoped `agent_instance_id`. Before mutation it MUST be bound to exactly one `project_id`. Child agents inherit the parent's project identity; conflicting child identity is rejected. Restarted instances do not inherit instance-owned locks or leases.

## Message contract

New executable messages use protocol `3.0.0` and include:

- `protocol_version`, globally collision-resistant `message_id`, `correlation_id`, `causation_id`, and `idempotency_key`;
- sender `project_id`, `agent_id`, `agent_instance_id`, and role;
- destination `project_id`, optional agent, and project-qualified channel;
- task identity;
- message type and sequence;
- timezone-aware creation and expiry timestamps;
- priority and required capabilities;
- project-qualified artifact references;
- payload plus SHA-256 payload hash.

The receiver validates caller/session identity, project ownership, protocol, required capabilities, TTL, structure, and integrity before execution. Outcomes are explicit: `ACCEPTED`, `REJECTED`, `QUARANTINED`, `EXPIRED`, `DUPLICATE`, `UNAUTHORIZED`, or `PROTOCOL_MISMATCH`.

Historical V1/V2 forum records remain immutable evidence. They are not automatically executable as V3 commands.

## Concurrency and replay

Retried mutations require an idempotency key. Work that can be claimed by multiple agents uses a project-qualified lease with holder instance and expiry. Expired leases are recoverable. Version-sensitive state changes require the caller's expected version; stale writes fail rather than overwriting newer state.

## Capabilities

Primary, Manager, and Research roles receive different capability sets. Communication does not imply authorization. External/transactional operations, financial actions, sensitive member/plan identifier disclosure, deployment, and material booking-term changes remain behind explicit human-approval boundaries where applicable.

## Repository and artifacts

All mutating operations validate the BenefitFlow project and repository binding before write. Artifact, task, message, lock, lease, and package identifiers are project-qualified internally. Foreign project mutation is denied by default.

## Packages

The canonical project manifest is `control/PROJECT_MANIFEST.json`. Primary, Manager, and Research packages MUST embed the current manifest, this protocol, role bootstrap, coordination runtime, and required shared control files. Package verification compares embedded files to source by SHA-256 and validates project/protocol/package versions. Relevant protocol/control-plane changes require all three role packages to be rebuilt as one release set.

## BenefitFlow governance preserved

Research produces evidence; Manager reviews/recommends; Primary accepts and integrates project truth; explicit human approval remains required for protected transactional/external actions. Multi-agent autonomy never weakens those boundaries.
