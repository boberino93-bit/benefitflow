# BenefitFlow R4 Evidence Packet v2 — Implementation Gaps and Reconciliation Hardening

Project: `BenefitFlow` (`project_id=benefitflow`)
Role: Research specialist — evidence/proposals only
Assignment: `R4 — Booking Channels and Confirmation Semantics`
Research date: 2026-10-03
Status: RESEARCH EVIDENCE / NOT ACCEPTED STATE

## Why this packet exists

A second R4 researcher independently published a strong channel-taxonomy packet at nearly the same time as this researcher. Rather than duplicate that work, this packet narrows to the complementary question:

> Given the current BenefitFlow beta code and the observed semantics of real booking systems, what concrete state, persistence, reconciliation, API, and test gaps must be closed before a transaction adapter can safely represent appointment outcomes?

This packet does not replace either R4 evidence stream. It is a delta focused on implementation consequences and integration correctness.

---

## 1. Current BenefitFlow beta observations

### B1 — Approval is correctly separated from external execution, but transaction state does not yet exist

Current `benefitflow_beta/workflow.py` returns:

- `DECLINED` when the user rejects the proposal.
- `READY_FOR_TRANSACTION_ADAPTER` when the user approves.

This is a sound authorization boundary: approval does not pretend that an appointment has been booked.

However, the current model has no durable object representing the external transaction after handoff. There is no explicit persisted state for:

- transaction started,
- external request submitted,
- provider acceptance pending,
- slot held,
- waitlisted,
- confirmed,
- cancellation pending,
- reschedule pending,
- ambiguous timeout,
- reconciliation required,
- superseded booking,
- final cancellation.

**Implementation implication:** production should introduce a transaction record rather than overloading `BookingResult`.

### B2 — Provider channel vocabulary is too coarse

Current `Provider.booking_channel` is limited to:

- `phone`
- `web`
- `manual`

Observed vendor behavior shows that `web` can mean materially different things:

- first-party transaction API,
- hosted booking page,
- appointment request form,
- waitlist flow,
- aggregator redirect,
- authenticated patient portal,
- read-only availability surface.

**Implementation implication:** the provider record needs capability metadata rather than a single generic channel label.

### B3 — Current tests validate the authorization boundary but do not validate transaction truth

Current `tests/test_workflow.py` correctly asserts that user approval produces `READY_FOR_TRANSACTION_ADAPTER` and that materially changed terms require renewed approval in the generated script.

There are no tests yet for:

- transport timeout after an external create,
- duplicate retry prevention,
- pending provider acceptance,
- waitlist vs confirmed distinction,
- slot hold expiry,
- provider-side mutation after approval,
- cancellation response with no body,
- reschedule partial failure,
- webhook replay/out-of-order delivery,
- stale availability,
- authoritative read-back reconciliation.

---

## 2. Additional observed evidence

### E10 — Microsoft Bookings create returns an appointment object with a stable ID

**Source:** Microsoft Graph v1.0 — Create bookingAppointment
https://learn.microsoft.com/en-us/graph/api/bookingbusiness-post-appointments?view=graph-rest-1.0

Observed:
- `POST /solutions/bookingBusinesses/{id}/appointments` creates a `bookingAppointment`.
- A successful call returns HTTP `201 Created` and a `bookingAppointment` object.
- The appointment object has an `id` and concrete appointment properties.

**Interpretation:** API-backed adapters can often return an authoritative external identifier immediately. BenefitFlow should persist the external appointment ID before presenting the result as confirmed.

**Confidence:** High.

### E11 — Microsoft Bookings supports independent read-back of a booking object

**Source:** Microsoft Graph v1.0 — Get bookingAppointment
https://learn.microsoft.com/en-us/graph/api/bookingappointment-get?view=graph-rest-1.0

Observed:
- `GET /solutions/bookingBusinesses/{id}/appointments/{id}` returns the appointment object.
- The resource can be read independently after creation.

