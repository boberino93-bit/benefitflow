# R7 Evidence Packet 001 — Product Economics and Operational Feasibility

Project: BenefitFlow (`project_id=benefitflow`)  
Agent: `researcher-r7-product-economics-20261003T2228Z`  
Assignment: R7 — Product Economics and Operational Feasibility  
Prepared lane: `product-economics-abuse`  
Status: RESEARCH EVIDENCE / NOT ACCEPTED STATE  
Evidence date: 2026-10-03

## Executive finding

BenefitFlow is economically plausible as a navigation/coordination product **only if it drives manual minutes and ambiguous transaction recovery down aggressively**. Public infrastructure prices suggest that raw telephony, messaging, and basic place-data lookup are small per-case costs. The likely dominant variable cost is human operations: provider verification, clinic contact, exception handling, follow-up on appointment requests, ambiguous booking reconciliation, and support around unsupported or restricted integrations.

The largest unresolved cost is not a cloud API line item. It is **integration access and operational friction**. Some practice-management systems expose transactional APIs, while other important systems use approval-based partner programs and do not currently support third-party appointment creation. BenefitFlow therefore needs channel-specific unit economics rather than one blended assumption that every appointment can be booked automatically.

## Evidence reviewed inside BenefitFlow

This packet treats the following internal outputs as research inputs, not accepted project truth:

- R3 provider discovery initial evidence: `BenefitFlow-AgentBus/artifactory/research/r3-provider-discovery/researcher-r3-provider-discovery-20261003T2222Z/INITIAL_EVIDENCE_REPORT.md`
- R4 booking-channel evidence and transaction-state work, including this researcher's preserved supplemental R4 packet.
- R6 voice/phone evidence: `BenefitFlow-AgentBus/artifactory/research/r6-voice-phone/R6_VOICE_PHONE_TRANSACTION_RESEARCH_V1.md`
- Shared manager cross-lane reconciliation: `BenefitFlow-AgentBus/artifactory/manager/shared/20261003-cross-lane-architecture-gate-v1-64f58a5f.md`

Cross-lane implications used here:

1. Provider identity, licensure, payer participation, member eligibility, and availability are separate checks with different freshness requirements.
2. Availability is perishable and can require re-check immediately before a booking action.
3. Appointment request, hosted handoff, waitlist, hold, and confirmed booking are different states.
4. Ambiguous post-action outcomes must be reconciled before retrying to avoid duplicates.
5. Voice transport completion is not proof of business/booking completion.
6. Production IAM, privacy, audit, and bounded authorization add fixed engineering/compliance burden before live sensitive-data workflows.

## Public cost evidence

All listed prices are public list prices retrieved 2026-10-03 and can change. They are evidence for order-of-magnitude modelling, not negotiated production quotes.

### E1 — Telephony transport is inexpensive relative to human time

Source: Twilio Programmable Voice pricing — Canada  
URL: https://www.twilio.com/en-us/voice/pricing/ca

Observed current list pricing:
- outbound United States & Canada calls: **USD $0.0140/minute**;
- inbound local calls: **USD $0.0085/minute**, plus local-number monthly charge;
- browser/app and SIP interface legs: **USD $0.0040/minute** at the listed tier.

Implication:
- A 10-minute outbound Canada/US call has a base telephony transport cost of about **USD $0.14**, before optional services, taxes, recording/transcription, or carrier-specific features.
- The transport itself is unlikely to dominate economics. Staff or agent time spent waiting, verifying, handling IVRs, repeating details, resolving ambiguity, or calling back is much more important.

### E2 — SMS transport is also a cents-scale cost, but carrier fees matter

Source: Twilio SMS pricing — Canada  
URL: https://www.twilio.com/en-us/sms/pricing/ca

Observed current list pricing:
- long-code outbound SMS base price: **USD $0.0083/segment**;
- listed outbound Canadian carrier fees for major carriers are roughly **USD $0.0067-$0.0087/segment** at retrieval;
- failed-message processing fees and other provider/carrier charges can also apply.

Implication:
- A simple one-segment transactional SMS is approximately cents-scale, not dollars-scale.
- Message volume and multi-segment content should still be measured, but SMS spend is unlikely to be the primary unit-economics risk for the pilot.

### E3 — Place discovery can be optimized with field masks and staged enrichment

