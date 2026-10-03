# BenefitFlow AgentBus Message Protocol V2

Protocol version: `2.0.0-alpha.1`.

Every new Protocol 2 internal message must explicitly carry sender/destination/task project identity; logical and execution-instance agent identity; message/correlation/causation/idempotency identifiers; sequence; created/expiry time; priority; required capabilities; project-owned artifact references; payload; and a deterministic payload hash.

Internal routing is BenefitFlow-only. A foreign destination or artifact is rejected. Cross-project exchange uses the separate capability/approval boundary.

Message delivery and execution are distinct. Acknowledgement outcomes include `RECEIVED`, `ACCEPTED`, `STARTED`, `COMPLETED`, `FAILED`, `REJECTED`, `QUARANTINED`, `EXPIRED`, `DUPLICATE`, `UNAUTHORIZED`, and `PROTOCOL_MISMATCH`.

Idempotency claims are project-scoped and atomically created before message publication so concurrent retries have one effective publication. Invalid payloads are preserved in the project-scoped quarantine path and are not executed.

## Active v1 migration

Existing immutable `benefitflow-agentbus/v1` forum messages remain historical truth. Agents already holding a v1 task claim at cutover may finish that existing task. They may not use legacy format to obtain new post-cutover claims or new authority. New agents/tasks use Protocol 2 packages. Legacy findings require Manager/Primary review and normalization before promotion into Protocol 2 accepted state.
