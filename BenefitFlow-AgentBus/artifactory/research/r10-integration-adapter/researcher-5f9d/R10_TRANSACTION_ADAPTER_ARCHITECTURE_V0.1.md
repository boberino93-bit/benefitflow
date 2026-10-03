# BenefitFlow R10 — Integration and Transaction Adapter Architecture v0.1

**Project:** BenefitFlow (`project_id=benefitflow`)  
**Assignment:** R10 — Integration and Transaction Adapter Architecture  
**Researcher:** `researcher-benefit-semantics-5f9d` (Primary-reassigned to R10)  
**Date:** 2026-10-03  
**Status:** SPECIALIST EVIDENCE / ARCHITECTURAL RECOMMENDATION — NOT ACCEPTED PROJECT STATE  
**Recommended disposition:** `SUPPORTED_FOR_MANAGER_RECONCILIATION`

## 1. Claim / question

What transaction-adapter boundary lets BenefitFlow execute approved booking/calendar/provider actions without collapsing approval, sensitive-data disclosure, transport success, external booking confirmation, calendar projection, retry, and reconciliation into one unsafe state?

The proposed answer is a **provider-independent transaction orchestrator plus narrow capability-declared adapters**. Adapters execute or observe one external system. The orchestrator owns approval validation, disclosure authorization, idempotency identity, state transitions, evidence, reconciliation policy, and human-recovery escalation.

## 2. Inputs and evidence

### Internal project evidence

**P0 — Primary architecture disposition**  
`BenefitFlow-AgentBus/artifactory/primary/20261003-P0_ARCHITECTURE_GATE_DISPOSITION_V1.md`

Accepted architectural requirements include:
- typed/provenanced benefit semantics;
- separation of booking approval from sensitive-field disclosure;
- sensitive-data isolation with opaque workflow references;
- authenticated principals, object authorization, least-privilege service identities and attributable audit events;
- a durable post-approval transaction state machine with idempotency, correlation, authoritative external identifiers, unknown-outcome reconciliation and human recovery;
- mechanically enforceable approval/provider-verification boundaries.

**R4 — Booking confirmation semantics**  
`BenefitFlow-AgentBus/artifactory/research/r4-booking-confirmation/R4_BOOKING_CONFIRMATION_RESEARCH_PACKET_V1.md`

Material dependency:
- request, hold, waitlist, calendar event and confirmed appointment are distinct;
- external mutation needs stable operation identity;
- duplicate/out-of-order webhooks must be tolerated;
- ambiguous mutation timeout enters reconciliation rather than blind retry;
- calendar is a projection, not booking authority;
- reschedule/cancellation need lineage and evidence.

**R5 — Privacy/consent**  
`BenefitFlow-AgentBus/artifactory/research/privacy-consent-regulatory/2026-10-03_R5_completion_packet_v0.1.md`

Material dependency:
- booking approval and disclosure authorization are separate;
- adapter access to raw member/plan identifiers must be purpose/recipient/field/expiry scoped;
- raw identifiers belong behind a restricted secret-store interface;
- unknown compliance mode should fail closed.

**R6 — Voice transaction workflow**  
`BenefitFlow-AgentBus/artifactory/research/r6-voice-phone/R6_VOICE_PHONE_TRANSACTION_RESEARCH_V1.md`

Material dependency:
- telephony transport completion is not booking confirmation;
- retry the transport, not the business transaction;
- any evidence the clinic may have acted creates an ambiguity lock requiring reconciliation before redial;
- counterparty verification and disclosure necessity checks precede sensitive disclosure;
- material term changes require reapproval.

**R9 — Identity/security**  
`BenefitFlow-AgentBus/artifactory/research/r9-identity-security/researcher-r9-identity-security-20261003T2222Z/INITIAL_SECURITY_ARCHITECTURE_FINDINGS.md`

Material dependency:
- every user-owned object/action must be bound to an authenticated principal;
- adapters should have distinct least-privilege service identities;
- approval should become an attributable, expiry-bounded, single-use authorization record;
- sensitive identifier access should use opaque references;
- append-oriented audit/security events are required.