**Interpretation:** where an adapter supports authoritative read-back, BenefitFlow should prefer create -> persist external ID -> read/reconcile rather than treating the transport response as the only confirmation evidence.

**Confidence:** High.

### E12 — Microsoft Bookings cancellation returns 204 with no response body

**Source:** Microsoft Graph v1.0 — bookingAppointment: cancel
https://learn.microsoft.com/en-us/graph/api/bookingappointment-cancel?view=graph-rest-1.0

Observed:
- cancellation uses a separate `POST .../cancel` operation.
- success returns HTTP `204 No Content`.
- the successful response contains no appointment body.

**Interpretation:** a successful mutation response can provide weaker post-state evidence than a create/read response. For external systems with this pattern, BenefitFlow should mark cancellation as acknowledged and perform read-back/event reconciliation when the adapter can do so. `204` proves the server accepted/completed the cancellation operation according to that API; it does not supply a post-cancellation booking object for local comparison.

**Confidence:** High.

### E13 — Microsoft Bookings notification preference is independent of appointment existence

**Source:** Microsoft Graph v1.0 — bookingAppointment resource type
https://learn.microsoft.com/en-us/graph/api/resources/bookingappointment?view=graph-rest-1.0

Observed:
- the appointment resource contains appointment state/details independently of notification properties.
- `optOutOfCustomerEmail` controls whether the customer wants a confirmation email.
- `smsNotificationsEnabled` controls SMS notifications.

**Interpretation:** confirmation-message delivery is not canonical appointment truth. A valid appointment may exist even when email confirmation is disabled. This independently corroborates the Jane grace-period finding from R4 v1.

**Confidence:** High.

### E14 — Microsoft Bookings enforces business/scheduling rules around API mutations

**Source:** Microsoft Graph — Business rules for Bookings appointments
https://learn.microsoft.com/en-us/graph/bookingsbusiness-business-rules

Observed:
- API-created/updated appointments must respect business-level and service-level rules.
- business hours and scheduling policy constrain successful mutations.

**Interpretation:** discovery-time availability is not sufficient to guarantee that a later mutation remains valid. Adapter execution must expect rule-based rejection and treat it as a normal deterministic failure, not as evidence of system inconsistency.

**Confidence:** High.

### E15 — Calendly reschedule emits cancellation of the old invitee plus creation of the replacement

**Source:** Calendly Developer Documentation — Webhook Payloads for Rescheduled Events
https://developer.calendly.com/docs/api-guides/see-how-webhook-payloads-change-when-invitees-reschedule-events

Observed:
- rescheduling triggers both `invitee.canceled` and `invitee.created`.
- the canceled payload identifies the old invitee and marks it rescheduled.
- the created payload contains the active replacement.
- old/new invitee references can connect the two records.

**Interpretation:** reschedule should be modeled as a relationship between separately addressable booking records, not merely an in-place timestamp change.

**Confidence:** High.

### E16 — Square create uses an explicit idempotency key

**Source:** Square Bookings API — Create booking
https://developer.squareup.com/reference/square/bookings-api/create-booking

Observed:
- create-booking accepts an `idempotency_key` explicitly documented as making the request idempotent.

**Interpretation:** BenefitFlow should create and persist logical-operation identity before sending an external write. Adapters that support provider idempotency should derive/reuse their external idempotency token from that durable operation identity.

**Confidence:** High.

### E17 — Jane waitlist exclusive access is a hold-like state, not a user-specific confirmed booking

**Sources:**
- https://jane.app/guide/setting-up-your-wait-list-notifications
- https://jane.app/guide/using-wait-list-notifications

Observed:
- Jane can hold a canceled/moved slot for eligible waitlist clients for an exclusive-access period.
- multiple eligible clients can be notified.
- the held slot can later be released or explicitly booked for one client.

**Interpretation:** `SLOT_HELD` must record *who/what the hold protects*. A generic hold flag is insufficient. A provider-level hold that gives a cohort exclusive access is not equivalent to a patient-specific reservation.

