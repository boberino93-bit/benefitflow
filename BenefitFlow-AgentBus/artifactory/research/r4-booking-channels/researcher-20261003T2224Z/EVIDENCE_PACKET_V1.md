# BenefitFlow R4 Evidence Packet v1 — Booking Channels and Confirmation Semantics

Project: `BenefitFlow` (`project_id=benefitflow`)
Role: Research specialist — evidence/proposals only
Assignment: `R4 — Booking Channels and Confirmation Semantics`
Prepared lane: `provider-discovery-booking`
Research date: 2026-10-03

## Executive finding

BenefitFlow needs a booking-state model that is explicitly separate from both **user authorization** and **communication/notification state**. Public documentation from current scheduling systems shows that:

1. A booking may exist but still be `PENDING` rather than accepted.
2. A wait-list request or wait-list notification is not a booking.
3. A platform may hold a slot temporarily for a class of users without assigning it to any one user.
4. A confirmation email can be delayed after the appointment is already booked, so email delivery cannot be the canonical booking truth.
5. Rescheduling may be represented as cancellation of one appointment plus creation of another, not an in-place time mutation.
6. Create/cancel operations can require idempotency keys and version checks because retries and concurrent edits can otherwise create incorrect outcomes.

The current beta boundary `AWAITING_USER_APPROVAL -> READY_FOR_TRANSACTION_ADAPTER` is a good authorization boundary, but it is not sufficient as a production transaction state machine. The production adapter should create and reconcile a separate transaction record until authoritative evidence reaches a terminal or human-review state.

---

## 1. Observed evidence

### E1 — Square exposes an explicit booking state machine

**Source:** Square Developer Documentation — BookingStatus Enum  
https://developer.squareup.com/reference/square/enums/BookingStatus

Current Square documentation exposes at least these booking states:
- `PENDING` — unaccepted booking, visible to customer and seller.
- `ACCEPTED` — seller has accepted/agreed to the booking.
- `DECLINED` — once pending, then declined by seller.
- `CANCELLED_BY_CUSTOMER`.
- `CANCELLED_BY_SELLER`.
- `NO_SHOW`.

**Applicability:** Strong conceptual evidence that a generic model must not equate "booking object created" with "confirmed appointment". Vendor-specific names should not be copied directly into BenefitFlow, but the semantic distinction is material.

**Confidence:** High.

### E2 — Square create and cancel operations use idempotency; cancel can use optimistic concurrency

**Sources:**
- Create booking: https://developer.squareup.com/reference/square/bookings/create-booking
- Cancel booking: https://developer.squareup.com/reference/square/bookings-api/CancelBooking
- Booking object: https://developer.squareup.com/reference/square/objects/Booking

Square's create-booking request accepts an `idempotency_key`. Cancellation also accepts an `idempotency_key`, and accepts a `booking_version`, described as the revision number used for optimistic concurrency. The Booking object itself carries a `version` field.

**Applicability:** Directly relevant to transaction-adapter design. A timeout after submitting a create/cancel request cannot safely be handled by blindly repeating the action. An adapter should persist an operation identity before external mutation and reconcile before retrying.

**Confidence:** High.

### E3 — Square booking updates can arrive asynchronously by webhook

**Source:** Square Developer Documentation — `booking.updated` webhook  
https://developer.squareup.com/reference/square/bookings-api/webhooks/booking.updated

Square publishes booking update events that include the external booking ID, status, timestamps and version.

**Applicability:** Supports event-driven reconciliation, but webhooks should be treated as change signals that update or trigger retrieval of authoritative state, not as the only source of truth.

**Confidence:** High.

### E4 — Calendly reschedule semantics are cancel + create

**Sources:**
- Webhook automation guide: https://developer.calendly.com/docs/api-guides/trigger-automations-with-other-apps-when-invitees-schedule-or-cancel-events
- Reschedule webhook guide: https://developer.calendly.com/docs/api-guides/see-how-webhook-payloads-change-when-invitees-reschedule-events

Calendly documents that a reschedule produces both an `invitee.canceled` event for the old appointment and an `invitee.created` event for the new one. The payload can carry references connecting the old and new invitee records.

**Applicability:** A generic BenefitFlow `RESCHEDULED` flag is not enough. The domain model should preserve the superseded booking and the replacement booking as separately addressable external objects connected by a correlation/supersession relationship.