**Current beta code**  
`benefitflow_beta/workflow.py` currently stops at `READY_FOR_TRANSACTION_ADAPTER` and returns a natural-language script. This is the correct prototype boundary, but production safety requires the script’s restrictions to become structured policy/state.

### External technical evidence

#### E1 — Google Calendar create-event semantics
Source: Google Calendar API, “Create events”  
https://developers.google.com/workspace/calendar/api/guides/create-events  
Source quality: first-party technical documentation  
Freshness: current as retrieved 2026-10-03

Observed:
- clients may supply their own event ID;
- Google states this can keep local and remote entities synchronized and prevent duplicate creation after an operation succeeds in the backend but the client experiences failure.

Interpretation:
- calendar projection should use stable projection identity where supported;
- calendar mutation is independently idempotent from provider booking mutation.

#### E2 — Google Calendar incremental synchronization
Source: Google Calendar API, “Synchronize resources efficiently”  
https://developers.google.com/workspace/calendar/api/guides/sync  
Source quality: first-party technical documentation  
Freshness: current as retrieved 2026-10-03

Observed:
- initial full synchronization yields a sync token;
- later incremental synchronization uses the stored token;
- deleted entries are included;
- invalidated tokens can return HTTP 410 and require a new full synchronization.

Interpretation:
- calendar integrations need durable sync cursors and explicit cursor-reset recovery;
- missing webhook delivery must be repairable by read/sync, not only push events.

#### E3 — Google Calendar push notifications
Source: Google Calendar API, “Push notifications”  
https://developers.google.com/workspace/calendar/api/guides/push  
Source quality: first-party technical documentation  
Freshness: current as retrieved 2026-10-03

Observed:
- notification channels have IDs and can have expiration;
- notifications indicate a watched resource changed;
- channel lifecycle must be managed;
- notification message numbers increase but need not be sequential.

Interpretation:
- subscriptions are leased integration resources requiring renewal/health monitoring;
- notification gaps cannot be inferred solely from non-sequential message numbers;
- notification receipt should trigger read/sync rather than be treated as the complete authoritative object state.

#### E4 — Google Calendar optimistic concurrency
Source: Google Calendar API, “Get specific versions of resources”  
https://developers.google.com/workspace/calendar/api/guides/version-resources  
Source quality: first-party technical documentation  
Freshness: current as retrieved 2026-10-03

Observed:
- resources expose `etag`;
- conditional mutation with `If-Match` can prevent lost updates when the resource changed since retrieval.

Interpretation:
- adapters should expose external version/concurrency tokens and map conflicts to reconciliation/re-read, not overwrite.

#### E5 — Microsoft Graph change tracking
Sources:
- https://learn.microsoft.com/en-us/graph/delta-query-overview
- https://learn.microsoft.com/en-us/graph/delta-query-events
Source quality: first-party technical documentation  
Freshness: current as retrieved 2026-10-03

Observed:
- delta query returns incremental additions/updates/deletions with opaque state tokens;
- Microsoft recommends combining change notifications with delta query so push can trigger efficient pull reconciliation.

Interpretation:
- BenefitFlow should treat push and pull as complementary: push for latency, pull/read-back for convergence.

#### E6 — Microsoft Graph change notifications
Source: https://learn.microsoft.com/en-us/graph/change-notifications-overview  
Source quality: first-party technical documentation  
Freshness: current as retrieved 2026-10-03

Observed:
- subscriptions have lifecycle management;
- basic notifications may only identify what changed, requiring the app to fetch the changed resource;
- lifecycle notifications exist for risk of missed notifications.

Interpretation:
- adapter contract needs subscription lease state plus a recoverable synchronization cursor.

#### E7 — Square webhooks
Sources:
- https://developer.squareup.com/docs/webhooks/overview
- https://developer.squareup.com/docs/webhooks/step1createurl
Source quality: first-party technical documentation  
Freshness: current as retrieved 2026-10-03

