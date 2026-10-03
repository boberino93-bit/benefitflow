# BenefitFlow R4 Research Packet — Booking Channels and Confirmation Semantics

**Project:** BenefitFlow (`project_id=benefitflow`)  
**Assignment:** R4 — Booking Channels and Confirmation Semantics  
**Prepared lane:** `provider-discovery-booking`  
**Researcher:** `researcher-r4-booking-confirmation-20261003`  
**Date:** 2026-10-03  
**Status:** Specialist evidence only — requires manager/reviewer reconciliation before Primary acceptance

## Executive finding

BenefitFlow's current beta has the correct safety boundary before external action, but it does not yet model what happens after an approved proposal is handed to a transaction adapter.

The central R4 finding is that **"request submitted", "slot held", "waitlisted", "calendar event created", and "appointment confirmed" are materially different states and must never be collapsed into one generic "booked" outcome.**

Healthcare scheduling standards already make this distinction. HL7 FHIR separates `proposed`, `pending`, `booked`, `waitlist`, `cancelled`, `noshow`, and later lifecycle states. FHIR further states that visible availability does not guarantee a booking: the receiving scheduling system can still make qualifying decisions before accepting the appointment.

Commercial systems reinforce the same point:

- Jane distinguishes a wait-list request from an actual booked appointment, and a wait-list opening can be offered to multiple eligible clients before one person books it.
- Google Calendar can create an event while an attendee is still `needsAction` or `tentative`; calendar insertion therefore cannot be treated as provider confirmation.
- Calendly models rescheduling as cancellation of the old invitee plus creation of a new invitee.
- Square's Bookings API exposes an actual booking resource, supports idempotency keys on create/update/cancel, uses booking versions for concurrency on cancellation, and emits booking webhooks. Square also documents duplicate webhook delivery and explicitly does not guarantee webhook delivery order.

BenefitFlow should therefore use a **provider-independent transaction state machine** plus adapter-specific evidence mapping. An external adapter may only promote a transaction to `CONFIRMED_BOOKED` when confirmation evidence satisfies a defined evidence threshold.

---

## 1. Scope and evidence classification

This packet covers:

1. Booking channel taxonomy.
2. Appointment/request/hold/waitlist/confirmation semantics.
3. Cancellation and rescheduling semantics.
4. Confirmation evidence requirements.
5. Retry, duplicate, ordering, idempotency, reconciliation, and human recovery.
6. Gaps in the current BenefitFlow beta model.
7. Recommended implementation/test implications.

This packet does **not** determine:

- Which booking vendors BenefitFlow will contract with.
- Which APIs are commercially available to BenefitFlow.
- Legal consent/privacy requirements (R5).
- Voice disclosure/recording implementation (R6).
- Full adapter architecture (R10).
- Provider identity/source authority (R3).
- Any real appointment availability.

### Evidence labels used

- **OBSERVED EVIDENCE** — directly supported by a cited source.
- **INTERPRETATION** — engineering meaning derived from evidence.
- **RECOMMENDATION** — proposed BenefitFlow design choice.
- **UNKNOWN** — not established by this research.

---

## 2. Source-indexed evidence

### S1 — HL7 FHIR R5 Appointment resource
**Source:** HL7 FHIR R5 Appointment  
**URL:** https://hl7.org/fhir/R5/appointment.html  
**Applicability:** Healthcare scheduling semantics; vendor-neutral conceptual model.  
**Freshness:** R5 published specification (permanent published version).  
**Confidence:** High for semantic distinctions; not a mandate that every clinic software uses FHIR.

**OBSERVED EVIDENCE**
- Availability does not guarantee an appointment can be made; the receiving booking system may apply additional qualifying decisions.
- Appointment request-response workflows can use `proposed`/`pending` before confirmation.
- Appointment becomes `booked` after participant acceptance is resolved.
- Waitlisting is a separate workflow/state.
- Cancellation and no-show are separate states.

**INTERPRETATION**
BenefitFlow must not infer confirmation from availability discovery or request submission.

### S2 — HL7 FHIR R4 Appointment status and transition examples
**Source:** HL7 FHIR R4 Appointment  
**URL:** https://hl7.org/fhir/R4/appointment.html  
**Applicability:** Mature healthcare scheduling semantics and transition examples.  
**Freshness:** Stable R4 specification; older than R5 but useful corroboration.  
**Confidence:** High.

**OBSERVED EVIDENCE**
- `pending` is used while acceptance is unresolved.
- `booked` is used once all participants are accepted and the slot is busy.
- `waitlist` is separate from `booked`.
- Example transitions include waitlist -> proposed -> booked, with an earlier appointment potentially cancelled.