Sources:
- Google Maps Platform pricing: https://developers.google.com/maps/billing-and-pricing/pricing
- Places field pricing: https://developers.google.com/maps/documentation/places/web-service/data-fields
- Place Details field masks: https://developers.google.com/maps/documentation/places/web-service/place-details

Observed current list pricing (USD per 1,000 billable events, after free caps and before volume discounts):
- Places Text Search Essentials — IDs only: unlimited no-cost tier listed;
- Place Details Essentials — IDs only: unlimited no-cost tier listed;
- Places Text Search Pro: **$32/1,000** after a 5,000-event monthly free cap;
- Place Details Pro: **$17/1,000** after a 5,000-event monthly free cap;
- Place Details Enterprise: **$20/1,000** after a 1,000-event monthly free cap;
- Text Search Enterprise: **$35/1,000** after a 1,000-event monthly free cap.

Google documents that phone number and website fields trigger the Place Details Enterprise SKU, while field masks can avoid requesting higher-priced data that is not needed.

Implication:
- Provider search should be staged: obtain candidate IDs with the cheapest sufficient operation, then enrich only shortlisted candidates.
- At list rate outside the free cap, an Enterprise Place Details enrichment is about **USD $0.02 per event**. Even several provider enrichments usually remain much cheaper than a few minutes of manual verification.
- Cost control should be built into the provider research strategy: avoid high-tier fields for candidates that will never reach the shortlist.

### E4 — Existing Canadian eClaims rails may be free to providers, but that does not establish free BenefitFlow integration access

Sources:
- TELUS Health eClaims FAQ: https://www.telus.com/en/health/health-professionals/allied-healthcare-professionals/eclaims/faq
- TELUS Health eClaims overview: https://www.telus.com/en/health/health-professionals/allied-healthcare-professionals/eclaims
- Sun Life provider hub/eClaims: https://www.sunlife.ca/sl/provider/en/

Observed:
- TELUS Health states eClaims is free for healthcare providers and patients.
- TELUS states eClaims can be used through its portal/app and through integrated practice-management software.
- Sun Life states eligible providers can access eClaims and Provider Search for free.

Unknown / important boundary:
- These statements describe provider/patient pricing. They do **not** establish that a third-party BenefitFlow product can obtain API/partner access at no cost or without a commercial/security review.
- Technology-partner licensing, onboarding, certification, support, and commercial terms remain unresolved.

Economic implication:
- Model provider/member usage fee as potentially zero for the existing rail, but model **BenefitFlow integration access as unknown until partner terms are obtained**.
- Do not put `$0` into the production integration budget based on provider-facing marketing pages.

### E5 — Jane creates a material integration-access constraint for automated scheduling

Sources:
- Jane integrations program announcement, 2026-04-01: https://jane.app/blog/jane-integrations-our-program-our-partners-and-how-to-work-with-us
- Jane partner application: https://integrations.jane.app/application_forms/jane-integrations-partner-interest-form/partner_applications/new
- Jane integrations hub: https://jane.app/guide/integrations-hub-faq

Observed:
- Jane says it does not provide an open/public API; integrations use a vetted, approval-based partner pathway.
- Jane's current partner application states its API does not yet support patient or appointment creation, modification, or deletion.
- Jane's April 2026 program announcement says it is not currently looking to work with AI scheduling tools and direct posting into Jane calendars is not supported.
- Jane publicly reports more than 240,000 practitioners across over 40 disciplines using its practice-management software, indicating that the constraint is not obviously niche.

Economic implication:
- For Jane-backed clinics, straight-through third-party booking cannot currently be assumed.
- A pilot that depends heavily on those clinics may require hosted-page handoff, user completion, or human coordination, increasing manual minutes and reducing transaction observability.
- Partner/business-development access becomes a product dependency, not merely an engineering task.

## Cost-driver model

Use an activity-based model per completed user objective rather than one generic cost per request.

### Core equation

```text
variable_cost_per_confirmed_booking =
    provider_discovery_data
  + provider_verification_data
  + communications_transport
  + booking_adapter_fees
  + model_compute
  + human_research_minutes * loaded_labor_per_minute
  + human_verification_minutes * loaded_labor_per_minute
  + human_booking_minutes * loaded_labor_per_minute
  + exception_recovery_minutes * loaded_labor_per_minute
  + expected_rework_cost
  + allocated_variable_support
```