Observed:
- notifications can be delivered more than once;
- Square tells consumers to deduplicate using `event_id`;
- webhook endpoints should store event data safely and use message versioning.

Interpretation:
- inbound-event deduplication and envelope versioning belong in the integration platform, not ad hoc per business handler.

## 3. Architectural separation

BenefitFlow should model six different concerns separately:

1. **Proposal** — what option BenefitFlow presented.
2. **Approval authorization** — the exact material terms the user approved.
3. **Disclosure authorization** — exact recipient, purpose and sensitive fields that may be released.
4. **Transaction** — BenefitFlow’s durable business intent and normalized external outcome.
5. **Adapter operation** — one mutation/read attempt against one external system.
6. **Projection** — downstream copies such as Google/Microsoft calendar entries.

This prevents dangerous equivalences such as:
- `approved == booked`;
- `HTTP 200 == booked`;
- `call completed == booked`;
- `webhook received == current truth`;
- `calendar event exists == clinic confirmed`;
- `retry == safe to repeat mutation`.

## 4. Recommended component boundary

```text
User/UI
  |
  v
Proposal + Approval Service
  |
  +----> Disclosure Authorization / Secret Vault
  |
  v
Transaction Orchestrator
  |        |             |
  |        |             +--> Append-only Audit/Event Store
  |        +----------------> Reconciliation Scheduler / Human Recovery Queue
  |
  +--> Booking Adapter (provider/booking system)
  +--> Voice Adapter (phone transport/business observation)
  +--> Calendar Projection Adapter
  +--> Future insurer/claim adapter (separately gated; not authorized by booking approval)
```

### Transaction Orchestrator owns

- authenticated actor/account/tenant boundary;
- proposal version/hash and approval validity;
- disclosure-grant validity;
- stable `transaction_id`;
- stable logical `operation_id` for each intended mutation;
- unique `attempt_id` per transport attempt;
- normalized transaction state;
- confirmation evidence threshold;
- adapter capability selection;
- retry policy;
- ambiguity lock;
- reconciliation schedule;
- human-recovery escalation;
- append-only business/audit event emission.

### Adapter owns

- vendor/channel-specific authentication;
- request formatting;
- vendor-specific idempotency/version headers/fields;
- transport execution;
- raw response parsing;
- webhook/signature verification where applicable;
- read-back/query/sync mechanics;
- mapping raw vendor observations into a constrained adapter result envelope.

### Adapter must NOT own

- deciding whether a user approved the action;
- widening permitted provider/service/time/price terms;
- deciding which sensitive fields are legally/contractually permissible to disclose;
- selecting a new provider after failure;
- treating transport success as business confirmation without mapping evidence;
- silently retrying ambiguous business mutations with new idempotency identity;
- submitting claims/payment unless separately authorized by a future distinct workflow.

## 5. Capability-declared adapter contract

Every adapter should publish a descriptor before use.

```json
{
  "adapter_id": "vendor-or-channel-adapter",
  "adapter_version": "semver",
  "channel_type": "DIRECT_TRANSACTIONAL_API",
  "capabilities": {
    "create": true,
    "update": true,
    "cancel": true,
    "status_read": true,
    "webhooks": true,
    "incremental_sync": false,
    "external_idempotency": true,
    "optimistic_concurrency": true,
    "hold": false,
    "waitlist": false
  },
  "confirmation_model": "BOOKING_RESOURCE_STATUS",
  "sensitive_fields_supported": ["member_id_ref", "plan_number_ref"],
  "requires_disclosure_grant": true
}
```

Unsupported capabilities must fail closed before execution.

## 6. Canonical operation request

Recommended conceptual envelope:

```json
{
  "schema": "benefitflow/adapter-operation/v1",
  "transaction_id": "txn_...",
  "operation_id": "op_...",
  "attempt_id": "attempt_...",
  "action": "CREATE_BOOKING",
  "account_id": "opaque-account-ref",
  "proposal_id": "bp_...",
  "proposal_version": "hash-or-version",
  "approval_id": "approval_...",
  "approval_terms_digest": "sha256:...",
  "disclosure_grant_id": "grant_... or null",
  "target": {
    "provider_id": "provider_...",
    "practitioner_id": "optional",
    "service_id": "service_...",
    "location_id": "location_..."
  },
  "requested_terms": {
    "window": "normalized time constraints",
    "price_ceiling": 125.00,
    "timezone": "America/Vancouver"
  },
  "sensitive_payload_lease": "opaque short-lived handle or null",
  "external": {
    "idempotency_key": "stable for same logical mutation",
    "expected_version": "optional"
  },
  "policy_snapshot_id": "policy_...",
  "created_at": "RFC3339"
}
```

### Required invariants

- `transaction_id` remains stable for the booking lifecycle.
- `operation_id` remains stable across retries of the **same logical mutation**.
- `attempt_id` is new for every network/phone attempt.
- changing material intent creates a new operation and may require reapproval.
- `sensitive_payload_lease` must be short-lived, transaction-scoped, field-scoped and recipient/purpose-scoped.
- adapters receive opaque account/workflow references, not broad account-query capability.

## 7. Canonical adapter result

```json
{
  "schema": "benefitflow/adapter-result/v1",
  "transaction_id": "txn_...",
  "operation_id": "op_...",
  "attempt_id": "attempt_...",
  "adapter_id": "adapter-...",
  "result_class": "SUCCEEDED|PENDING|RETRYABLE_FAILURE|FINAL_FAILURE|AMBIGUOUS",
  "external_object_id": "optional",
  "external_parent_id": "optional",
  "external_version": "optional",
  "raw_status": "vendor status",
  "normalized_observation": "REQUEST_SUBMITTED|WAITLISTED|HOLD_ACTIVE|CONFIRMED|CANCELLED|...",
  "confirmation_evidence": [],
  "retry_after": "optional timestamp",
  "read_back_supported": true,
  "reconciliation_required": false,
  "observed_at": "RFC3339"
}
```

Adapters report observations. The orchestrator decides normalized state transitions after validating evidence and policy.

## 8. Transaction state model

Recommended normalized business states:

```text
DRAFT
READY_FOR_EXECUTION
EXECUTING
REQUEST_SUBMITTED
AWAITING_EXTERNAL_CONFIRMATION
HOLD_ACTIVE
WAITLISTED
CONFIRMED_BOOKED
REAPPROVAL_REQUIRED
RESCHEDULE_PENDING
CANCELLATION_PENDING
CANCELLED
REJECTED
FAILED_RETRYABLE
FAILED_FINAL
RECONCILIATION_REQUIRED
HUMAN_RECOVERY_REQUIRED
SUPERSEDED
FULFILLED
```

### Core guarded transitions

| From | Event / condition | To | Guard |
|---|---|---|---|
| DRAFT | approval + policy valid | READY_FOR_EXECUTION | exact proposal digest matches |
| READY_FOR_EXECUTION | mutation begins | EXECUTING | adapter capability + auth + disclosure scope valid |
| EXECUTING | request accepted, not confirmed | REQUEST_SUBMITTED | external evidence retained |
| EXECUTING | authoritative booking confirmation | CONFIRMED_BOOKED | confirmation threshold met |
| EXECUTING | timeout after transmission | RECONCILIATION_REQUIRED | never assume failure |
| REQUEST_SUBMITTED | external confirmed | CONFIRMED_BOOKED | trusted evidence/read-back |
| REQUEST_SUBMITTED | rejected | REJECTED | authoritative evidence |
| any active | material terms differ | REAPPROVAL_REQUIRED | old approval cannot widen |
| any mutation | ambiguous outcome | RECONCILIATION_REQUIRED | automatic duplicate-prone retry blocked |
| CONFIRMED_BOOKED | cancel submitted | CANCELLATION_PENDING | separate operation ID |
| CANCELLATION_PENDING | cancellation confirmed | CANCELLED | authoritative evidence |
| CONFIRMED_BOOKED | reschedule changes material terms | REAPPROVAL_REQUIRED | fresh authority required |
| reconciliation | unresolved beyond policy | HUMAN_RECOVERY_REQUIRED | bounded automation exhausted |

