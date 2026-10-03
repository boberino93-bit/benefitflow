# R4 Evidence Packet 001 — Booking Channels and Confirmation Semantics

Project: BenefitFlow  
Project ID: `benefitflow`  
Agent: `researcher-r4-booking-channels-20261003T2224Z`  
Assignment: R4 — Booking Channels and Confirmation Semantics  
Prepared lane: `provider-discovery-booking`  
Status: RESEARCH EVIDENCE / NOT ACCEPTED STATE  
Retrieved: 2026-10-03

## Research question

What booking-channel types and transaction states must BenefitFlow distinguish so that it never represents an appointment as booked when it has only observed availability, submitted a request, opened a hosted booking page, or encountered an ambiguous provider response?

## Observed evidence

### E1 — Sun Life Provider Search distinguishes booking from appointment requests

Source: Sun Life, “Provider Search and Profiles”  
URL: https://www.sunlife.ca/sl/provider/en/support/faqs/provider-search-and-profiles/  
Freshness: retrieved 2026-10-03; page current at retrieval.  
Jurisdiction/applicability: Canada; provider discovery/connect workflow.

Observed:
- Sun Life instructs users to connect to providers using either **“book now”** or **“request an appointment”**, and says the available option depends on the provider profile.
- Sun Life says Provider Search itself is not a clinic/practice and its support team does not have patient information or clinic booking history.

Interpretation:
- A discovery platform can expose multiple downstream transaction semantics under a single “booking” user journey.
- `REQUESTED` must not be collapsed into `CONFIRMED`.
- An intermediary may be unable to independently verify downstream booking history unless it receives explicit confirmation evidence.

Confidence: high for the observed Sun Life behavior.

### E2 — Displayed availability is not authoritative confirmation

Source: Sun Life Provider Search public search/disclaimer  
URL: https://providersearch.sunlife.ca/en/  
Freshness: retrieved 2026-10-03.  
Jurisdiction/applicability: Canada.

Observed:
- Sun Life displays next-available appointment information for select providers.
- Its disclaimer states that next-available appointments are for information purposes only and may not apply to specific services or client types.
- It also states that provider-supplied extended-profile information is not guaranteed to be error-free or comprehensive.

Interpretation:
- `AVAILABILITY_OBSERVED` is evidence for a proposal, not proof that the user can successfully book that slot.
- BenefitFlow should attach source, observation timestamp, service/provider context, and a freshness window to availability signals.

Confidence: high for the product-semantics implication.

### E3 — Jane hosted booking is real-time, but Jane does not expose an open booking-write API

Sources:
- Jane, “Online Booking”  
  https://jane.app/features/online-booking
- Jane, “Integrations Hub & FAQ”  
  https://jane.app/guide/integrations-hub-faq
- Jane, “Jane Integrations: Our Program, Our Partners, and How to Work with Us” (2026-04-01)  
  https://jane.app/blog/jane-integrations-our-program-our-partners-and-how-to-work-with-us
- Jane partner application  
  https://integrations.jane.app/application_forms/jane-integrations-partner-interest-form/partner_applications/new

Observed:
- Jane advertises real-time online booking through clinic-hosted Jane booking pages.
- Jane states it does not provide an open API/API keys.
- In its April 2026 integration-program announcement, Jane describes an approval-based partner API pathway rather than a public API.
- Jane states that its partner API currently supports reading patient, appointment, and treatment data and writing to charting, but does **not** yet support appointment creation, modification, or deletion.
- Jane also states that it is not currently looking to work with AI scheduling tools and that posting directly into Jane calendars is not supported.
- Jane provides clinic/practitioner hosted booking URLs/buttons and supports Reserve with Google.

Interpretation:
- For Jane-backed clinics, BenefitFlow should default to `HOSTED_BOOKING_HANDOFF` or user-guided booking unless/until BenefitFlow obtains an approved integration with appointment-write capability.
- Browser scraping, credential sharing, or pretending an unsupported write integration exists would be an unsafe architecture.
- “Real-time availability” on a Jane booking page does not automatically imply BenefitFlow itself can atomically reserve a slot.

Confidence: high for current public Jane integration constraints; future partner capabilities can change and require re-verification.

### E4 — Cliniko exposes a public API with appointment write/cancel operations and availability controls

Sources:
- Cliniko API overview / booking docs  
  https://docs.api.cliniko.com/openapi/reference/overview  
  https://docs.api.cliniko.com/openapi/reference/booking  
  https://docs.api.cliniko.com/openapi/service

