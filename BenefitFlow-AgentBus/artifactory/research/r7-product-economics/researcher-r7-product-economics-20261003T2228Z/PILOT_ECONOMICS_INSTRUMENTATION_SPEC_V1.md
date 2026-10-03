# R7 Pilot Economics Instrumentation Specification v1

Project: BenefitFlow (`project_id=benefitflow`)  
Agent: `researcher-r7-product-economics-20261003T2228Z`  
Assignment: R7 — Product Economics and Operational Feasibility  
Status: RESEARCH RECOMMENDATION / NOT ACCEPTED STATE  
Date: 2026-10-03

## Purpose

Define the minimum event, timing, channel, exception, and cost instrumentation BenefitFlow needs before it can make credible claims about:

- cost per normalized plan;
- cost per provider shortlist;
- cost per booking attempt;
- cost per confirmed booking;
- straight-through automation rate;
- human-support burden;
- exception/reconciliation burden;
- unit economics by provider system and booking channel;
- contribution margin under any future pricing model.

This specification is deliberately separate from the production domain model. It is an observability/economics layer. It must not become a reason to duplicate sensitive member identifiers into analytics.

## Current-beta audit

The current beta exposes useful workflow boundaries but has almost no economics instrumentation.

### Existing callable boundaries

`benefitflow_beta/app.py` exposes:

- `/api/parse-text`
- `/api/parse-file`
- `/api/plan`
- `/api/providers`
- `/api/providers/verify`
- `/api/booking/propose`
- `/api/booking/approve`

These are natural event boundaries for pilot measurement.

### Existing workflow boundaries

`benefitflow_beta/workflow.py` currently separates:

1. provider verification;
2. proposal creation;
3. user approval/decline;
4. the `READY_FOR_TRANSACTION_ADAPTER` boundary.

That separation is useful, but it does not currently record:

- start/end timestamps for an economic activity;
- elapsed or active human time;
- channel type;
- provider-system type;
- data/API operations;
- paid communications usage;
- failure/exception reason;
- reconciliation work;
- whether a booking was eventually confirmed;
- whether the same case was touched repeatedly;
- cost attribution.

### Current status limitation

`BookingResult.status` currently ends at:

- `READY_FOR_TRANSACTION_ADAPTER`
- `DECLINED`

Therefore the beta cannot currently measure the downstream denominator that matters most to R7:

> authoritative confirmed booking outcomes and the work required to get there.

Until a transaction model is implemented, economics instrumentation should treat `READY_FOR_TRANSACTION_ADAPTER` as a handoff event only, never as a completed booking.

## Instrumentation principles

1. **Measure activities, not only API endpoints.**
   A single booking attempt may span provider search, verification, phone calls, hosted handoff, retries, and reconciliation.

2. **Use pseudonymous workflow IDs, not member/plan identifiers.**
   Analytics does not need raw plan number, certificate/member ID, date of birth, health details, or claim identifiers.

3. **Separate wall-clock latency from human touch time.**
   Waiting two hours for a clinic reply is operationally different from two hours of staff labour.

4. **Track channel/provider-system dimensions.**
   Averages across API, hosted-page, phone, email, and unsupported flows will hide the scalable and unscalable parts of the product.

5. **Track negative work.**
   Failed searches, dead ends, stale availability, duplicate-risk reconciliation, and unsupported integrations consume real cost.

6. **Never infer confirmation from a request or handoff.**
   Economics denominators must use the same booking-state semantics as R4/R6.

7. **Keep fixed and variable costs separate.**
   Security, privacy, legal, vendor onboarding, and integration certification are not per-booking API costs.

## Proposed identifiers

### `journey_id`

One pseudonymous end-to-end user objective, such as:

- "use physiotherapy benefit";
- "find and book massage therapy";
- "review annual benefits and create utilization plan".

Properties:

- opaque random ID;
- no embedded user/member identifier;
- stable across all activities for the objective;
- can span multiple provider candidates and booking attempts.

### `activity_id`

One measurable unit of work.

Examples:

- one parsing execution;
- one provider-search pass;
- one provider verification;
- one booking attempt;
- one reconciliation action.

### `booking_intent_id`

Stable identifier for one approved attempt to obtain one appointment under materially fixed terms.

Do not reuse after a material change requiring fresh user approval.

### `provider_candidate_id`

Opaque internal candidate identity used for analytics joins.

Do not use raw license numbers, phone numbers, or insurer identifiers as analytics keys.

## Canonical economics event envelope