Then:

```text
expected_cost_per_user_plan =
  plan_normalization_cost
  + sum(expected_provider_research_cost_by_category)
  + sum(expected_booking_cost_by_category)
  + cancellation_reschedule_expected_cost
  + support_cost
```

Fixed/step-function costs should be kept outside the per-case numerator until there is enough volume to allocate them sensibly:

- privacy/legal review;
- security architecture and penetration testing;
- vendor partnership/onboarding/certification;
- insurer or transaction-rail integration work;
- monitoring/audit platform;
- production identity provider and secrets management;
- customer-support tooling;
- on-call/reliability coverage.

## Channel-specific economic classes

### Class A — Straight-through transactional API

Expected cost profile:
- low human minutes after integration stabilizes;
- API/data/compute costs are measurable and automatable;
- reconciliation can often query authoritative state;
- highest fixed engineering/security integration cost, lowest marginal operations cost.

Primary metric: `straight_through_confirmation_rate`.

### Class B — Hosted booking handoff

Expected cost profile:
- low BenefitFlow transaction transport cost;
- completion depends on user/provider-hosted flow;
- confirmation ingestion/reconciliation may require messaging or user confirmation;
- lower engineering integration cost, but weaker control over completion funnel.

Primary metric: `handoff_to_confirmed_conversion_rate`.

### Class C — Appointment request / asynchronous message

Expected cost profile:
- low send cost;
- follow-up latency and unresolved requests increase support/reconciliation work;
- repeated availability checks may be needed before confirmation.

Primary metrics:
- `request_to_confirmation_rate`;
- `median_request_confirmation_latency`;
- `followups_per_confirmed_booking`.

### Class D — Phone/manual coordination

Expected cost profile:
- telephony minutes are inexpensive;
- human/agent time, hold time, IVR traversal, callback handling, disclosure controls, and ambiguity dominate;
- difficult to make economical if a large fraction of bookings remain here.

Primary metrics:
- `human_minutes_per_confirmed_booking`;
- `calls_per_confirmed_booking`;
- `hold_minutes_per_confirmed_booking`;
- `ambiguous_call_outcome_rate`.

### Class E — Unsupported / human recovery

Expected cost profile:
- highest and least predictable marginal cost;
- must include failed attempts, escalation, duplicate-risk reconciliation, and user communication;
- should be explicitly bounded rather than absorbed invisibly into support.

Primary metric: `exception_rate` and `exception_minutes`.

## Illustrative sensitivity model

The table below is **not a market-price forecast**. Loaded labour rates and workflow minutes are synthetic assumptions chosen to show sensitivity. Vendor transport uses current public list-price order of magnitude outside applicable free caps.

| Scenario | Illustrative loaded labour | Human minutes | Voice minutes | Paid place-data events | SMS segments | Illustrative variable cost* |
|---|---:|---:|---:|---:|---:|---:|
| High automation | $45/hr | 3 | 0 | 2 detail + 1 search | 1 | ~USD $2.34 |
| Hybrid verification | $55/hr | 10 | 5 | 5 detail + 1 search | 2 | ~USD $9.40 |
| Manual exception | $65/hr | 25 | 12 | 8 detail + 2 search | 3 | ~USD $27.53 |

\*Illustrative calculation uses $0.02 Enterprise detail event, $0.035 Enterprise search event, $0.014 outbound voice minute, and ~1.65 cents/SMS segment as a midpoint illustration. It excludes model compute, storage, taxes, FX, recording/transcription, support overhead, partner fees, fixed compliance/security costs, and negotiated discounts.

### Sensitivity conclusion

At an illustrative loaded labour rate of $45/hour:
- one human minute costs **$0.75**;
- that is roughly the same raw cost as more than **50 minutes of Twilio outbound voice** at $0.014/minute;
- it is also roughly the same as about **37 Enterprise Place Details events** at $0.02/event.

Therefore the economic optimization target should be **manual minutes per successful user outcome**, not merely API-call minimization.

## Operational bottlenecks likely to dominate R7

### B1 — Provider verification freshness

R3 shows that licensure, payer participation, and availability have different sources and freshness. Re-verification close to the transaction creates repeated work.

Risk:
- stale records save lookup cost but increase failed-booking and trust risk;
- overly aggressive refresh burns data calls and human review.