State transitions must be append-only facts with a current-state projection. Late or duplicate external events cannot erase newer verified facts solely because they arrived later.

## 9. Idempotency model

### Identity hierarchy

- `transaction_id`: one user-approved appointment lifecycle.
- `operation_id`: one logical external mutation, e.g. create/cancel/reschedule.
- `attempt_id`: one transport execution attempt.
- `external_idempotency_key`: vendor-compatible stable key derived from `operation_id` where supported.
- `external_event_id`: vendor event identity for inbound deduplication.

### Rules

1. Retrying the same logical mutation reuses `operation_id`.
2. If provider supports idempotency, reuse the same external idempotency key.
3. A timeout after request transmission is **AMBIGUOUS**, not retryable failure.
4. Before another create after ambiguity, read/reconcile by external ID, idempotency key, provider/status lookup or human verification.
5. A genuinely changed intent gets a new operation ID.
6. Reschedule should preserve lineage to the old booking/operation.
7. Cancellation is a compensating business action, not a database rollback.

## 10. Inbound event / webhook inbox

Every inbound notification should first enter a durable inbox.

```text
receive
 -> authenticate/signature-validate
 -> identify adapter/subscription
 -> dedupe trusted event ID
 -> store minimal raw evidence / content hash
 -> map raw event
 -> compare external version/timestamp
 -> optional authoritative read-back
 -> append normalized observation
 -> evaluate transaction transition
 -> acknowledge
```

### Required controls

- reject or quarantine invalid signatures/unknown channels;
- dedupe by `(adapter_id, external_event_id)` when trustworthy;
- do not assume delivery order;
- keep raw vendor status and normalized interpretation separately;
- schema/version-tag inbound envelopes;
- avoid raw member/plan identifiers in general webhook logs;
- rate-limit and isolate webhook endpoints from user-facing APIs.

## 11. Push + pull reconciliation

Push notifications improve latency but are not sufficient for convergence.

Recommended adapter modes:

- `PUSH_ONLY`: allowed only if provider offers authoritative ordered/durable semantics sufficient for the use case; uncommon and should require explicit review.
- `PUSH_PLUS_READBACK`: default for booking systems with webhooks + GET.
- `PUSH_PLUS_DELTA`: ideal for calendar/resource systems exposing change notifications + delta/sync.
- `POLL_READBACK`: fallback when no push exists.
- `HUMAN_RECONCILIATION`: phone/email/manual channels.

A reconciliation job should be triggered by:
- ambiguous timeout;
- invalid/out-of-order/conflicting notification;
- subscription renewal failure;
- missed-notification/lifecycle signal;
- stale pending transaction;
- external version conflict;
- user/provider-reported contradiction;
- periodic safety sweep for open high-value transactions.

## 12. Calendar adapter rules

Calendar integration is a **projection of confirmed or explicitly tentative transaction state**, not the booking source of truth.

### Projection identity

Store:
- `calendar_connection_id`
- `calendar_provider`
- `calendar_id_ref`
- `projection_id`
- `external_event_id`
- `external_version/etag`
- `sync_cursor`
- `subscription/channel_id`
- `subscription_expires_at`
- `last_sync_at`
- `projection_state`

Where the calendar API permits client-generated IDs, derive a stable non-sensitive projection ID from the BenefitFlow transaction identity.

### Projection states

`NOT_PROJECTED -> CREATE_PENDING -> PROJECTED -> UPDATE_PENDING -> PROJECTED`

Exceptional:
- `PROJECTION_CONFLICT`
- `PROJECTION_RECONCILIATION_REQUIRED`
- `PROJECTION_DELETED_EXTERNALLY`
- `PROJECTION_FAILED`

Calendar projection failures must not downgrade a provider-confirmed booking. They create a calendar-sync problem, not a booking-state problem.

### External calendar edits