**INTERPRETATION**
A single boolean `booked=true/false` is too weak for production scheduling.

### S3 — Jane wait-list workflow
**Source:** Jane App — Using the Wait List  
**URL:** https://jane.app/guide/using-the-wait-list  
**Applicability:** Real healthcare practice-management workflow, particularly relevant to Canadian/US clinics.  
**Freshness:** Current Jane help content accessed 2026-10-03.  
**Confidence:** High for Jane-specific behavior.

**OBSERVED EVIDENCE**
- Patients/clients can create wait-list requests.
- A wait-list request stores preferred appointment/timing information.
- Staff later use a separate booking action to place the client into an actual slot.

**INTERPRETATION**
Joining a waitlist is not evidence of an appointment.

### S4 — Jane wait-list notifications and held openings
**Source:** Jane App — Wait List Notifications / Automatic Wait List Notifications  
**URLs:**  
- https://jane.app/guide/wait-list-notifications-client-experience  
- https://jane.app/guide/using-automatic-wait-list-notifications  
**Applicability:** Healthcare scheduling; illustrates held opportunity vs confirmed booking.  
**Freshness:** Current Jane help content accessed 2026-10-03.  
**Confidence:** High for Jane-specific behavior.

**OBSERVED EVIDENCE**
- When a qualifying opening appears, Jane can hold the spot during a notification/exclusive-access period.
- Multiple eligible wait-listed clients may be notified.
- A client can click through but find the spot unavailable if another client books first.

**INTERPRETATION**
A "held opening", "exclusive booking opportunity", or "offer" cannot be represented as a confirmed appointment. Holds require expiry semantics.

### S5 — Jane booking grace period
**Source:** Jane App — Online Booking Grace Period  
**URL:** https://jane.app/guide/online-booking-grace-period  
**Applicability:** Healthcare scheduling lifecycle.  
**Freshness:** Current Jane help content accessed 2026-10-03.  
**Confidence:** High for Jane-specific behavior.

**OBSERVED EVIDENCE**
- Jane has a short post-booking grace period before sending the booking notification.
- During that interval a just-booked appointment can be changed/cancelled, with different archival/cancellation handling.

**INTERPRETATION**
Notification delivery time is not itself the creation time or authoritative status boundary. BenefitFlow should store source timestamps separately.

### S6 — Calendly webhook/reschedule behavior
**Source:** Calendly Developer Documentation  
**URLs:**  
- https://developer.calendly.com/docs/api-guides/see-how-webhook-payloads-change-when-invitees-reschedule-events  
- https://developer.calendly.com/docs/api-guides/trigger-automations-with-other-apps-when-invitees-schedule-or-cancel-events  
**Applicability:** Common scheduling SaaS behavior; useful adapter pattern.  
**Freshness:** Current developer docs accessed 2026-10-03.  
**Confidence:** High for Calendly-specific behavior.

**OBSERVED EVIDENCE**
- Scheduled events trigger `invitee.created`.
- Cancellations trigger `invitee.canceled`.
- A reschedule triggers both cancellation of the old invitee and creation of a new invitee.
- Payloads link old and new invitee URIs.

**INTERPRETATION**
Rescheduling should be modeled as a lineage relationship, not assumed to be an in-place mutation.

### S7 — Google Calendar event creation and attendee responses
**Source:** Google Calendar API documentation  
**URLs:**  
- https://developers.google.com/workspace/calendar/api/guides/create-events  
- https://developers.google.com/resources/api-libraries/documentation/calendar/v3/csharp/latest/classGoogle_1_1Apis_1_1Calendar_1_1v3_1_1Data_1_1EventAttendee.html  
**Applicability:** Calendar projection/integration semantics.  
**Freshness:** Current documentation accessed 2026-10-03.  
**Confidence:** High.

**OBSERVED EVIDENCE**
- `events.insert()` creates a calendar event.
- Developers can choose their own event ID; Google documents that doing so can prevent duplicate event creation after ambiguous failures and helps sync local records.
- Attendee response statuses include `needsAction`, `tentative`, `accepted`, and `declined`.

**INTERPRETATION**
A calendar write is a projection/sync action, not authoritative provider-booking evidence. Calendar event creation should occur after confirmation, or be visibly marked tentative when used before confirmation.

### S8 — Square Bookings API create/update/cancel
**Source:** Square Developer Documentation — Bookings API  
**URLs:**  
- https://developer.squareup.com/reference/square/bookings-api/create-booking  
- https://developer.squareup.com/reference/square/bookings-api/update-booking  
- https://developer.squareup.com/reference/square/bookings-api/CancelBooking  
**Applicability:** Concrete example of a transactional booking API.  
**Freshness:** API versions surfaced in September 2026.  
**Confidence:** High for Square-specific mechanics.

