# BenefitFlow Manager-01 — Round 1 Owned-Lanes Review 001

Project: `benefitflow`  
Manager: `manager-01`  
Owned slots: `R1`, `R2`, `R3`, `R4`, `R7`  
Authority: manager review/reconciliation only; Primary retains accepted-state authority.

## Executive disposition

New work is present and materially advances all five Manager-01 lanes. The evidence is directionally coherent with Primary's already-accepted P0 architecture gate. No finding reviewed here justifies weakening the production block on real member data, live credentials, claims submission, or live booking adapters.

This review classifies research evidence and extracts implementation/test consequences. Exact research-proposed class names, enums, tables, vendors, and storage choices remain proposals until Primary integration.

## R1 — Benefit Semantics and Normalization

**Disposition: SUPPORTED_WITH_LIMITS; promote implementation requirements, not exact schema names.**

The secondary validation is strong and uses first-party insurer/industry sources. The most important implementation requirements are:

1. Unknown deductible/utilization state must not default to zero.
2. Deductibles/maxima need explicit scope and shared-accumulator semantics where applicable.
3. Service/incurred date must be distinct from claim submission, adjudication, and payment timestamps.
4. Coordination of benefits must preserve plan-specific eligible-expense/adjudication state rather than collapsing to one synthetic reimbursement percentage.
5. Maximum basis must be explicit when it changes the dollar result.
6. Dollar projection must fail closed when material semantic axes are unresolved.

**Manager action:** request conversion of the proposed 18 parser/optimizer cases into a canonical red-test packet aligned with the current beta codebase. Avoid locking exact object names before Primary model convergence.

## R2 — Insurer Direct Billing and Payer Variability

**Disposition: SUPPORTED_WITH_LIMITS; escalate sanctioned-partner discovery.**

The evidence supports a provider-mediated claims-rail architecture, not a generic consumer-side direct-billing API. Pacific Blue Cross PROVIDERnet is the strongest bounded BC API pilot signal. TELUS eClaims is the broadest evidenced multi-insurer vendor surface, but BenefitFlow access is not established by public material. GreenShield/providerConnect has clear provider workflow value but no supported BenefitFlow machine interface has been proven.

**Manager action:**
- keep all live claim/eligibility transaction code blocked until sanctioned access exists;
- require explicit transaction principal, authorization mode/scope, capability provenance, and freshness in the eventual adapter model;
- escalate a bounded partner/API discovery packet for Pacific Blue Cross and TELUS rather than engineering against assumed access;
- preserve provider-mediated handoff as the beta-safe fallback.

## R3 — Provider Discovery and Identity Resolution

**Disposition: SUPPORTED_WITH_LIMITS; terms/authorization is a hard dependency.**

R3 correctly separates source authority from permission to automate. Regulator registries can be authoritative while still restricting commercial use. Provider identifiers can carry fraud value and should not be treated as harmless enrichment data. Jane search is useful but incomplete/opt-in and does not establish autonomous scheduling rights. Payer directories contain field-specific and often non-real-time evidence.

**Manager action:**
- treat source authorization/terms posture as a pre-acquisition control;
- use assertion-specific freshness rather than one provider-record TTL;
- separate licensure, identity, payer participation, clinic operations, price, and availability evidence;
- preserve durable internal provider identity with versioned external aliases;
- request legal/terms resolution before automated commercial ingestion of restricted BC regulator data;
- keep discovery/deep-link capability separate from transaction capability.

## R4 — Booking Channels and Confirmation Semantics

**Disposition: SUPPORTED_WITH_LIMITS; implementation should follow after earlier P0 primitives.**

The evidence strongly supports a post-approval external transaction lifecycle. Request submitted, hold, waitlist, calendar event, and confirmed booking are distinct states. The beta currently lacks durable post-handoff lifecycle/reconciliation semantics.

**Manager action:**
- require separation of user authorization state from external booking state;
- require idempotency/correlation identities, duplicate-event suppression, out-of-order reconciliation, authoritative external identifiers, and human recovery for ambiguous outcomes;
- do not allow calendar creation alone to prove provider confirmation;
- preserve immutable reschedule lineage and require reapproval for material term changes;
- reconcile channel semantics with R3 source/automation classification and R10 adapter architecture before Primary fixes exact state names.

## R7 — Product Economics and Operational Feasibility

**Disposition: SUPPORTED_AS_PILOT-METRICS FRAMEWORK; insufficient for profitability/pricing conclusions.**

R7's central conclusion is credible: early variable cost is more likely to be dominated by human research, verification, booking, follow-up, and reconciliation minutes than by raw telephony/SMS/place-data transport. Integration access and booking-channel mix are material cost dependencies.

**Manager action:**
- instrument human minutes per successful outcome as a primary pilot metric;
- report unit economics separately by booking channel/provider system rather than one blended metric;
- track ambiguous outcomes, reconciliation minutes, follow-ups, and exception rates;
- keep production-readiness security/privacy/vendor onboarding costs separate from low-volume variable-cost claims;
- treat pricing models as hypotheses until real pilot utilization and willingness-to-pay evidence exists.

## Cross-lane reconciliation

The five lanes converge on one coherent implementation sequence already consistent with Primary's accepted P0 gate:

1. typed domain/provenance primitives and semantic fail-closed behavior;
2. authorization/privacy/security primitives owned across managers;
3. red tests for parser/optimizer semantics;
4. source-authorized provider/direct-billing evidence adapters;
5. durable booking transaction/reconciliation lifecycle;
6. sanctioned integration experiments only after preceding gates pass;
7. pilot economics instrumentation across every step.

## Unresolved escalations to Primary

1. Approve creation of a concrete P0 implementation work package derived from accepted research, while keeping exact model naming centralized.
2. Decide whether business-development discovery with Pacific Blue Cross and TELUS should begin now as a non-transactional information-gathering workstream.
3. Confirm that restricted regulator registry terms must be resolved before any automated commercial ingestion, with bounded manual/user-directed verification as the interim path.

## Follow-up directives for owned researchers

- **R1:** turn the 18 proposed cases into code-targeted red-test specifications and identify exact current-beta failure points.
- **R2:** produce a partner-discovery question set and minimum sanctioned-access evidence checklist for PBC/TELUS/GreenShield.
- **R3:** produce a canonical assertion/freshness/terms matrix for BC pilot sources and flag any source that cannot presently be automated.
- **R4:** produce a vendor-neutral transition/evidence table plus regression scenarios for retries, duplicate events, out-of-order events, holds, waits, cancellations, and reschedules.
- **R7:** produce a minimal pilot instrumentation schema and sensitivity ranges driven by manual minutes, channel mix, exception rate, and confirmation rate.

No accepted state is modified by this manager review.