If a user edits/deletes a projection directly:
- do not mutate clinic booking automatically unless that behavior was separately authorized;
- reconcile the calendar object;
- surface divergence;
- offer an explicit BenefitFlow cancellation/reschedule workflow.

## 13. Subscription/cursor lifecycle

Integration state is durable operational state.

Store per subscription/sync target:
- external subscription/channel ID;
- resource ID;
- expiration;
- secret/token reference;
- cursor/delta/sync token;
- last successful notification;
- last successful reconciliation;
- renewal attempt/result;
- terminal invalidation reason.

Treat subscription expiry/renewal as a monitored SLO. If a cursor is invalidated (e.g. Google Calendar HTTP 410), perform a bounded full resynchronization and rebuild the cursor without interpreting absence of events during the gap as cancellation.

## 14. Concurrency

Adapter contract should surface external version tokens where available.

On optimistic concurrency conflict:
1. do not overwrite blindly;
2. read current external object;
3. compare against approved/intended state;
4. if semantically equivalent, converge local state;
5. if materially different, enter `REAPPROVAL_REQUIRED` or `RECONCILIATION_REQUIRED`;
6. persist both expected and observed version evidence.

## 15. Error taxonomy

| Class | Examples | Automatic retry? | Safe normalized handling |
|---|---|---:|---|
| `POLICY_BLOCK` | approval expired, disclosure scope missing | No | stop / reapproval |
| `AUTHENTICATION_FAILURE` | expired vendor token | After credential refresh policy | no business mutation retry until auth fixed |
| `AUTHORIZATION_FAILURE` | insufficient external scope | No blind retry | operator/config remediation |
| `VALIDATION_FAILURE` | malformed request, unsupported field | No | final/config error |
| `CAPABILITY_MISMATCH` | adapter cannot cancel/read status | No | alternate approved channel or human |
| `NOT_FOUND` | provider/booking resource missing | Maybe after read reconciliation | reconcile identity/state |
| `AVAILABILITY_CONFLICT` | slot taken | Yes only as new approved selection | not booked |
| `RATE_LIMITED` | HTTP 429 | Yes with vendor retry policy | preserve same operation |
| `TRANSIENT_TRANSPORT` | connect failure before transmit | Yes | bounded same operation |
| `AMBIGUOUS_TIMEOUT` | timeout after transmit | No mutation retry | reconciliation required |
| `CONCURRENCY_CONFLICT` | ETag/version mismatch | No blind retry | read-back/reconcile |
| `DUPLICATE_EVENT` | repeated webhook event_id | No processing repeat | ignore after evidence record |
| `OUT_OF_ORDER_EVENT` | stale external version | No rollback | ignore/reconcile |
| `WEBHOOK_AUTH_FAILURE` | invalid signature/channel | No | quarantine/security event |
| `SCHEMA_DRIFT` | unknown status/payload version | No unsafe mapping | quarantine + reconciliation |
| `EXTERNAL_SEMANTIC_UNKNOWN` | vendor “created” meaning unclear | No | pending/manual review |
| `SENSITIVE_DATA_BLOCK` | requested fields exceed grant | No | stop + user approval if appropriate |
| `CALENDAR_PROJECTION_FAILURE` | event insert/update failure | bounded projection retry | booking state unchanged |
| `HUMAN_CHANNEL_AMBIGUITY` | phone says “we’ll call back” | No duplicate-prone retry | pending/manual |
| `EXTERNAL_IRREVERSIBLE_ACTION` | claim/payment accidentally requested | No | critical incident/human recovery |

## 16. Retry policy

Retry policy is a function of **failure class + side-effect certainty**, not merely HTTP code.

Safe automatic retry examples:
- pre-connect transport failure;
- explicit throttling where provider documents retry behavior;
- calendar projection mutation with stable projection identity;
- read-only reconciliation query.

Unsafe automatic retry examples:
- booking create timeout after bytes may have reached provider;
- phone disconnect after clinic indicated it was booking;
- cancellation timeout where booking might already be cancelled;
- any mutation after approval expired/material terms changed.