**OBSERVED EVIDENCE**
- Create booking supports an `idempotency_key`.
- Update booking supports an `idempotency_key`.
- Cancel booking supports an `idempotency_key`.
- Cancellation accepts a booking revision/version for optimistic concurrency.
- Booking objects have explicit statuses such as `ACCEPTED` and cancellation statuses.

**INTERPRETATION**
BenefitFlow adapters need stable operation IDs, idempotent retry behavior where available, and concurrency/version awareness.

### S9 — Square booking webhooks
**Source:** Square Developer Documentation — `booking.updated` and Webhooks overview  
**URLs:**  
- https://developer.squareup.com/reference/square/bookings-api/webhooks/booking.updated  
- https://developer.squareup.com/docs/webhooks/overview  
**Applicability:** External status synchronization and recovery.  
**Freshness:** Current docs, September 2026 API version.  
**Confidence:** High.

**OBSERVED EVIDENCE**
- `booking.updated` is emitted when a booking is updated or cancelled.
- Webhook events have unique `event_id` values.
- Square states webhook notifications can be delivered more than once.
- Square states delivery order is not guaranteed.
- Failed deliveries are retried with exponential backoff for up to 24 hours.

**INTERPRETATION**
Webhook receivers must deduplicate, tolerate out-of-order events, and reconcile with authoritative current state.

### S10 — Square webhook authenticity
**Source:** Square Developer Documentation — validate event notification  
**URL:** https://developer.squareup.com/docs/webhooks/step3validate  
**Applicability:** Confirmation evidence integrity for webhook-driven adapters.  
**Freshness:** Current docs accessed 2026-10-03.  
**Confidence:** High.

**OBSERVED EVIDENCE**
- Square signs webhook notifications.
- Consumers are expected to validate the HMAC signature and discard untrusted posts.

**INTERPRETATION**
A webhook cannot count as confirmation evidence until authenticity verification succeeds.

### S11 — Microsoft Graph Bookings
**Source:** Microsoft Graph v1.0 — Create bookingAppointment / bookingAppointment resource  
**URLs:**  
- https://learn.microsoft.com/en-us/graph/api/bookingbusiness-post-appointments?view=graph-rest-1.0  
- https://learn.microsoft.com/en-us/graph/api/resources/bookingappointment?view=graph-rest-1.0  
**Applicability:** Concrete direct booking API pattern.  
**Freshness:** Current Graph v1.0 docs accessed 2026-10-03.  
**Confidence:** High for Microsoft-specific behavior.

**OBSERVED EVIDENCE**
- Successful appointment creation returns HTTP 201 and a bookingAppointment object.
- Bookings supports create/read/update/delete/cancel operations.

**INTERPRETATION**
Some adapters provide a strong synchronous confirmation artifact, but BenefitFlow still needs vendor-specific mapping to its own state model.

---

## 3. Booking channel taxonomy

BenefitFlow's current `Provider.booking_channel` enum is:

- `phone`
- `web`
- `manual`

That is insufficient because "web" can represent radically different transaction semantics.

### Recommended channel model

| Channel class | Example behavior | Submission result | Can immediately prove booking? | Recovery mode |
|---|---|---|---|---|
| `DIRECT_TRANSACTIONAL_API` | Square/Microsoft-style create-booking API | Booking resource or API error | Yes, if provider semantics/status meets confirmation rule | GET/reconcile by external ID or idempotency key |
| `HOSTED_SELF_BOOKING` | Provider-hosted booking page | User/agent completes hosted flow | Only after provider-hosted confirmation evidence | Confirmation page/email + later reconciliation |
| `WEB_REQUEST_FORM` | "Request an appointment" form | Request/lead/ticket | No | Await provider response; manual escalation on timeout |
| `WAITLIST` | Wait-list signup or opening notification | Wait-list/request record | No | Expiry/offer tracking; later booking action required |
| `PHONE_SYNCHRONOUS` | Clinic staff verbally confirms slot | Human verbal outcome | Potentially, with captured confirmation details | Human callback/reverification |
| `EMAIL_ASYNC` | Email booking request | Message sent | No | Await reply; threaded reconciliation |
| `MANUAL_STAFF_HANDOFF` | Human completes task in external portal/process | Human attestation + evidence | Depends on evidence | Human review |
| `CALENDAR_ONLY` | Calendar invite/event creation | Calendar object | No, unless provider's system itself defines it as booking evidence | Attendee response and provider confirmation still required |