Recommended minimum envelope:

```json
{
  "schema": "benefitflow/economics-event/v1",
  "event_id": "opaque-unique-id",
  "occurred_at": "RFC3339 UTC",
  "journey_id": "opaque-id",
  "activity_id": "opaque-id",
  "booking_intent_id": "optional-opaque-id",
  "event_type": "enum",
  "workflow_stage": "enum",
  "booking_channel_type": "enum-or-null",
  "external_system_type": "enum-or-null",
  "provider_candidate_id": "opaque-or-null",
  "outcome": "enum",
  "reason_code": "enum-or-null",
  "wall_clock_ms": 0,
  "active_human_ms": 0,
  "automated_compute_ms": 0,
  "api_call_count": 0,
  "data_lookup_count": 0,
  "voice_seconds": 0,
  "sms_segments": 0,
  "email_messages": 0,
  "retry_count": 0,
  "reconciliation_count": 0,
  "estimated_variable_cost_micros": 0,
  "synthetic": true
}
```

Amounts should use integer micros or minor currency units rather than binary floating point.

## Event taxonomy

### Plan normalization

- `PLAN_PARSE_STARTED`
- `PLAN_PARSE_SUCCEEDED`
- `PLAN_PARSE_FAILED`
- `PLAN_PARSE_MANUAL_REVIEW_REQUIRED`
- `PLAN_MODEL_BUILT`
- `PLAN_OPTIMIZATION_STARTED`
- `PLAN_OPTIMIZATION_SUCCEEDED`
- `PLAN_OPTIMIZATION_FAILED`

Economic questions answered:

- how many parse attempts are required per usable plan;
- how often ambiguity creates manual work;
- how much human review time is consumed before provider research begins.

### Provider research

- `PROVIDER_SEARCH_STARTED`
- `PROVIDER_CANDIDATE_FOUND`
- `PROVIDER_CANDIDATE_REJECTED`
- `PROVIDER_ENRICHMENT_REQUESTED`
- `PROVIDER_ENRICHMENT_COMPLETED`
- `PROVIDER_VERIFICATION_STARTED`
- `PROVIDER_VERIFICATION_SUCCEEDED`
- `PROVIDER_VERIFICATION_INCONCLUSIVE`
- `PROVIDER_VERIFICATION_FAILED`
- `AVAILABILITY_OBSERVED`
- `AVAILABILITY_STALE`
- `AVAILABILITY_REFRESHED`

Economic questions answered:

- paid lookups per viable candidate;
- number of candidates researched per final shortlist;
- human minutes per verified candidate;
- source-specific contradiction and staleness cost.

### Proposal and approval

- `BOOKING_PROPOSAL_CREATED`
- `BOOKING_PROPOSAL_PRESENTED`
- `BOOKING_PROPOSAL_APPROVED`
- `BOOKING_PROPOSAL_DECLINED`
- `BOOKING_PROPOSAL_EXPIRED`
- `FRESH_APPROVAL_REQUIRED`

Economic questions answered:

- how much research is abandoned before transaction;
- how often material changes force rework;
- cost per approved opportunity rather than cost per raw search.

### Transaction execution

- `TRANSACTION_ATTEMPT_STARTED`
- `HOSTED_HANDOFF_OPENED`
- `APPOINTMENT_REQUEST_SUBMITTED`
- `PHONE_CALL_STARTED`
- `PHONE_CALL_ENDED`
- `EMAIL_REQUEST_SENT`
- `WAITLIST_JOINED`
- `SLOT_HELD`
- `BOOKING_CONFIRMED`
- `TRANSACTION_FAILED`
- `TRANSACTION_AMBIGUOUS`
- `HUMAN_RECOVERY_STARTED`
- `HUMAN_RECOVERY_COMPLETED`

Economic questions answered:

- confirmation rate by channel;
- manual minutes per channel;
- ambiguity rate;
- cost of exception recovery;
- straight-through confirmation rate.

### Post-booking

- `CANCELLATION_REQUESTED`
- `CANCELLATION_CONFIRMED`
- `RESCHEDULE_REQUESTED`
- `RESCHEDULE_CONFIRMED`
- `POST_BOOKING_SUPPORT_CONTACT`
- `APPOINTMENT_COMPLETION_REPORTED`

Economic questions answered:

- downstream support burden;
- true cost of a "successful" booking after cancellation/reschedule work;
- whether pricing based only on initial confirmation understates service cost.

## Required channel dimension

Use explicit values compatible with R4 concepts:

- `FIRST_PARTY_TRANSACTION_API`
- `RESTRICTED_PARTNER_API`
- `HOSTED_BOOKING_PAGE`
- `AGGREGATOR_BOOK_NOW`
- `APPOINTMENT_REQUEST_FORM`
- `PHONE`
- `EMAIL_OR_MESSAGE`
- `WAITLIST`
- `UNSUPPORTED_OR_UNKNOWN`

Never use only `online=true/false`.

## External-system capability dimension

Recommended analytics-only categories:

- `PRACTICE_MANAGEMENT_SYSTEM`
- `INSURER_OR_ECLAIMS_RAIL`
- `PROVIDER_DIRECTORY`
- `REGULATOR_REGISTRY`
- `MAPS_OR_PLACES_DATA`
- `TELEPHONY_PROVIDER`
- `MESSAGING_PROVIDER`
- `MANUAL_CLINIC_CONTACT`
- `UNKNOWN`

Separately record a versioned capability snapshot when known:

- read availability;
- create appointment;
- read appointment confirmation;
- cancel;
- reschedule;
- webhook/event support;
- partner approval required;
- commercial terms known.

## Human-time instrumentation

### Required split

Do not log one generic `manual_minutes`.

Track:

- `human_research_ms`
- `human_verification_ms`
- `human_booking_ms`
- `human_reconciliation_ms`
- `human_support_ms`

Why:

- each category has different automation opportunities;
- a product can reduce booking call time while still losing money on provider verification;
- exception reconciliation is likely to have a long-tail distribution.

### Active-time rule

Count active operator attention, not passive waiting.

Examples:

- listening to IVR/hold while the operator must remain engaged: active;
- waiting overnight for an email response: wall clock only;
- researching an alternate provider after a failure: active research;
- reviewing an ambiguous response to determine retry safety: reconciliation.

## Reason-code taxonomy

### Provider research

- `NO_CANDIDATES`
- `SOURCE_NOT_AUTHORITATIVE`
- `SOURCE_STALE`
- `IDENTITY_CONFLICT`
- `LICENSURE_UNRESOLVED`
- `PAYER_PARTICIPATION_UNKNOWN`
- `PLAN_ELIGIBILITY_UNKNOWN`
- `AVAILABILITY_STALE`
- `SERVICE_MISMATCH`
- `LOCATION_MISMATCH`
- `NEW_PATIENT_NOT_ACCEPTED`

### Booking/transaction

- `CHANNEL_UNSUPPORTED`
- `PARTNER_ACCESS_REQUIRED`
- `WRITE_CAPABILITY_UNAVAILABLE`
- `HOSTED_USER_ACTION_REQUIRED`
- `CLINIC_CALLBACK_REQUIRED`
- `WAITLIST_ONLY`
- `SLOT_NO_LONGER_AVAILABLE`
- `PRICE_CHANGED`
- `PROVIDER_CHANGED`
- `SERVICE_CHANGED`
- `TIME_CHANGED`
- `CANCELLATION_TERMS_CHANGED`
- `FRESH_APPROVAL_REQUIRED`
- `TRANSPORT_TIMEOUT`
- `AMBIGUOUS_EXTERNAL_STATE`
- `DUPLICATE_RISK`
- `AUTHENTICATION_REQUIRED`
- `SENSITIVE_DISCLOSURE_NOT_AUTHORIZED`
- `CLINIC_DECLINED`
- `USER_DECLINED`
- `USER_ABANDONED`

### Support

- `USER_CONFUSION`
- `BOOKING_STATUS_QUESTION`
- `CANCELLATION_HELP`
- `RESCHEDULE_HELP`
- `BILLING_OR_COVERAGE_QUESTION`
- `DATA_CORRECTION`
- `SECURITY_OR_IDENTITY_RECOVERY`
- `OTHER`

## Cost attribution fields

Each measurable vendor/operation event should optionally carry:

```json
{
  "cost": {
    "currency": "USD",
    "amount_micros": 14000,
    "cost_type": "VOICE|SMS|PLACE_DATA|MODEL|PARTNER_FEE|OTHER",
    "pricing_source": "list|contract|estimated|unknown",
    "price_version_observed_at": "RFC3339 UTC"
  }
}
```

Rules:

- `unknown` is valid and preferable to fake zero;
- partner pricing that has not been obtained must remain unknown;
- provider-facing "free" services must not be normalized to zero-cost BenefitFlow integration without evidence;
- FX conversion should be reported separately from source-currency spend.