Observed:
- Cliniko publishes a REST API.
- The API includes create/update/cancel-style operations for individual appointments and endpoints for available times.
- Available-time responses respect clinic-configured booking constraints such as maximum appointments per day segment and minimum advance booking time.
- API credentials provide access to sensitive information and are documented as secrets that must be protected.

Interpretation:
- Some practice-management systems can support a true transaction adapter, but availability and booking remain provider-configured and adapter-specific.
- A successful adapter should persist the provider-system appointment identifier and authoritative status returned by the system.
- BenefitFlow must not generalize one vendor’s API capabilities to another vendor.

Confidence: high for Cliniko API capability at retrieval.

### E5 — NexHealth explicitly separates appointment creation, confirmation, and cancellation

Sources:
- NexHealth API, “Appointments”  
  https://docs.nexhealth.com/reference/appointments-1
- NexHealth API, “Create appointment”  
  https://docs.nexhealth.com/reference/postappointments

Observed:
- NexHealth documents appointment creation, confirmation, and cancellation as distinct operations.
- Its create endpoint inserts a future appointment into the connected health-record system for a provider/location.

Interpretation:
- Even API-capable booking systems can expose multiple lifecycle operations that should map to explicit BenefitFlow states and event evidence.
- A create response is stronger confirmation evidence than a discovery-page slot, but BenefitFlow should still retain the external identifier and reconcile uncertain transport failures.

Confidence: high for the documented API semantics.

## Booking channel taxonomy recommendation

Use an explicit `booking_channel_type` rather than a generic “online booking” flag:

1. `FIRST_PARTY_TRANSACTION_API`
   - BenefitFlow/approved adapter can create/read/cancel/reschedule an appointment in the authoritative provider system.
   - Strongest path for deterministic automation.

2. `RESTRICTED_PARTNER_API`
   - Transaction access exists only under vendor approval/partnership and may expose read-only or partial write scopes.
   - Capability must be discovered per partner grant, not assumed.

3. `HOSTED_BOOKING_PAGE`
   - Provider/vendor owns the interactive booking page.
   - BenefitFlow may deep-link or hand off but should not claim booking completion until independent confirmation evidence is captured.

4. `AGGREGATOR_BOOK_NOW`
   - Discovery intermediary offers a “book now” action.
   - Must determine whether it is a true booking, redirect, embedded vendor flow, or request workflow.

5. `APPOINTMENT_REQUEST_FORM`
   - Submission expresses requested date/time/preferences but requires provider acceptance.
   - Terminal success state is `REQUESTED`, not `CONFIRMED`.

6. `PHONE`
   - Human or authorized voice transaction with clinic staff.
   - Confirmation must capture appointment details and a reliable evidence record.

7. `EMAIL_OR_MESSAGE`
   - Asynchronous request/coordination.
   - Remains `REQUESTED` until provider confirmation is received.

8. `WAITLIST`
   - User is eligible to be contacted for a future slot; no appointment exists yet.

9. `UNSUPPORTED_OR_UNKNOWN`
   - Discovery is possible but no reliable transaction semantics have been established.
   - Route to user/human recovery.

## Recommended transaction state model

Keep availability, approval, execution, and confirmation separate.

```text
DISCOVERED
  -> AVAILABILITY_OBSERVED
  -> SLOT_PROPOSED
  -> USER_APPROVED
  -> TRANSACTION_INITIATED
      -> HOSTED_HANDOFF
      -> REQUESTED
      -> HELD
      -> CONFIRMED
      -> WAITLISTED
      -> FAILED
      -> AMBIGUOUS
      -> NEEDS_HUMAN

CONFIRMED
  -> CANCEL_REQUESTED -> CANCELLED | CANCELLATION_AMBIGUOUS | NEEDS_HUMAN
  -> RESCHEDULE_REQUESTED -> CONFIRMED(new external appointment) | AMBIGUOUS | NEEDS_HUMAN

REQUESTED / HELD / WAITLISTED / AMBIGUOUS
  -> CONFIRMED | EXPIRED | DECLINED | FAILED | NEEDS_HUMAN
```

Critical invariant:
- Only `CONFIRMED` may be shown to the user as “booked.”
- `HOSTED_HANDOFF`, `REQUESTED`, `HELD`, `WAITLISTED`, and `AVAILABILITY_OBSERVED` require wording that clearly describes their weaker status.

## Confirmation evidence requirements

Recommended minimum evidence tiers:

### Tier A — authoritative API confirmation
- provider/vendor system
- external appointment ID
- authoritative status
- provider + clinic/location
- appointment type/service
- start/end time and timezone
- response timestamp
- adapter correlation/transaction ID