**Confidence:** High.

### E5 — Calendly distinguishes routing-form submission from successful booking

**Source:** Calendly — webhook subscriptions  
https://developer.calendly.com/docs/api-guides/receive-data-from-scheduled-events-in-real-time-with-webhook-subscriptions

Calendly's routing form submission event can fire whenever a routing form is submitted, whether or not a booking occurs.

**Applicability:** Strong evidence that "form submitted" is a request/intake state, not confirmation evidence. BenefitFlow should represent form completion separately from appointment creation.

**Confidence:** High.

### E6 — Jane wait-list request is not an appointment

**Sources:**
- Jane — Using the Wait List: https://jane.app/guide/using-the-wait-list
- Jane — Client Experience: https://jane.app/guide/wait-list-notifications-client-experience

Jane permits clients to add a wait-list request containing appointment preferences and availability. Staff can later choose a client and explicitly book them into an opening. Jane also documents that a client may receive a wait-list notification but find the spot already taken by another client.

**Applicability:** A wait-list membership, notification, exclusive-access invitation or "slot available" message must never be displayed by BenefitFlow as a booked appointment.

**Confidence:** High.

### E7 — Jane can hold an opening without assigning the appointment to a patient

**Sources:**
- Jane — Managing Your Wait List: https://jane.app/guide/managing-your-wait-list-with-jane-d7b60bc9-5a45-41de-8bc4-ac831f95d239
- Jane — Using Wait List Notifications: https://jane.app/guide/using-wait-list-notifications

When an appointment opens, Jane can place a wait-list cue that holds the time temporarily and notify eligible wait-listed clients. The held spot may later be released or booked by a specific client.

**Applicability:** "Hold" is a distinct allocation state. BenefitFlow should not map a temporary hold to either `available` or `confirmed`; it should be represented separately where the adapter can observe it.

**Confidence:** High.

### E8 — Confirmation email timing may lag canonical booking state

**Source:** Jane — Online Booking Grace Period  
https://jane.app/guide/online-booking-grace-period

Jane documents a three-minute grace period after an appointment is booked before sending the "Thanks for Booking" notification. During the grace period the appointment can already exist and be changed, cancelled or archived.

**Applicability:** Email/SMS confirmation delivery is notification evidence, not authoritative booking creation evidence. BenefitFlow should prioritize the scheduling system's external booking object/confirmed state over whether a notification has been delivered.

**Confidence:** High.

### E9 — Cliniko separates availability configuration from actual bookings and exposes explicit cancellation operations

**Sources:**
- Cliniko API booking docs: https://docs.api.cliniko.com/openapi/booking
- Cliniko cancel individual appointment: https://docs.api.cliniko.com/openapi/individual-appointment/cancelindividualappointment-patch

Cliniko's availability endpoints respect practice-configured online-booking rules such as minimum advance time and maximum appointments per day segment. Individual appointments have a specific cancellation endpoint; the documented cancellation response is HTTP 204.

**Applicability:** Search-time availability must be treated as ephemeral. A slot observed during discovery is not a reservation. After cancellation or other mutation where an API returns little/no body, the adapter may need a follow-up read or webhook reconciliation to establish canonical state.

**Confidence:** High.

---

## 2. Interpretation for BenefitFlow

### 2.1 Three independent dimensions must not be collapsed

BenefitFlow should distinguish:

1. **Authorization state** — what the user has approved BenefitFlow to do.
2. **Transaction state** — what has actually happened at the provider/scheduling system.
3. **Notification state** — what messages or receipts have been sent/received.

Example:
- User authorization: `APPROVED`.
- Transaction: `REQUEST_SUBMITTED` or `PENDING_PROVIDER_ACCEPTANCE`.
- Notification: `CONFIRMATION_EMAIL_NOT_YET_SENT`.

These can legitimately coexist. The existing beta correctly stops at user authorization, but production logic must not convert authorization directly into a claim that an appointment is confirmed.

### 2.2 Recommended normalized transaction states

Recommended generic states, deliberately broader than any one vendor:

- `NOT_STARTED` — no external transaction attempted.
- `AVAILABILITY_OBSERVED` — candidate slot found; no hold or booking implied.
- `WAITLIST_REQUESTED` — user is on a waitlist; not booked.
- `SLOT_HELD` — external system temporarily protects a slot, but confirmation is not established.
- `REQUEST_SUBMITTED` — form/email/phone/API request was sent but acceptance is not established.
- `PENDING_PROVIDER_ACCEPTANCE` — external system explicitly reports a pending/unaccepted booking.
- `CONFIRMED` — authoritative evidence establishes an accepted/active appointment.
- `RESCHEDULE_PENDING` — old booking may still exist while replacement is unresolved.
- `SUPERSEDED` — old booking has been replaced by a new booking; preserve linkage.
- `CANCELLATION_PENDING` — cancellation requested but canonical cancellation not yet observed.
- `CANCELLED` — authoritative state confirms cancellation.
- `DECLINED` — provider/seller explicitly declined a pending request.
- `NO_SHOW` — post-appointment terminal outcome where available.
- `FAILED` — deterministic failure with no booking created/modified.
- `UNKNOWN_RECONCILIATION_REQUIRED` — timeout, broken channel, conflicting evidence, or partial failure where blindly retrying may duplicate/change a real booking.

The UI can simplify these states for users, but the internal adapter should keep the full distinction.

### 2.3 Recommended booking-channel taxonomy

A normalized channel enum should distinguish at least:

1. `NATIVE_API` — BenefitFlow can create/read/cancel through authenticated API.
2. `HOSTED_BOOKING_PAGE` — external self-service page, potentially with strong success evidence but limited programmatic reconciliation.
3. `ROUTING_OR_INTAKE_FORM` — submits a request/intake; never assume confirmed.
4. `WAITLIST` — expresses preference/interest; never assume confirmed.
5. `PHONE_LIVE` — confirmation can be obtained verbally; must capture evidence and actor.
6. `EMAIL_ASYNC` — request sent; confirmation arrives asynchronously.
7. `STAFF_MANUAL` — clinic staff manually create appointment after another interaction.
8. `AGGREGATOR_HANDOFF` — third-party marketplace/referral layer; final clinic booking status may differ.

Each provider record should include the actual channel and its confirmation capabilities rather than one generic `booking_channel` value of only `phone/web/manual`.

---

## 3. Confirmation evidence hierarchy

Recommended evidence levels:

### Level A — authoritative machine-verifiable

Examples:
- Retrieval of an external booking object whose state is accepted/active/confirmed.
- API create response returning an accepted booking plus stable external booking ID, followed by successful retrieval or consistent webhook state where appropriate.

Store:
- adapter/provider system,
- external booking ID,
- external version/revision if available,
- external status,
- practitioner/service/location,
- start/end time and timezone,
- observed-at timestamp,
- source operation ID,
- raw-evidence hash or minimal replay-safe evidence reference.

### Level B — authenticated hosted-system success evidence

Examples:
- Hosted booking completion page showing confirmed time and booking reference.
- Authenticated patient portal showing appointment in upcoming appointments.

Prefer independent follow-up retrieval when available.

### Level C — provider-originated confirmation artifact

Examples:
- Clinic confirmation email/SMS containing concrete provider/service/date/time/location and a booking or cancellation reference.

Useful, but the Jane grace-period evidence demonstrates that notification timing should not define creation time or canonical status.

### Level D — human verbal/manual confirmation

Examples:
- Clinic employee verbally confirms appointment by phone.

Required capture should include:
- time of call,
- clinic/contact channel,
- name/role if voluntarily provided and necessary,
- exact appointment terms repeated back,
- any reference number,
- explicit statement whether confirmation is final or a request pending follow-up.

This should be considered lower-confidence than authoritative system retrieval and should trigger later reconciliation if another channel becomes available.

### Not confirmation evidence

The following must never be represented as `CONFIRMED` by themselves:
- slot visible in availability search,
- routing/intake form submitted,
- email sent requesting an appointment,
- voicemail left,
- wait-list membership,
- wait-list notification received,
- "we will contact you" acknowledgement,
- user approval for BenefitFlow to attempt the booking,
- transient slot hold without assignment/acceptance.

---

## 4. Retry, idempotency and reconciliation recommendations

### 4.1 Persist operation intent before external mutation