Retries must be bounded by:
- attempt count;
- wall-clock expiry;
- provider hours/channel policy;
- exponential backoff/jitter where appropriate;
- user preference;
- operation deadline.

## 17. Compensation and “rollback”

Distributed external transactions often cannot be rolled back atomically.

BenefitFlow should use **compensating actions**, each separately authorized and evidenced:
- cancel confirmed booking;
- reschedule via linked replacement operation;
- delete/update calendar projection;
- revoke unused disclosure lease;
- mark stale request superseded.

Never report “rolled back” until the external system confirms the compensating action. Unknown compensation outcome enters reconciliation.

Claims submission/payment are outside the current booking authorization and require separate future workflows; they must not be treated as routine compensation.

## 18. Human recovery contract

Human recovery is a first-class product path, not an exceptional debugging escape hatch.

A recovery case should show:
- transaction ID and account-scoped owner;
- exact approved material terms digest;
- disclosure grant status without raw secret values;
- chronological append-only event/evidence timeline;
- current normalized state and why automation stopped;
- external object IDs/reference numbers;
- adapter/channel and version;
- last successful authoritative read-back;
- ambiguity/error class;
- safe permitted actions;
- actions requiring user reapproval;
- duplicate-risk warning;
- correlation IDs for logs.

Permitted recovery actions should themselves generate audited operations, not direct database edits.

Examples:
- “check provider status again”;
- “mark confirmed using verified human evidence”;
- “request user reapproval for changed time/price/provider”;
- “initiate cancellation operation”;
- “link duplicate/superseded transactions”;
- “close as unresolved after user/provider confirmation.”

## 19. Observability

### Correlation dimensions

Every log/metric/trace should carry non-sensitive:
- `transaction_id`
- `operation_id`
- `attempt_id`
- `adapter_id`
- `adapter_version`
- `channel_type`
- `normalized_state`
- `error_class`
- `reconciliation_case_id` when applicable

### Metrics

- mutation success rate by adapter/channel;
- ambiguous-outcome rate;
- confirmation latency;
- pending-age distribution;
- retries per operation;
- duplicate webhook rate;
- stale/out-of-order event rate;
- reconciliation success and time-to-converge;
- subscription renewal failure rate;
- calendar projection divergence;
- human-recovery volume and resolution time;
- reapproval-trigger rate.

Do not use member/plan IDs, free-form transcripts, diagnoses, or raw secret payloads as metric labels.

## 20. Security/privacy boundary for adapters

Recommended design:
- separate service identity per adapter class/environment;
- least-privilege external OAuth/API scopes;
- secrets in managed secret/KMS boundary;
- short-lived secret payload leases from a sensitive-data service;
- lease audience bound to adapter + transaction + recipient + field set;
- adapter cannot enumerate vault contents;
- raw secret values are not returned to orchestrator logs;
- webhook endpoints use independent authentication/signature verification;
- calendar adapter does not inherit booking/insurance secret access unless strictly required.

This operationalizes R5/R9 rather than relying on prompt instructions.

## 21. Adapter conformance tests

### Authorization/disclosure

1. Expired approval cannot execute.
2. Changed proposal digest cannot execute under old approval.
3. Booking approval without disclosure grant cannot retrieve restricted identifiers.
4. Provider-A disclosure grant cannot be used by Provider-B operation.
5. Adapter cannot request fields outside lease.

### Idempotency/ambiguity

6. Same operation retried reuses external idempotency identity.
7. Pre-transmit connect failure may retry with new attempt ID.
8. Post-transmit timeout becomes reconciliation, not a new create.
9. Reconciliation finds existing booking and prevents duplicate.
10. Duplicate webhook event is applied once.

### Ordering/concurrency

11. Older external version after newer version cannot roll state backward.
12. ETag/version conflict causes read-back before mutation retry.
13. Unknown vendor status cannot silently map to confirmed.

### Confirmation semantics