Pilot requirement:
- measure refreshes per confirmed booking and contradiction rate by source.

### B2 — Booking-channel fragmentation

R4 evidence shows request, handoff, waitlist, hold, phone, and API-confirmed bookings need different flows.

Risk:
- a blended booking-success metric hides expensive manual channels.

Pilot requirement:
- report conversion, manual minutes, retries, and reconciliation separately by `booking_channel_type`.

### B3 — Ambiguous transactions and duplicate-risk recovery

R4/R6 converge that a timeout/disconnect after a possible external mutation cannot be blindly retried.

Risk:
- reconciliation can be more expensive than the original transaction;
- duplicates create support burden and user harm.

Pilot requirement:
- track `ambiguous_outcome_rate`, `mean_reconciliation_minutes`, and duplicate-prevention interventions.

### B4 — Vendor partnership constraints

Jane demonstrates that an important ecosystem may not permit the desired booking-write use case even when hosted booking is available.

Risk:
- engineering plans can assume automation that cannot be commercially/technically authorized;
- business-development lead time can become the critical path.

Pilot requirement:
- maintain a capability matrix with `public_api`, `partner_api`, `appointment_write`, `confirmation_read`, `commercial_terms_known`, and `approved_for_benefitflow`.

### B5 — Security/privacy production gate

R5/R9/shared-manager work requires bounded authorization, identity, object-level authorization, audit, sensitive-data isolation, and retention controls before real member data/live adapters.

Risk:
- these are real fixed/step-function costs that a prototype P&L can hide.

Pilot requirement:
- keep a separate `production_readiness_fixed_cost` budget and do not misleadingly amortize it over tiny beta volume.

## Pricing/value hypotheses to test — not recommendations yet

### H1 — B2C subscription

Hypothesis:
- recurring subscription can smooth revenue, but usage may be episodic around benefit-year resets, new diagnoses/needs, or appointment bursts.

Risk:
- a small set of high-support members could dominate operations cost.

Test:
- measure active navigation episodes/member/month and human minutes per active vs inactive member.

### H2 — Per-success / per-confirmed-booking fee

Hypothesis:
- aligns revenue with completed coordination outcome.

Risk:
- incentives can become distorted if the payer is a provider or if BenefitFlow benefits from maximizing bookings rather than member value.
- cancellation/reschedule and multi-provider care complicate what counts as success.

Test:
- define auditable success event and compare contribution margin by channel.

### H3 — Employer / plan-sponsor / advisor PMPM or tiered platform fee

Hypothesis:
- navigation value may fit a B2B2C model where the buyer values benefits utilization, employee time saved, and experience rather than individual transaction fees.

Risk:
- evidence of willingness to pay and measurable sponsor ROI is not yet established.

Test:
- pilot with explicit outcome metrics; do not infer sponsor ROI from booking volume alone.

### H4 — Hybrid base fee + usage band

Hypothesis:
- base fee covers fixed navigation/platform capability while usage bands protect against high manual-support tails.

Risk:
- adds pricing complexity and requires reliable usage accounting.

Test:
- simulate pricing using observed human minutes and channel mix after pilot data exists.

## Pilot metrics required before credible economics

### Funnel
- users with normalized benefit plan
- utilization plans generated
- provider searches initiated
- provider shortlists produced
- proposals approved
- booking attempts
- confirmed bookings
- completed/cancelled/rescheduled appointments

### Operational cost
- automated provider lookups per case
- paid data events per case
- telephony minutes per case
- SMS segments per case
- human research minutes
- human verification minutes
- human booking minutes
- exception/reconciliation minutes
- support contacts per case
- cancellations/reschedules per case

### Automation quality
- straight-through processing rate
- hosted-handoff conversion rate
- request-to-confirmation rate
- exception rate
- ambiguous outcome rate
- retries prevented by reconciliation
- duplicate booking incidence
- source contradiction rate

### Time
- time from user approval to booking attempt
- time from attempt to authoritative confirmation
- human touch time vs wall-clock latency

### Economics
- variable cost per plan normalized
- variable cost per provider shortlist
- variable cost per approved booking attempt
- variable cost per confirmed booking
- gross contribution per user/account/channel
- fixed/step-function production-readiness spend tracked separately