## Labour-cost handling

Do not bake one salary assumption into telemetry.

Store time; apply labour-rate scenarios later.

Recommended reporting scenarios:

- low loaded-rate scenario;
- expected loaded-rate scenario;
- high loaded-rate scenario.

This permits sensitivity analysis without rewriting historical telemetry.

Formula:

```text
human_cost =
  active_human_hours
  * selected_loaded_hourly_rate
```

## KPI definitions

### Straight-through confirmation rate

```text
confirmed bookings requiring zero human activity after approval
/
all confirmed bookings
```

### Automated-or-user-handoff completion rate

```text
confirmed bookings completed through API or hosted self-service
/
all confirmed bookings
```

Keep this separate from straight-through automation because hosted user completion may have low BenefitFlow labour but is not automated booking by BenefitFlow.

### Human minutes per confirmed booking

```text
sum(active human time for journeys ending in confirmation)
/
confirmed bookings
```

Also report p50, p75, p90, p95.

A mean alone will hide expensive exception tails.

### Exception rate

```text
booking intents entering HUMAN_RECOVERY or TRANSACTION_AMBIGUOUS
/
all transaction attempts
```

### Reconciliation burden

Report:

- reconciliations per 100 attempts;
- mean and p95 reconciliation minutes;
- percent resolved without user contact;
- percent resolved without duplicate external mutation.

### Cost per confirmed booking

```text
sum(variable vendor costs + model costs + scenario labour costs + variable support)
/
confirmed bookings
```

Report by:

- booking channel;
- external provider system;
- benefit/service category;
- geography/jurisdiction when non-identifying;
- new vs returning provider relationship.

### Research yield

```text
verified shortlist candidates
/
provider candidates researched
```

Pair with:

```text
human research minutes
/
verified shortlist candidates
```

### Availability waste

```text
candidate availability observations that expire or invalidate before transaction
/
all availability observations used in proposals
```

This quantifies the cost of stale/perishable discovery.

## Funnel denominators

The beta should preserve distinct counts for:

1. normalized plans;
2. utilization plans;
3. provider-search journeys;
4. provider candidates researched;
5. verified candidates;
6. proposals presented;
7. proposals approved;
8. transaction attempts;
9. appointment requests;
10. authoritative confirmations;
11. cancellations/reschedules;
12. completed appointments when known.

Do not report "booking conversion" without naming the numerator and denominator.

## Mapping to current beta code

### `app.py`

Instrument request-level boundaries around:

- parse endpoints;
- plan endpoint;
- provider listing/search endpoint;
- provider verification endpoint;
- booking proposal endpoint;
- booking approval endpoint.

Recommended properties:

- route name;
- activity ID;
- success/error classification;
- elapsed compute/wall time;
- synthetic flag.

Do not record raw uploaded file text, plan numbers, member IDs, or request bodies in economics telemetry.

### `workflow.verify_provider()`

Add economics events for:

- verification started;
- verification result;
- verification source type;
- active human time if manual;
- lookup counts;
- reason code on inconclusive/failure.

Current synthetic verification must remain clearly `synthetic=true`.

### `workflow.create_proposal()`

Record:

- verification reuse vs fresh verification;
- proposal created;
- provider candidate ID;
- expected price band or cost bucket if useful.

Do not copy raw member/plan identifiers into analytics.

### `workflow.approve_proposal()`

Record:

- approved/declined;
- time from proposal presentation to decision when presentation timestamp exists;
- fresh-approval requirement when material terms change.

`READY_FOR_TRANSACTION_ADAPTER` should emit a handoff event, not a booking-confirmed event.

### Future transaction adapter

Must become the main source for:

- channel type;
- API/voice/message usage;
- external transaction status;
- ambiguity;
- reconciliation;
- authoritative confirmation;
- cancellation/reschedule effort.

## Minimal pilot event store

A pilot could use an append-only economics-events table separate from workflow storage.

Suggested logical schema:

```text
economics_events
- event_id
- occurred_at
- journey_id
- activity_id
- booking_intent_id nullable
- event_type
- workflow_stage
- channel_type nullable
- external_system_type nullable
- provider_candidate_id nullable
- outcome
- reason_code nullable
- wall_clock_ms
- active_human_ms
- automated_compute_ms
- api_call_count
- data_lookup_count
- voice_seconds
- sms_segments
- email_messages
- retry_count
- reconciliation_count
- variable_cost_currency nullable
- variable_cost_micros nullable
- cost_type nullable
- pricing_source nullable
- synthetic
```