**Confidence:** High.

---

## 3. Recommended production data model

The following is a proposal for Primary/Manager review, not accepted design.

### 3.1 Preserve authorization as its own object

Current proposal/approval logic should remain conceptually separate.

Recommended fields to add to the authorization record:

- `authorization_id`
- `proposal_id`
- `authorization_version`
- `approved_at`
- `approved_provider_id`
- `approved_service_category`
- `approved_practitioner_id` if material
- `approved_location_id` if material
- `approved_time_window`
- `approved_price_ceiling` or exact expected price where applicable
- `approved_cancellation_terms_hash`
- `approved_transaction_capabilities` (create/request/handoff/etc.)

Any materially changed terms should require a new authorization version.

### 3.2 Introduce `BookingTransaction`

Suggested conceptual fields:

- `transaction_id`
- `authorization_id`
- `provider_id`
- `adapter_id`
- `channel_type`
- `state`
- `created_at`
- `updated_at`
- `last_reconciled_at`
- `reconciliation_deadline`
- `external_system`
- `external_booking_id`
- `external_version`
- `replacement_transaction_id`
- `supersedes_transaction_id`
- `confirmation_evidence_level`
- `confirmation_evidence_ref`
- `failure_code`
- `human_recovery_required`

### 3.3 Introduce durable `TransactionOperation`

Each external mutation should be separately persisted:

- `operation_id`
- `transaction_id`
- `operation_type` = create / cancel / reschedule / update / waitlist / verify
- `logical_operation_key`
- `external_idempotency_key`
- `attempt_number`
- `request_started_at`
- `response_received_at`
- `transport_outcome`
- `external_http_status` where applicable
- `external_correlation_id`
- `precondition_external_version`
- `postcondition_external_version`
- `result_classification`

This provides the minimum substrate for safe retries, auditability, and ambiguous-outcome recovery.

---

## 4. Recommended normalized transaction states

The beta should not necessarily expose all of these to the user, but the adapter layer should distinguish them.

### Pre-execution

- `NOT_STARTED`
- `AVAILABILITY_OBSERVED`
- `AUTHORIZED`

### In-flight / nonterminal

- `TRANSACTION_IN_FLIGHT`
- `HOSTED_HANDOFF_ACTIVE`
- `REQUEST_SUBMITTED`
- `PENDING_PROVIDER_ACCEPTANCE`
- `WAITLISTED`
- `SLOT_HELD_PROVIDER_SCOPE`
- `SLOT_HELD_PATIENT_SCOPE`
- `CONFIRMATION_PENDING_RECONCILIATION`
- `CANCELLATION_PENDING`
- `RESCHEDULE_PENDING`
- `UNKNOWN_RECONCILIATION_REQUIRED`

### Terminal / stable

- `CONFIRMED`
- `DECLINED`
- `EXPIRED`
- `CANCELLED`
- `SUPERSEDED`
- `FAILED_DETERMINISTIC`
- `NO_SHOW` where the provider system exposes it

### Invariant

Only `CONFIRMED` may support user-facing wording equivalent to **“booked.”**

`REQUEST_SUBMITTED`, `WAITLISTED`, `SLOT_HELD_*`, `PENDING_PROVIDER_ACCEPTANCE`, and `UNKNOWN_RECONCILIATION_REQUIRED` must have explicit weaker wording.

---

## 5. Transition guards

### Guard G1 — approval equality

Before any external create/request operation, compare current execution terms against the approved authorization version.

If practitioner, service, location, material price, time window, or cancellation conditions differ beyond the authorization scope:

`AUTHORIZED -> REQUIRES_FRESH_USER_APPROVAL`

Do not silently widen authorization.

### Guard G2 — confirmation requires evidence

Do not permit transition to `CONFIRMED` unless confirmation evidence includes enough information to bind the result to the approved proposal:

- provider/clinic,
- service,
- start time + timezone,
- relevant practitioner/location when material,
- authoritative booking identifier or equivalent provider-originated confirmation evidence.