### User value signals
- member-reported time saved
- abandoned searches recovered
- out-of-pocket estimate accuracy versus final known result
- successful use of benefits that the member intended to use
- satisfaction/trust after exceptions, not only after happy-path bookings

## Economic guardrails for the next implementation phase

1. **Do not automate a channel merely because transport is cheap.** Measure total human/reconciliation cost.
2. **Do not cache perishable availability solely to reduce API cost.** Failed transactions can cost much more than a fresh lookup.
3. **Use staged provider enrichment.** Resolve cheaply, enrich the shortlist, verify only when a candidate is decision-relevant.
4. **Separate request from confirmation.** Otherwise the dashboard will overstate conversion and understate support cost.
5. **Track human minutes by reason code.** “Manual work” is too coarse to improve.
6. **Put a spend/time ceiling on exception recovery.** Escalate to the user rather than creating an unbounded concierge obligation.
7. **Treat unsupported partner access as a hard capability constraint.** Do not budget unofficial scraping or credential-sharing as a workaround.
8. **Preserve exact approval scope.** A material change requiring fresh approval is an economic event because it adds latency and potentially another human touch.
9. **Measure unit economics by booking channel and provider system.** The average will hide where the product is actually scalable.
10. **Keep fixed production-readiness costs visible.** Security, privacy, vendor onboarding, and audit are not free because the beta uses synthetic data.

## Initial operational target hypotheses for pilot instrumentation

These are measurement targets, not commitments or validated thresholds:

- achieve a rising `straight_through_or_user_handoff_rate` over successive pilot cohorts;
- drive median human touch time down while keeping confirmation correctness at 100% for audited samples;
- keep ambiguous outcomes rare and always reconciled before retry;
- identify the top three manual reason codes and automate only those with authoritative data/transaction support;
- avoid any business model that requires profitable economics while a large majority of cases remain phone/manual exceptions.

A numeric go/no-go threshold should be set only after actual pilot data establishes the channel mix and human-time distribution.

## Contradictions and unresolved unknowns

1. Public provider-facing eClaims pricing does not reveal BenefitFlow technology-partner commercial terms.
2. Google/Twilio list prices may differ from negotiated production rates and are USD-denominated; FX/tax are excluded here.
3. Human labour cost is organization-specific. This packet intentionally uses synthetic sensitivity rates rather than asserting a market salary.
4. Model/LLM inference cost is not estimated here because architecture/model choice and request volume are not yet fixed.
5. Vendor coverage by Canadian provider segment is not yet quantified, so the future API-vs-manual channel mix is unknown.
6. Jane's current integration constraints can change; they must be re-verified before architectural or commercial commitments.
7. No current evidence establishes willingness to pay, retention, sponsor ROI, or an acceptable consumer price.
8. No current evidence establishes that every direct-billing or booking workflow may legally/contractually be automated by BenefitFlow.

## Recommended next R7 work

1. Build a synthetic activity-based costing worksheet driven by observed pilot counters rather than hard-coded assumptions.
2. Ingest R3/R4/R6/R10 channel/capability outputs into a single operational capability-cost matrix.
3. Add reason-coded human-touch instrumentation to beta workflow prototypes.
4. Define a maximum permitted manual-touch budget per booking attempt before human/user fallback.
5. Obtain partner/API commercial terms for the highest-volume provider systems before promising a production automation rate.
6. Run a Monte Carlo/sensitivity model after pilot estimates exist for exception probability, human minutes, booking success, and channel mix.
7. Ask manager/Primary to keep R7 involved whenever R3/R4/R6/R9/R10 changes increase or reduce manual operational burden.

## What this evidence does not establish

- It does not prove BenefitFlow is profitable.
- It does not establish a price customers will pay.
- It does not establish partner/API access rights.
- It does not establish that provider-facing free services are free for BenefitFlow integration.
- It does not establish a production automation percentage.
- It does not establish legal/compliance conclusions.
- It does not promote any cost assumption or pricing hypothesis into accepted project state.

## Research disposition

`SUPPORTED_INITIAL`: Current public pricing and cross-lane evidence support the conclusion that transport/data lookups are likely secondary to human exception handling and integration-access constraints in early BenefitFlow economics. The production business case remains unproven until channel mix, manual minutes, conversion, partner terms, and willingness-to-pay are measured in a pilot.