### RECOMMENDATION

Store at least:

- `channel_type`
- `channel_provider`
- `channel_url_or_endpoint_id` (non-secret reference)
- `channel_verified_at`
- `channel_verification_source`
- `supports_create`
- `supports_update`
- `supports_cancel`
- `supports_status_read`
- `supports_webhooks`
- `supports_idempotency`
- `supports_hold`
- `supports_waitlist`
- `confirmation_mode`
- `confirmation_evidence_required`

Do not overload "web" to mean both direct booking and request submission.

---

## 4. Provider-independent transaction state model

BenefitFlow should keep **internal proposal authorization state** separate from **external appointment transaction state**.

### 4.1 Internal proposal authorization

Suggested states:

1. `PROPOSAL_DRAFT`
2. `AWAITING_USER_APPROVAL`
3. `USER_APPROVED`
4. `USER_DECLINED`
5. `APPROVAL_EXPIRED`
6. `REAPPROVAL_REQUIRED`

This state answers: **"What has the user authorized BenefitFlow to do?"**

### 4.2 External transaction state

Suggested normalized states:

1. `NOT_STARTED`
2. `SUBMISSION_IN_PROGRESS`
3. `REQUEST_SUBMITTED`
4. `AWAITING_EXTERNAL_CONFIRMATION`
5. `SLOT_HOLD_ACTIVE`
6. `WAITLISTED`
7. `CONFIRMED_BOOKED`
8. `RESCHEDULE_PENDING`
9. `CANCELLATION_PENDING`
10. `CANCELLED`
11. `REJECTED`
12. `EXPIRED`
13. `FAILED_RETRYABLE`
14. `FAILED_FINAL`
15. `RECONCILIATION_REQUIRED`
16. `UNKNOWN_EXTERNAL_STATE`
17. `NO_SHOW`
18. `FULFILLED`

This state answers: **"What does the external scheduling process currently establish?"**

### 4.3 Why the split matters

An approved proposal can remain `USER_APPROVED` while the external transaction is:

- still unsent,
- pending,
- waitlisted,
- held,
- confirmed,
- failed,
- cancelled,
- or uncertain.

The user's approval is not proof the clinic accepted the appointment.

### 4.4 Hold semantics

A hold should be a separate object or state extension:

- `hold_external_id`
- `hold_created_at`
- `hold_expires_at`
- `hold_scope`
- `hold_owner`
- `hold_release_required`
- `hold_status`

A hold becoming expired must never silently remain displayed as an appointment.

### 4.5 Waitlist semantics

A wait-list record should contain:

- `waitlist_external_id`
- `requested_period`
- `service/practitioner preferences`
- `joined_at`
- `expires_at` if known
- `notification preference`
- `last_offer_at`
- `offer_expires_at`
- `status`

`WAITLISTED` must not imply any reserved appointment time.

---

## 5. Confirmation evidence hierarchy

### Tier A — Strong authoritative confirmation

Examples:
- Provider/scheduling API returns an externally addressable booking object with a provider-defined accepted/booked status.
- Authenticated read-back (`GET`) confirms that booking by external ID.

Minimum fields:
- external booking ID
- provider/clinic ID
- practitioner if applicable
- service
- start/end + timezone
- location/modality
- current status
- source timestamp/version
- adapter/provider name

**RECOMMENDATION:** Sufficient for `CONFIRMED_BOOKED` when adapter mapping is reviewed and trusted.

### Tier B — Authenticated provider event corroboration

Examples:
- Signed webhook indicating created/accepted/booked.
- Webhook followed by authoritative read-back.

Requirements:
- signature/authenticity valid
- event deduplicated
- external booking ID present
- current state reconciled if ordering can vary

**RECOMMENDATION:** Strong evidence; prefer read-back before state promotion if the webhook provider documents unordered/duplicate delivery.

### Tier C — Provider-hosted confirmation artifact

Examples:
- Provider-hosted confirmation page with unique booking reference and full appointment details.
- Provider-generated confirmation email/SMS linked to a known transaction.

**RECOMMENDATION:** May support confirmation for hosted/manual channels, but provenance and parsing quality must be captured.

### Tier D — Synchronous clinic confirmation

Examples:
- Authorized clinic staff confirms exact appointment details by phone.
- Confirmation number/reference captured where available.

Required audit fields:
- timestamp
- dialed clinic identity
- staff name/role if volunteered
- exact confirmed date/time/service/practitioner/location
- reference number if available
- whether any approval-scoped term changed