### Guard G3 — timeout is not failure

If an external create/cancel request times out after transmission, do not mark it `FAILED_DETERMINISTIC` unless the adapter has positive evidence that no state change occurred.

Instead:

`TRANSACTION_IN_FLIGHT -> UNKNOWN_RECONCILIATION_REQUIRED`

Then reconcile before retry.

### Guard G4 — retries must preserve logical operation identity

Retrying the same logical mutation should reuse the same durable `operation_id` lineage and external idempotency key where supported.

A changed appointment request is a new logical operation, not a retry.

### Guard G5 — reschedule must preserve both old and new records

A reschedule should preserve:

- old booking identity,
- replacement booking identity,
- supersession linkage,
- independent state of each.

Do not delete/overwrite the historical booking record simply because the new one succeeds.

---

## 6. Reconciliation algorithm proposal

### Create operation

1. Persist `TransactionOperation` before external mutation.
2. Send request with idempotency token if supported.
3. If response includes external booking ID, persist it immediately.
4. If the response establishes accepted/active state, classify as `CONFIRMATION_PENDING_RECONCILIATION` until either:
   - independent read-back confirms matching appointment, or
   - adapter contract explicitly defines the create response as authoritative enough for `CONFIRMED`.
5. If transport outcome is ambiguous, reconcile before retry.
6. If authoritative state cannot be determined within a bounded period, require human recovery.

### Cancellation

1. Read current external booking state if available.
2. Persist cancel operation.
3. Send cancellation using version/precondition and idempotency features where available.
4. If API returns no post-state body (Microsoft and Cliniko both document successful cancellation responses without a returned appointment object), mark `CANCELLATION_PENDING` or `CANCELLED_ACKNOWLEDGED` internally.
5. Read back / consume authoritative event where possible.
6. Only present final cancellation when the adapter contract's evidence threshold is satisfied.

### Reschedule

Treat reschedule as a saga unless the vendor contract proves atomic semantics:

1. Preserve current booking A.
2. Obtain/create replacement B.
3. Confirm B.
4. Cancel/supersede A if needed.
5. Reconcile A and B.
6. If both remain active unexpectedly: human recovery for duplicate booking.
7. If A is gone but B fails: human recovery for lost appointment.

---

## 7. Adapter capability contract

The current `booking_channel` field should evolve into explicit capabilities.

Suggested capability flags/metadata:

- `can_search_availability`
- `can_hold_slot`
- `hold_scope` = none / cohort / patient
- `can_create_booking`
- `create_result_semantics` = request / pending / confirmed
- `can_read_booking`
- `can_update_booking`
- `can_cancel_booking`
- `can_reschedule_booking`
- `reschedule_semantics` = atomic / cancel_create / unknown
- `supports_idempotency_create`
- `supports_idempotency_cancel`
- `supports_version_preconditions`
- `supports_webhooks`
- `supports_confirmation_reference`
- `supports_waitlist`
- `supports_patient_portal_readback`
- `requires_hosted_handoff`
- `capability_verified_at`
- `capability_source`

The adapter should fail closed if required capabilities are unknown.

---

## 8. Concrete test backlog

These tests are proposed as acceptance criteria for later implementation.

### Authorization boundary

1. Approval alone never produces `CONFIRMED`.
2. Different practitioner after approval requires fresh approval when practitioner identity is material.
3. Price above authorized ceiling requires fresh approval.
4. Different location/cancellation terms require fresh approval when material.

### Create/idempotency

5. Create succeeds with external ID -> transaction persists ID before confirmation UI.
6. Create response times out after server-side success -> read-back finds booking -> no duplicate retry.
7. Create response times out and read-back finds nothing -> same logical idempotency key is reused.
8. User changes requested time after timeout -> new logical operation/idempotency key.

### Request/pending/waitlist