14. Request submitted cannot become confirmed without evidence threshold.
15. Waitlist/hold cannot become confirmed.
16. Calendar event existence cannot become confirmed booking.
17. Telephony call-completed cannot become confirmed booking.
18. Provider read-back confirming booking may promote to confirmed.

### Cancellation/reschedule

19. Cancellation request stays pending until confirmation.
20. Reschedule links old/new transaction/external IDs.
21. Material reschedule change requires reapproval.
22. Ambiguous cancellation timeout enters reconciliation.

### Calendar

23. Stable projection ID prevents duplicate event on retry.
24. External calendar deletion creates projection divergence, not clinic cancellation.
25. Expired notification subscription triggers renewal/reconciliation.
26. Invalid sync cursor triggers bounded full resync.
27. Calendar version conflict does not overwrite user changes silently.

### Human recovery/security

28. Recovery user cannot directly edit state without an audited action.
29. Recovery action outside user authority requires reapproval.
30. Ordinary logs contain no raw member/plan identifiers.

## 22. Proposed implementation sequence

### P0 — before any live booking adapter
1. `Transaction`, `Operation`, `Attempt`, and append-only `TransactionEvent` primitives.
2. Approval digest/expiry validation and separate disclosure authorization.
3. Adapter descriptor/capability negotiation.
4. Stable operation identity and ambiguity lock.
5. Confirmation evidence model.
6. `RECONCILIATION_REQUIRED` + human-recovery queue.
7. Least-privilege adapter service identity and secret lease boundary.
8. Conformance tests 1–22.

### P1 — first direct API/calendar integrations
1. Inbox/webhook verification + deduplication.
2. Out-of-order/version-aware read-back.
3. Subscription/cursor lease state.
4. Calendar projection model + deterministic projection identity.
5. Periodic reconciliation scheduler.
6. Conformance tests 23–30.

### P2 — operational maturity
1. Recovery console.
2. Adapter reliability scorecards.
3. Dead-letter/quarantine workflow for schema drift.
4. Integration SLOs and alerting.
5. Replay-safe event migration/versioning.

## 23. Contradictions / unresolved unknowns

### U1 — exact adapter deployment topology
Evidence supports least privilege, but does not determine whether adapters must be separate processes, containers, serverless functions, or a modular monolith. Separate service identities are more important than a specific packaging choice.

### U2 — exact confirmation evidence threshold per vendor
A Square/Microsoft-style booking resource may support strong mapping; phone/email/request forms require different evidence. R10 should not universalize one vendor status.

### U3 — commercial/API access
Public documentation demonstrates technical semantics, not BenefitFlow’s contractual right to use each vendor API.

### U4 — insurer/claims adapters
This packet defines architectural boundaries only. Current booking approval does not authorize claim submission, coverage adjudication or payment.

### U5 — retention durations
R5 establishes the need for retention governance but not exact durations. Adapter evidence should carry a retention class, with durations set by accepted policy.

### U6 — calendar provider choice
Google/Microsoft evidence supports synchronization patterns, not a project decision to support either provider first.

## 24. What this research does NOT establish

- It does not authorize live external booking.
- It does not accept any class/enum/table names as project truth.
- It does not authorize disclosure of member/plan identifiers to research agents.
- It does not claim webhook delivery is reliable or ordered across vendors.
- It does not claim calendar state is provider booking state.
- It does not establish that all external mutations are reversible.
- It does not determine legal compliance for every jurisdiction.
- It does not select a telephony, calendar, booking, insurer, cloud, database or queue vendor.

## 25. Recommended manager disposition

`SUPPORTED_FOR_ARCHITECTURAL_INTEGRATION`, with implementation naming reserved to Primary.

The P0 requirement should be expressed as:

> BenefitFlow’s post-approval execution layer must use durable transaction/operation identity, capability-limited adapters, separate disclosure authorization, evidence-based confirmation, side-effect-aware retry semantics, authoritative read-back reconciliation, append-only audit events, and explicit human recovery. Calendar and webhook integrations are synchronization/projection mechanisms, not standalone booking authority.

No accepted project state was modified by this researcher.