**RECOMMENDATION:** Can support confirmation when direct digital evidence is unavailable, subject to R6 voice controls.

### Tier E — Weak/supporting evidence only

Examples:
- Calendar event created by BenefitFlow.
- Calendar invite where provider has not accepted.
- Availability screen.
- Form submission success.
- "We'll contact you" message.
- Wait-list enrollment.
- Outbound email sent.
- User says they expect the booking succeeded.

**RECOMMENDATION:** Never independently promote to `CONFIRMED_BOOKED`.

---

## 6. Confirmation rule

BenefitFlow should only set `CONFIRMED_BOOKED` when all of the following are true:

1. Evidence identifies the exact external appointment or an equivalent provider-controlled record.
2. Evidence comes from an authoritative or explicitly accepted confirmation source.
3. Date/time/timezone are resolved.
4. Provider/clinic and service are resolved.
5. Any practitioner substitution is within user-approved scope.
6. Price/deposit/cancellation conditions have not materially changed from the approved proposal, or fresh approval was obtained.
7. Confirmation evidence is persisted with source timestamp and provenance.
8. No higher-confidence evidence currently contradicts the booking.
9. If the adapter receives unordered/duplicated events, the current external state has been reconciled.
10. Calendar synchronization (if used) is downstream of this decision and does not itself cause the decision.

---

## 7. Rescheduling model

### OBSERVED EVIDENCE

Calendly can represent a reschedule as:
- old invitee/event cancelled
- new invitee/event created
- linkage between old and new records

FHIR examples also represent renegotiation and replacement state transitions rather than assuming a simple timestamp edit.

### RECOMMENDATION

Represent rescheduling with explicit lineage:

- `supersedes_transaction_id`
- `superseded_by_transaction_id`
- `reschedule_reason`
- `old_external_booking_id`
- `new_external_booking_id`
- `approval_reused` boolean
- `reapproval_reason` if false
- `effective_at`

Do not overwrite the original booking history.

If the new time/provider/service is outside the user's approved range, enter `REAPPROVAL_REQUIRED` before accepting the replacement.

---

## 8. Cancellation model

Recommended flow:

`CONFIRMED_BOOKED`  
→ `CANCELLATION_PENDING`  
→ `CANCELLED`

or, if ambiguous:

`CANCELLATION_PENDING`  
→ `RECONCILIATION_REQUIRED`

Capture:
- initiator (user/provider/system)
- requested_at
- provider-confirmed cancellation_at
- external version
- reason if available
- fee/penalty impact
- confirmation evidence
- whether calendar cleanup succeeded

### Important distinction

"Cancellation request sent" is not the same as "appointment cancelled."

Square's cancellation API illustrates a strong synchronous path because it returns the cancelled Booking object. Other channels, especially phone/email/web forms, may require delayed confirmation.

---

## 9. Retry, idempotency, duplicate, and ordering requirements

### 9.1 Stable operation ID

Every external mutation should have a BenefitFlow-generated `operation_id` that remains stable across retries.

Store:
- operation ID
- user approval version
- adapter
- action type
- request hash
- first attempt time
- attempt count
- external idempotency key if supported
- external booking ID if learned
- terminal outcome

### 9.2 Adapter idempotency

Where an API supports an idempotency key, reuse the same key for retries of the **same intended mutation**.

Do not generate a new idempotency key after a timeout unless reconciliation has established the first action did not succeed.

Square explicitly supports idempotency keys on booking create/update/cancel.

### 9.3 Ambiguous timeout rule

If a create/update/cancel call times out after transmission:

1. Do not assume failure.
2. Enter `RECONCILIATION_REQUIRED`.
3. Query by external booking ID, operation correlation, or authoritative listing/search where possible.
4. Retry only when duplicate-prevention semantics are understood.

### 9.4 Webhook processing

Square documents:
- duplicate event delivery is possible
- event delivery order is not guaranteed
- retries can continue for up to 24 hours

Therefore:

- persist webhook `event_id`
- validate signature/authenticity before processing
- process idempotently
- never rely on arrival order alone
- prefer external object version/timestamp or read-back state
- keep raw event evidence for audit within retention policy
- run periodic reconciliation for missed events where adapter supports it

### 9.5 Calendar idempotency

Google Calendar lets clients provide an event ID and explicitly notes that doing so can prevent duplicate event creation after ambiguous failures.

**RECOMMENDATION:** Derive a stable calendar projection ID from the BenefitFlow booking/transaction identity. Calendar sync is idempotent projection, not booking authority.

---

## 10. Human recovery conditions

Escalate to a human/operator when any of these occur:

- External action may have succeeded but no authoritative state can be read back.
- Provider reports a booking that BenefitFlow cannot map to the intended transaction.
- Two external records plausibly represent the same attempted booking.
- Webhook state conflicts with current provider read-back.
- Reschedule creates a materially different provider/service/time/cancellation condition.
- Provider requires payment/deposit not covered by authorization.
- Provider requests new sensitive identifiers outside approved disclosure scope.
- A phone/email workflow produces ambiguous wording ("we'll try to fit you in", "we'll call you back").
- Wait-list offer expires mid-transaction.
- A calendar event exists but provider evidence says no booking.
- Cancellation is requested but cannot be confirmed.
- Duplicate booking is suspected.

Human recovery must have a single screen showing:
- approved scope
- attempted actions
- external IDs
- evidence chronology
- current normalized state
- contradictions
- safe next actions

---

## 11. Gap analysis against BenefitFlow beta v0.3.0

### Current model strength

`workflow.py` correctly:
- requires provider verification before proposal creation
- requires user approval before transaction handoff
- stops at `READY_FOR_TRANSACTION_ADAPTER`
- prohibits accepting materially different provider/service/price/cancellation/window terms without fresh approval
- prohibits deposit/claim action without separate authorization

These are strong pre-transaction controls.

### G1 — Booking state stops too early

Current `BookingResult.status` only supports:
- `READY_FOR_TRANSACTION_ADAPTER`
- `DECLINED`

There is no normalized external transaction state after handoff.

**RECOMMENDATION:** Add a separate `BookingTransaction` model instead of overloading `BookingResult`.

### G2 — Booking channel enum is too coarse

Current `Provider.booking_channel`:
- `phone`
- `web`
- `manual`

This cannot distinguish a direct transactional API from a request form or waitlist.

**RECOMMENDATION:** Adopt the channel taxonomy in Section 3.

### G3 — No external booking identity/provenance

Current models have no fields for:
- adapter/provider
- external booking ID
- external status
- external version
- confirmation evidence
- provider-confirmed timestamp
- operation/idempotency key

**RECOMMENDATION:** Add them to a transaction/evidence model.

### G4 — No hold/waitlist representation

Real healthcare scheduling systems expose waitlists and temporary held opportunities.

**RECOMMENDATION:** Model hold and waitlist explicitly; never shoehorn them into appointment confirmation.

### G5 — No reschedule lineage

Current beta has no booking object, so there is no way to preserve old/new booking relationships.

**RECOMMENDATION:** Add immutable transaction lineage.

### G6 — Preferred window is unstructured text

`BookingProposal.preferred_window` is a string.

This creates ambiguity for:
- timezone
- exact user authorization boundary
- permitted days
- permitted start/end times
- earliest/latest dates
- tolerance on appointment shift

**RECOMMENDATION:** Replace or augment with structured constraints:
- timezone
- date range
- allowed weekdays
- time-of-day intervals
- hard/soft preference marker

### G7 — No stale-approval rule

A proposal can theoretically remain approved while provider price/availability/cancellation policy changes.

**RECOMMENDATION:** Bind approval to a proposal version/hash and expiry. Any material mutation triggers `REAPPROVAL_REQUIRED`.

### G8 — No reconciliation state

Distributed booking systems can produce ambiguous outcomes.

**RECOMMENDATION:** `RECONCILIATION_REQUIRED` must be first-class rather than treating adapter errors as simple failure.

---

## 12. Recommended data model additions

### BookingTransaction

Suggested fields:

```text
transaction_id
proposal_id
proposal_version
approval_id
approval_granted_at
approval_expires_at

channel_type
adapter_name
adapter_version

operation_id
external_idempotency_key
external_booking_id
external_parent_booking_id
external_version

normalized_status
external_status_raw
status_observed_at
status_source
status_confidence

provider_id
practitioner_id
service_id
location_id
start_at
end_at
timezone

request_submitted_at
confirmed_at
cancelled_at
fulfilled_at

confirmation_evidence_ids[]
contradiction_ids[]

supersedes_transaction_id
superseded_by_transaction_id

last_reconciled_at
reconciliation_status
human_recovery_required
```

### BookingEvidence

Suggested fields:

```text
evidence_id
transaction_id
evidence_type
source_system
source_uri_or_reference
external_event_id
external_object_id
observed_at
source_timestamp
signature_valid
raw_status
normalized_interpretation
confidence
content_hash
retention_class
```

---

## 13. Minimum event model

Recommended append-only events:

- `PROPOSAL_APPROVED`
- `TRANSACTION_STARTED`
- `REQUEST_SUBMITTED`
- `HOLD_CREATED`
- `HOLD_EXPIRED`
- `WAITLIST_JOINED`
- `WAITLIST_OFFERED`
- `WAITLIST_OFFER_EXPIRED`
- `EXTERNAL_BOOKING_OBSERVED`
- `BOOKING_CONFIRMED`
- `BOOKING_REJECTED`
- `RESCHEDULE_REQUESTED`
- `RESCHEDULE_CONFIRMED`
- `CANCELLATION_REQUESTED`
- `CANCELLATION_CONFIRMED`
- `EXTERNAL_STATUS_CHANGED`
- `WEBHOOK_RECEIVED`
- `WEBHOOK_DUPLICATE_IGNORED`
- `RECONCILIATION_STARTED`
- `RECONCILIATION_RESOLVED`
- `HUMAN_RECOVERY_REQUIRED`
- `NO_SHOW_RECORDED`
- `FULFILLED_RECORDED`

Current state should be derived/reconciled from durable facts, not inferred from a single last message if events can arrive out of order.

---

## 14. Failure and ambiguity taxonomy

### F1 — Availability race
Slot appears available but is taken before booking completes.

**Safe state:** `FAILED_RETRYABLE` or `AWAITING_EXTERNAL_CONFIRMATION`, never confirmed.

### F2 — Request-vs-booking confusion
Web form says "submitted successfully."

**Safe state:** `REQUEST_SUBMITTED`.

### F3 — Waitlist mistaken as booking
User receives "you're on the wait list."

**Safe state:** `WAITLISTED`.

### F4 — Hold mistaken as booking
Temporary/exclusive opening is reserved or offered.

**Safe state:** `SLOT_HOLD_ACTIVE` with expiry.

### F5 — Ambiguous API timeout
Request may have succeeded server-side.

**Safe state:** `RECONCILIATION_REQUIRED`.

### F6 — Duplicate retry
Same logical create is sent again.

**Control:** stable idempotency key; reconcile before new operation.

### F7 — Duplicate webhook
Same external event delivered twice.

**Control:** dedupe by trusted event ID.

### F8 — Out-of-order webhooks
Cancel/update arrives before older create/update event.

**Control:** version/timestamp/read-back reconciliation; never use arrival order as truth.

### F9 — Reschedule split-brain
Old event cancelled, new event created, only one webhook processed.

**Safe state:** `RECONCILIATION_REQUIRED` until linked replacement verified.

### F10 — Calendar divergence
Calendar shows appointment while provider system has no booking or has cancellation.

**Control:** provider booking state outranks calendar projection.

### F11 — Material terms changed
Provider substitutes practitioner/service/price or cancellation condition.

**Safe state:** `REAPPROVAL_REQUIRED`.

### F12 — Cancellation ambiguity
Cancellation request sent but provider status unknown.

**Safe state:** `CANCELLATION_PENDING` / `RECONCILIATION_REQUIRED`.

---

## 15. Recommended tests

### State-semantic tests

1. Form submission cannot become `CONFIRMED_BOOKED`.
2. Waitlist enrollment cannot become `CONFIRMED_BOOKED`.
3. Slot hold expires to non-booked state.
4. Provider API `ACCEPTED` + trusted adapter mapping can become confirmed.
5. Calendar event creation alone cannot become confirmed.
6. Google attendee `needsAction` cannot become provider-confirmed.
7. Conflicting provider evidence blocks confirmation.
8. Cancellation request does not equal cancellation confirmation.
9. Reschedule preserves old/new lineage.
10. Material reschedule change triggers reapproval.

### Idempotency/recovery tests

11. Create timeout + successful external creation does not produce duplicate on retry.
12. Duplicate webhook event ID is processed once.
13. Newer external version followed by older webhook does not roll state backward.
14. Missed webhook is repaired by reconciliation/read-back.
15. Cancellation retry uses same idempotency operation where supported.
16. Calendar projection retry does not duplicate the event.
17. Concurrent updates trigger version conflict and recovery rather than overwrite.
18. Adapter returns unknown status -> `RECONCILIATION_REQUIRED`.

### Human-recovery tests

19. Phone agent says "we'll call back" -> pending, not confirmed.
20. Phone agent verbally confirms exact slot -> confirmation evidence captured.
21. Clinic requests deposit beyond approval -> stop and reapprove.
22. Waitlist offer expires during flow -> no booking claim.
23. Duplicate external bookings suspected -> human recovery.
24. Provider cancels out-of-band -> normalized cancellation after evidence/reconciliation.

---

## 16. Implementation priorities