This is intentionally event-oriented rather than a mutable aggregate row so later calculations can be reproduced.

## Privacy and security constraints

Economics telemetry should explicitly prohibit:

- raw plan number;
- raw member/certificate ID;
- health diagnosis;
- claim number;
- date of birth;
- full address;
- provider authentication credentials;
- insurer credentials;
- phone-call raw audio/transcript by default;
- free-text notes that could accidentally contain sensitive data.

Use structured reason codes over free text.

Where a user/account join is needed for cohort analysis, use a purpose-limited pseudonymous subject key controlled by the production privacy/security design, not by research agents.

## Pilot dashboard requirements

Minimum views:

### 1. Funnel

Shows counts and conversion between:

`plan -> search -> verified provider -> proposal -> approval -> attempt -> confirmed`

### 2. Human-work waterfall

Human minutes split into:

- research;
- verification;
- booking;
- reconciliation;
- support.

### 3. Channel economics

For every channel:

- attempts;
- confirmations;
- confirmation rate;
- p50/p95 human minutes;
- variable cost;
- ambiguity rate;
- cancellation/reschedule burden.

### 4. Provider-system economics

For every known system/vendor:

- capability class;
- volume;
- manual touch;
- confirmation rate;
- exception rate;
- commercial terms status.

### 5. Exception Pareto

Top reason codes by:

- count;
- human minutes;
- variable cost;
- abandoned journeys.

This should determine what to automate next.

## Pilot decision gates proposed for manager/Primary consideration

These are measurement gates, not accepted thresholds.

Before claiming scalable economics, BenefitFlow should have enough observed pilot volume to estimate:

- booking-channel mix;
- distribution of human minutes;
- exception rate;
- confirmation conversion;
- reconciliation tail;
- support contacts;
- vendor access mix;
- unit cost with confidence intervals or at least stable ranges.

Before claiming automation:

- distinguish zero-human API automation from user-completed hosted handoff;
- exclude appointment requests that are not confirmed;
- exclude synthetic workflows from production rates.

Before claiming profitability:

- include variable support;
- include scenario labour;
- include partner fees where known;
- keep unknown partner fees visible as unknown rather than zero;
- allocate fixed production-readiness costs explicitly under a stated policy.

## Recommended implementation order

1. Create identifiers and append-only economics event envelope.
2. Instrument current beta endpoint/workflow boundaries.
3. Add human-time and reason-code capture to synthetic pilot tooling.
4. Integrate transaction-adapter events after R10 architecture lands.
5. Add cost-rate lookup/versioning separately from raw events.
6. Build reports only after event semantics are tested.
7. Add regression tests proving sensitive identifiers cannot enter economics events.

## Required tests

### Privacy tests

- raw plan number absent from emitted event;
- raw member ID absent;
- request body not serialized into telemetry;
- free-text error messages sanitized or mapped to reason codes.

### Semantics tests

- `READY_FOR_TRANSACTION_ADAPTER` does not increment confirmed bookings;
- appointment request does not increment confirmed bookings;
- waitlist does not increment confirmed bookings;
- hosted handoff does not increment confirmed bookings;
- only authoritative confirmation increments confirmed bookings.

### Time tests

- wall-clock wait does not become active human time;
- reconciliation time is classified separately from booking time;
- repeated manual touches accumulate correctly.

### Cost tests

- missing vendor price remains `unknown`, not zero;
- currency is retained with source cost;
- labour scenario changes do not mutate raw telemetry;
- retries and duplicate-risk reconciliation are counted.

## R7 implementation conclusion

The current beta has good conceptual workflow boundaries but is not instrumented to answer the economic questions the project will eventually be judged on.

The most important next economics implementation is not a pricing page or revenue forecast. It is an append-only, privacy-minimized event stream that can distinguish:

- automated vs human work;
- request vs confirmation;
- cheap transport vs expensive operational recovery;
- scalable channels vs structurally manual channels.

Without that layer, any future "cost per booking", "automation rate", or "ROI" number would be vulnerable to denominator errors and hidden manual labour.

## What this specification does not establish

- It does not set a production architecture.
- It does not authorize collection of personal or health information.
- It does not establish labour rates or customer pricing.
- It does not establish profitability.
- It does not define legal retention requirements.
- It does not mutate accepted project state.

## Research disposition

`IMPLEMENTATION_RECOMMENDATION_READY_FOR_MANAGER_REVIEW`