### Tier B — authoritative hosted-flow confirmation
- provider/vendor confirmation page, confirmation message, or other first-party receipt
- clinic/provider, service, date/time, and confirmation identifier when present
- captured timestamp and source

### Tier C — provider staff confirmation
- clinic identity
- staff-confirmed appointment details
- timestamp
- bounded audit record sufficient to distinguish confirmation from a callback/request

### Non-confirming evidence
The following are never sufficient by themselves:
- search result or next-available display
- “request sent”
- waitlist enrollment
- outbound email sent
- phone call placed with no confirmed details
- hosted booking page opened
- payment authorization without appointment confirmation

## Retry, reconciliation, and idempotency recommendations

1. Generate a BenefitFlow `transaction_intent_id` before any external write.
2. Use provider-supported idempotency keys when available.
3. Persist every external request/response correlation ID and returned appointment ID.
4. On timeout or transport ambiguity, **reconcile before retrying**:
   - query appointment state when API supports it;
   - otherwise route to human/user confirmation rather than blindly submitting again.
5. Prevent duplicate retries using a conservative dedupe key over:
   - provider/clinic
   - appointment type
   - intended patient/session identity held inside the transaction boundary
   - requested time window
   - active transaction intent
6. Cancellation/rescheduling should read current state before mutation where the adapter allows it.
7. If a hosted/manual channel cannot support reliable reconciliation, mark it `AMBIGUOUS`/`NEEDS_HUMAN` instead of guessing.

## Human-recovery triggers

Route to human/user recovery when:
- the booking channel is request-only and provider acceptance has not arrived;
- a write request times out and authoritative state cannot be queried;
- the same slot/provider appears to have conflicting states;
- the provider changes date/time/service during manual confirmation;
- an integration is read-only or prohibits appointment creation;
- required clinic-specific intake, eligibility, new-patient, referral, or service rules cannot be established;
- a hosted page reports success without enough details to bind it to the approved proposal;
- cancellation/rescheduling status is unclear.

## Implementation implications for BenefitFlow beta

1. Replace any generic `booking_status` boolean with explicit state + evidence.
2. Add `booking_channel_type`, `external_system`, `external_appointment_id`, `transaction_intent_id`, `confirmation_evidence_type`, `observed_at`, and `last_reconciled_at`.
3. Require provider/service/time proposal equality checks before applying external confirmation to the approved transaction.
4. Hosted-page handoff should be a bounded action that returns to a reconciliation step; it must not auto-mark the appointment as booked.
5. Adapter capability discovery should be versioned and vendor-specific.
6. The user approval card should say exactly what BenefitFlow is authorized to do:
   - “open booking page,”
   - “submit appointment request,” or
   - “book this exact appointment,”
   rather than using one generic “Book” action.

## Contradictions / unresolved unknowns

- Public Sun Life material proves that both “book now” and “request appointment” exist, but does not establish the technical mechanism behind every provider’s “book now” path.
- Jane’s 2026 partner program is evolving. Its public material currently restricts appointment write access and says it is not looking for AI scheduling integrations, but this could change and must be re-verified before implementation.
- Cliniko and NexHealth demonstrate technically writable appointment systems, but public documentation does not establish that any particular BenefitFlow target clinic uses them or would authorize BenefitFlow access.
- Cancellation/rescheduling semantics, required intake forms, deposits, new-patient restrictions, and insurance-specific eligibility checks vary by clinic/vendor and need adapter-specific evidence.
- No evidence in this packet establishes a universal booking API across Canadian providers.

## Recommended next tests / decisions

1. Add state-machine unit tests proving that `REQUESTED`, `HOSTED_HANDOFF`, `HELD`, and `WAITLISTED` never render as “booked.”
2. Add an ambiguous-timeout integration test that confirms the adapter reconciles before retry.
3. Add adapter capability metadata tests for read-only vs create vs cancel/reschedule.
4. Create synthetic fixtures for:
   - API-confirmed appointment,
   - hosted booking handoff,
   - request-only form,
   - phone confirmation,
   - waitlist,
   - timeout after write,
   - cancellation ambiguity.
5. Review BenefitFlow’s approval-card copy against the three authorization verbs above.
6. Manager/Primary should decide whether Jane-backed clinics are a pilot dependency; if so, partner-access feasibility is a business-development constraint, not merely an engineering task.

## What this evidence does not establish

- It does not establish that BenefitFlow is authorized to access any vendor API.
- It does not establish that displayed availability is reservable.
- It does not establish that insurer/provider discovery systems provide universal write access.
- It does not establish legal permission to record calls or store clinical data.
- It does not establish that a user’s benefits plan covers a discovered provider or service.
- It does not promote any recommendation here into accepted project state.
