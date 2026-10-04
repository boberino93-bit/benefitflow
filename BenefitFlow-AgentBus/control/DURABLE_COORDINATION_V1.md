# BenefitFlow Durable Coordination V1

Status: **ACTIVE**
Project: `benefitflow`
Protocol: `3.1.0`
Runtime: `benefitflow_beta/durable_store.py` + `benefitflow_beta/durable_coordination.py`

## Purpose

Process-local locks, dictionaries, leases, and idempotency ledgers are useful test primitives but are not sufficient when multiple BenefitFlow agent processes race, restart, or crash. Mutable coordination state that can be touched by more than one process MUST use `DurableCoordinationStore`.

The durable store is bound to `project_id=benefitflow`. It uses SQLite transactions with WAL mode, `BEGIN IMMEDIATE`, full synchronous durability, project-qualified primary keys, and bounded busy waits. The default implementation is intended for multiple local processes using the same local filesystem. It is not a claim that SQLite on an arbitrary network filesystem is a safe multi-host database; a sanctioned transactional database service is required before multi-host production scaling.

## Durable state

The store persists:

- project control mode and version;
- idempotency reservations/results;
- instance-owned leases and expiry;
- versioned project state;
- append-only audit records;
- append-only outbox records;
- append-only outbox delivery receipts.

Every BenefitFlow table is keyed by `project_id`. The production API never accepts a caller-selected foreign project identity. Foreign rows may coexist in the same physical database only as a proving fixture or through separately authorized infrastructure and are never returned as BenefitFlow state.

## Atomic mutation contract

A durable state mutation is one transaction:

1. verify BenefitFlow actor identity;
2. verify project mode is `ACTIVE`;
3. reserve the idempotency key;
4. compare the caller's expected state version;
5. write the new state version;
6. append a hash-linked audit record;
7. append an outbox event when requested;
8. persist the completed idempotent result;
9. commit once.

A stale version, foreign identity, active conflicting lease, paused/read-only mode, or other authorization failure rolls the entire transaction back. Retrying a completed idempotency key returns the original result and does not create another state transition, audit event, or outbox event.

## Lease contract

Durable leases are project-scoped and owned by `agent_instance_id`, not only logical agent ID. Claim, renewal, and release are audited and idempotent. Another instance cannot take an unexpired lease. After TTL expiry, current state must be reread and the lease may be reclaimed. A crashed process cannot retain an immortal lock.

## Project control

Durable project mode is `ACTIVE`, `PAUSED`, or `DEGRADED_READ_ONLY`. Only a BenefitFlow `PRIMARY` identity with explicit human approval may change durable project mode. Mode changes use expected-version compare-and-set and are themselves idempotent/audited.

A BenefitFlow pause applies only to BenefitFlow rows. It cannot pause, resume, or mutate a foreign project.

## Append-only audit and outbox

`audit_log`, `outbox`, and `outbox_delivery` are protected by SQLite triggers that reject update/delete operations. Audit records form a per-project SHA-256 hash chain. Outbox payloads carry canonical SHA-256 hashes.

Delivery does not mutate an outbox event. A consumer writes one append-only delivery receipt keyed by the event. Downstream consumers MUST use the event ID idempotently because no local database can make an arbitrary external side effect transactionally atomic with SQLite.

`verify_integrity()` validates the audit chain and every outbox payload hash.

## Proving requirement

`python tools/prove_multi_project_isolation.py` is a release gate. It uses a disposable `project-c` fixture in the same physical database and deliberately reuses BenefitFlow task/resource/idempotency identifiers. It verifies:

- eight simultaneous BenefitFlow processes produce one effective mutation plus seven safe replays;
- foreign rows with identical human-readable IDs do not collide with BenefitFlow;
- a crashed lease cannot be stolen before TTL and is recoverable after expiry;
- BenefitFlow can pause while Project-C continues;
- idempotency/state survive process restart;
- the audit chain/outbox remain valid.

The fixture never grants Project-C authority over BenefitFlow and never writes to a foreign GitHub repository.

## Deployment rule

`durable_coordination.py`, this contract, the proving harness, and the GitHub write-security policy are shared package dependencies. Any semantic change to durable state, idempotency, leases, audit/outbox, project control, or the proving model requires coordinated PRIMARY/MANAGER/RESEARCH package regeneration and readback verification.