Before a create, cancel or reschedule operation, create a durable internal transaction operation containing:
- `operation_id` (globally unique),
- `proposal_id`,
- operation type,
- normalized intended appointment terms,
- adapter/provider identity,
- idempotency key if supported,
- prior external booking ID/version if applicable,
- authorization record/version,
- attempt counter,
- state `IN_FLIGHT`.

### 4.2 On timeout, reconcile before retry

If response status is unknown:
1. Query by external booking ID when known.
2. Query/search by stable request correlation where the adapter supports it.
3. Consume or inspect webhook/events.
4. If still ambiguous, move to `UNKNOWN_RECONCILIATION_REQUIRED` instead of blindly repeating the mutation.

### 4.3 Reuse idempotency keys for the same logical operation

Where the external API supports idempotency (Square is direct evidence), retries of the **same logical create/cancel** should reuse the same stored idempotency key. A materially changed operation must receive a new operation identity and require any fresh user approval dictated by the existing BenefitFlow boundary.

### 4.4 Respect external versions

Where a booking system exposes versions/revisions (Square does), persist the observed version and use optimistic-concurrency fields where supported. A conflict should trigger a re-read and re-evaluation rather than overwrite newer provider/customer changes.

### 4.5 Model reschedule as a saga

Because systems such as Calendly represent reschedule as old cancellation + new creation, BenefitFlow should not assume atomic reschedule.

Recommended flow:
1. Identify current confirmed booking A.
2. Create or obtain replacement B according to channel semantics.
3. Establish B as confirmed.
4. Cancel/supersede A if not handled atomically by provider system.
5. Reconcile both A and B.
6. If B exists but A remains active, raise human recovery to avoid double booking.
7. If A is cancelled but B creation failed, surface the loss explicitly; do not falsely present a rescheduled appointment.

---

## 5. Human-recovery conditions

Route to human review rather than autonomous repeat when any of the following occur:

- External mutation times out and creation/cancellation state cannot be determined.
- Provider changes practitioner, service, price, location, time window or cancellation terms outside the approved scope.
- A booking remains pending beyond an adapter/channel-specific threshold.
- Wait-list offer expires or is taken by another patient.
- Confirmation artifact conflicts with API/portal state.
- Multiple active external bookings match the same BenefitFlow operation.
- Reschedule leaves both old and new appointments active.
- Cancellation may incur a fee not covered by the user's approved transaction scope.
- Booking channel asks for additional sensitive data not authorized in the approved proposal.
- Clinic says an appointment is "booked" but will only confirm later by another staff member/system.
- External source is unavailable long enough that freshness cannot be guaranteed.

---

## 6. Current beta gaps and implementation implications

### Observed current beta

`BookingProposal` currently has one status: `AWAITING_USER_APPROVAL`.

`BookingResult` currently permits only:
- `READY_FOR_TRANSACTION_ADAPTER`, or
- `DECLINED`.

The workflow correctly prevents external action before approval and instructs the adapter not to accept materially different terms without returning to the user.

### Gap G1 — no post-approval transaction object

Add a durable object separate from `BookingResult`, e.g. `BookingTransaction`, that records actual execution and reconciliation state.

Suggested fields:
- `transaction_id`
- `proposal_id`
- `operation_id`
- `channel_type`
- `adapter_id`
- `state`
- `external_booking_id`
- `external_booking_version`
- `external_status_raw`
- `requested_terms_hash`
- `confirmed_terms`
- `evidence_level`
- `evidence_reference`
- `created_at`, `last_observed_at`, `terminal_at`
- `supersedes_transaction_id` / `superseded_by_transaction_id`
- `retry_count`
- `reconciliation_required`
- `failure_code`
- `human_recovery_reason`

### Gap G2 — `Provider.booking_channel` is too coarse

Current enum `phone | web | manual` cannot distinguish a hosted confirmed booking flow from an intake form or waitlist. Expand channel semantics and store channel capability flags, such as:
- `can_query_availability`
- `can_create_booking`
- `create_returns_confirmation`
- `supports_pending_acceptance`
- `supports_waitlist`
- `supports_cancel`
- `supports_reschedule`
- `supports_idempotency`
- `supports_versioning`
- `supports_webhooks`
- `supports_external_retrieval`

### Gap G3 — confirmation semantics are absent