### P0 — Must exist before any live booking adapter

1. Separate proposal authorization from external transaction state.
2. Add `REQUEST_SUBMITTED`, `WAITLISTED`, `SLOT_HOLD_ACTIVE`, `CONFIRMED_BOOKED`, `CANCELLATION_PENDING`, `CANCELLED`, and `RECONCILIATION_REQUIRED`.
3. Add external booking ID + confirmation evidence persistence.
4. Enforce "calendar is not confirmation."
5. Stable operation/idempotency identity.
6. Reapproval when material terms change.
7. Human recovery for ambiguous external outcomes.

### P1 — Required for robust API adapters

1. Webhook signature verification.
2. Webhook event deduplication.
3. Out-of-order/version-aware reconciliation.
4. Periodic reconciliation/read-back.
5. Reschedule lineage.
6. Adapter-specific status mapping tests.

### P2 — Operational maturity

1. Recovery dashboard.
2. SLA/timeout policies by channel.
3. Metrics for pending duration, ambiguity rate, duplicate prevention, reconciliation success, and human-recovery burden.
4. Provider/channel reliability scoring based on observed transaction outcomes.

---

## 17. Product wording implications

BenefitFlow UI should use precise language:

### Safe wording before confirmation

- "Booking request sent"
- "Waiting for clinic confirmation"
- "You're on the wait list"
- "A slot is temporarily held until [time]"
- "The clinic offered this time; it is not confirmed yet"
- "We're reconciling the booking status before showing it as confirmed"

### Wording reserved for authoritative confirmation

- "Appointment confirmed"
- "Booked for [date/time]"
- "Clinic confirmed [provider/service/location]"

Do not display "Booked" merely because:
- availability was found
- a form was submitted
- a call was placed
- an email was sent
- a calendar event was created
- a waitlist request was accepted
- an adapter timed out after submission

---

## 18. Contradictions and unresolved unknowns

### C1 — Vendor status vocabularies are not equivalent
FHIR uses healthcare-neutral states; Square uses its own booking status values; Calendly uses invitee/event semantics; Jane exposes UX-level booking/waitlist behavior.

**Disposition:** Do not force raw vendor statuses into a shared enum without adapter-specific mapping and tests.

### C2 — "Created" can mean different things
Microsoft/Square creation endpoints create booking resources. Calendly `invitee.created` indicates scheduling. A generic web form may create only a request.

**Disposition:** `created` is not a universal confirmation signal.

### U1 — API availability across BenefitFlow's target clinic market
Not established. Many clinics may expose only hosted booking or phone workflows.

### U2 — Provider-specific booking terms
Deposit requirements, cancellation windows, intake prerequisites, and practitioner substitution vary and require R3/R6/R10 integration.

### U3 — Exact legal/audit retention requirements
Out of R4 scope; route to R5.

### U4 — Voice confirmation evidence requirements
R4 identifies required scheduling facts; recording/consent and call-evidence policy belongs to R6/R5.

### U5 — Commercial API rights
Public docs establish technical behavior, not BenefitFlow's contractual ability to use each API.

---

## 19. What this evidence does NOT establish

This packet does **not** establish that:

- FHIR is implemented by all BenefitFlow target providers.
- Square, Calendly, Jane, Microsoft Bookings, or Google Calendar will be production dependencies.
- A particular clinic supports any specific API.
- A public availability display is accurate at transaction time.
- Provider-issued email/SMS is always sufficient confirmation without additional provenance checks.
- Phone confirmation can be automated without additional privacy/consent/legal work.
- Any live booking should occur without the existing user approval gate.

The evidence establishes the **need for semantic separation, evidence-based confirmation, idempotent mutation handling, and reconciliation** regardless of which adapters are ultimately chosen.

---

## 20. Recommended manager decision

**Recommendation:** `SUPPORTED_FOR_ARCHITECTURAL_INTEGRATION`, subject to R3/R5/R6/R10 cross-lane reconciliation.

Specific proposed Primary-facing decisions:

1. Preserve the current pre-transaction approval boundary.
2. Add a new `BookingTransaction` domain model rather than extending `BookingResult` into an overloaded object.
3. Adopt a provider-independent state machine that explicitly separates request, hold, waitlist, and confirmed booking.
4. Require confirmation evidence before `CONFIRMED_BOOKED`.
5. Treat calendar writes as downstream projections.
6. Require stable operation IDs/idempotency strategy and first-class reconciliation state.
7. Preserve immutable reschedule/cancellation lineage.
8. Block live adapter rollout until ambiguity/retry/duplicate/out-of-order tests pass.