9. Appointment request acknowledgement -> `REQUEST_SUBMITTED`, never `CONFIRMED`.
10. Provider API returns pending/unaccepted -> `PENDING_PROVIDER_ACCEPTANCE`.
11. Waitlist enrollment -> `WAITLISTED`.
12. Waitlist notification/exclusive access -> not confirmed.
13. Cohort slot hold cannot be rendered as patient-specific hold.

### Notification independence

14. Appointment exists while email confirmation is disabled -> still `CONFIRMED` if authoritative booking evidence exists.
15. Confirmation email delivered without matching approved provider/service/time -> human review, not confirmation.

### Cancellation

16. Cancellation returns HTTP 204/no object -> adapter performs configured reconciliation before final UI state.
17. Cancellation transport timeout -> no blind retry without reconciliation.
18. Cancellation read-back shows active appointment -> remain pending/recovery.

### Reschedule

19. Replacement B confirmed then old A canceled -> A=`SUPERSEDED`, B=`CONFIRMED`.
20. B confirmed but A still active -> duplicate-booking recovery.
21. A canceled but B failed -> lost-appointment recovery.
22. Out-of-order old-cancel/new-create webhook events still converge to correct supersession graph.

### Staleness / business rules

23. Availability observed, then booking rejected by changed scheduling rule -> deterministic failure, not system corruption.
24. Availability snapshot exceeds adapter freshness threshold -> re-query before mutation.

### Event correctness

25. Duplicate webhook event -> idempotent processing.
26. Older external version arrives after newer one -> ignore/regard as stale according to adapter ordering rule.
27. External booking changes outside BenefitFlow after confirmation -> detect drift and require user/human reconciliation if material.

---

## 9. Cross-agent dependencies

### R3 Provider Discovery

R3 provider records should expose the booking-system/vendor identity and provenance needed to select an adapter. A provider profile saying merely `web` is insufficient.

### R6 Voice Transaction Workflow

R6 should define what evidence converts a live phone interaction from `REQUEST_SUBMITTED` to `CONFIRMED`, and how to capture material appointment terms without over-collecting sensitive data.

### R8 Abuse/Fraud

R8 should red-team:
- forged provider confirmation,
- replayed booking evidence,
- duplicate retry abuse,
- malicious redirect/hosted booking page,
- approval-token replay after terms change.

### R9 Security

R9 should define storage/access requirements for external booking IDs, adapter secrets, idempotency records, and audit history.

### R10 Integration Adapter Architecture

R10 should consume the `BookingTransaction`, `TransactionOperation`, idempotency, reconciliation, and supersession recommendations as candidate adapter-contract requirements.

---

## 10. Coordination collision note

Two R4 researchers created independent workstreams at essentially the same timestamp:

- `r4-booking-channels/researcher-20261003T2224Z/`
- `r4-booking-channels/researcher-r4-booking-channels-20261003T2224Z/`

Both contain relevant evidence. Neither should overwrite the other. Manager reconciliation should merge the complementary evidence and decide the canonical R4 disposition.

This is also evidence that lane claiming currently permits a race condition. That coordination issue belongs to Manager/Primary rather than being silently "fixed" by a researcher.

---

## 11. What this packet does not establish

This evidence does **not** establish:

- that BenefitFlow is authorized to use Microsoft, Square, Calendly, Jane, Cliniko, or any other vendor API;
- that every vendor requires post-create read-back before a booking can be trusted;
- that every `204` cancellation requires the same follow-up policy;
- that every reschedule is non-atomic;
- that a single generic adapter can safely normalize every vendor without vendor-specific contracts;
- that a discovered provider accepts a user's insurance or benefit plan;
- that any recommendation here is accepted project state.

## Research disposition

The evidence now supports a stronger statement than "booking has multiple states":

**BenefitFlow needs a durable transaction ledger with explicit operation identity and reconciliation semantics before any production adapter can safely claim booking, cancellation, or reschedule outcomes.**

The current beta's `READY_FOR_TRANSACTION_ADAPTER` boundary should be preserved as authorization handoff, not expanded into a booking-success state.