Add a normalized `confirmation_state` and an evidence level. UI wording should be generated from the state, not from the fact that an adapter call completed.

### Gap G4 — no explicit unknown/ambiguous state

A production adapter requires `UNKNOWN_RECONCILIATION_REQUIRED`. Without it, timeout/error handling tends to collapse into either false failure or unsafe retry.

---

## 7. Recommended tests

1. **Pending booking** — adapter creates booking object in external `PENDING`; BenefitFlow must not show confirmed.
2. **Accepted booking** — external `ACCEPTED`; store stable ID and show confirmed.
3. **Waitlist request** — patient added to waitlist; UI says waitlisted, never booked.
4. **Waitlist notification race** — opening notification arrives but another user takes slot; state remains waitlisted/unbooked.
5. **Slot hold expiry** — temporary hold expires; never transition to cancelled appointment because no appointment existed.
6. **Confirmation email delay** — authoritative booking exists before email; state remains confirmed even while notification pending.
7. **Create timeout with idempotency** — retry same logical operation with same key; only one external booking permitted.
8. **Create timeout without idempotency** — reconcile first; ambiguous state enters human review rather than blind retry.
9. **Cancel with version conflict** — external booking changed since read; refetch before retry.
10. **Calendly-style reschedule** — old cancellation and new creation correlated; avoid temporary false `CANCELLED` user state when replacement is being established.
11. **Reschedule partial failure A** — new booking confirmed, old cancellation fails; human recovery because duplicate active bookings exist.
12. **Reschedule partial failure B** — old cancelled, replacement fails; surface explicit unbooked outcome.
13. **Form submitted** — routing/intake form acknowledgement cannot transition to confirmed.
14. **Phone request only** — voicemail left; state request-submitted, not confirmed.
15. **Phone verbal confirmation** — capture terms and lower-tier evidence; schedule follow-up reconciliation where possible.
16. **Provider term drift** — phone staff offers different practitioner/price/time; return to user for fresh approval if material under BenefitFlow policy.
17. **Cancellation fee appears** — stop before consenting to fee absent explicit authorization.
18. **Webhook duplicate/out-of-order delivery** — state reducer is idempotent and version/timestamp aware.
19. **Webhook says cancelled but API retrieval says active** — contradiction triggers reconciliation, not silent selection.
20. **Booking ID reused incorrectly across providers** — external identity key must be namespaced by adapter/provider account.

---

## 8. Unknowns / contradictions requiring later research or implementation discovery

- Jane public documentation establishes semantic behavior, but the public pages reviewed here do not establish a general public booking API contract suitable for BenefitFlow integration.
- Cliniko documentation reviewed establishes API bookings/appointments and cancellation behavior, but this packet has not yet established whether every Cliniko online booking path maps one-to-one to a public API-created appointment flow.
- Hosted booking pages vary in whether they expose stable confirmation IDs, authenticated patient-portal retrieval or anti-automation controls; adapter-specific discovery will be required.
- Phone/email channels have clinic-specific semantics. A spoken "you're booked" may still depend on internal staff workflow; independent confirmation should be preferred when available.
- Cancellation fees, deposits and payment authorization belong to adjacent transaction/payment policy and require explicit user authorization rules; R4 only establishes that these changes are material to booking semantics.

---

## 9. What this evidence does not establish

This packet does **not** establish:
- that BenefitFlow may legally or contractually automate any named vendor or clinic,
- that a public API exists or is available under acceptable commercial terms for any particular provider,
- that provider-side "confirmed" status guarantees insurance eligibility, direct billing or claim payment,
- that an email/SMS receipt is legally sufficient proof of an appointment,
- that all scheduling systems use the same states or atomicity model,
- that BenefitFlow should bypass a hosted booking system's terms, security controls or patient authentication,
- that a cancellation/reschedule is fee-free.

---

## 10. Recommendation to Manager / Primary

Treat the existing `READY_FOR_TRANSACTION_ADAPTER` result as an **authorization handoff only**. Do not rename it `BOOKED` or `CONFIRMED`.

For production architecture, add a separate adapter-owned transaction state machine with durable operation IDs, idempotency/reconciliation logic, explicit unknown states, evidence levels, and old/new booking linkage for reschedules. The UI should only state that an appointment is confirmed once confirmation evidence reaches the product's accepted confirmation threshold.
