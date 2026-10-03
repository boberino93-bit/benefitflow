# BenefitFlow — Code/Schema Benefit-Semantics Gap Analysis v0.1

- Project: `benefitflow`
- Lane: `benefit-semantics / implementation-gap`
- Agent: `researcher-benefit-semantics-5f9d`
- Baseline: Beta v0.3.0
- Disposition: `ESCALATE_TO_PRIMARY`
- Date: 2026-10-03

## 1. Claim / question

Can the current `BenefitRule` model, regex parser, and category-keyed optimizer safely represent common real-world Canadian supplementary-health plan semantics without materially misprojecting reimbursement?

## 2. Evidence

### E1 — Sun Life Health Choice B
Publisher: Sun Life Canada  
Source quality: primary commercial insurer source  
Freshness: current (retrieved 2026-10-03)  
Applicability: Canadian personal health plan example  
URL: https://www.sunlife.ca/en/choices/leaving-group-benefits/health-coverage-choice/health-choice-b/

Observed facts:
- Paramedical coverage can have `$300/year per practitioner type` **and** a `$500/calendar-year combined maximum`.
- Psychology/social work can have `$70/visit` **and** `7 visits/year`.
- Vision can have `$200 every 2 years` including a `$50 eye-exam` sublimit.
- Hospital can combine `85% reimbursement`, `$175/day`, and `$5,000/year`.
- Medical-equipment items can share an annual pool while carrying item-specific annual/lifetime sublimits.

### E2 — Manulife CoverMe Guaranteed Issue Enhanced
Publisher: Manulife  
Source quality: primary commercial insurer source  
Freshness: current (retrieved 2026-10-03)  
Applicability: Canadian personal health plan example  
URL: https://www-aem-prod.coverme.manulife.ca/health-insurance/guaranteed-issue-enhanced-plan.html?as=cm&open=

Observed facts:
- `Benefit year` and `calendar year` are distinct concepts.
- The page defines benefit year as a 12-month period beginning from the first claim for a specified benefit.
- It also shows combined maxima, coinsurance, visit caps, and first-visit/subsequent-visit distinctions.

### E3 — Securian Canada EHC
Publisher: Securian Canada  
Source quality: primary commercial insurer source  
Freshness: current (retrieved 2026-10-03)  
Applicability: Canadian extended-health product example  
URL: https://www.securiancanada.ca/scs/ppao/home/insurance-products/extended-health-care-with-core-travel-insurance.html

Observed facts:
- Limits can be per insured person, plan year, calendar year, every N months/years, lifetime, item-count, or combined.
- Private reimbursement can depend on the eligible portion first paid by a government health insurance plan.

### E4 — McGill Supplemental Health Plan
Publisher: McGill University  
Source quality: first-party plan sponsor source  
Freshness: current (retrieved 2026-10-03)  
Applicability: Canadian employer plan example  
URL: https://www.mcgill.ca/hr/benefits/insurance/health-dental/health

Observed facts:
- Out-of-pocket maxima differ for single vs family coverage.
- Family coverage can contain a member-specific sublimit plus an eligible-dependants-combined sublimit.
- Other contractual limits, including reasonable-and-customary fees and benefit maxima, continue to apply after reimbursement changes to 100%.

### E5 — CLHIA Consumer Guides / Coordination of Benefits
Publisher: Canadian Life and Health Insurance Association  
Source quality: authoritative Canadian industry-association source  
Freshness: current (retrieved 2026-10-03)  
Applicability: Canadian supplementary-health insurance  
URL: https://www.clhia.ca/en-CA/Consumers/Consumer-Guides

Observed fact:
- Coordination of benefits is a separate coverage layer and governing policy wording remains authoritative.

## 3. Current code reviewed

- `benefitflow_beta/models.py` blob `c849eaa2833079d229f5501c55b099919b7ce50c`
- `benefitflow_beta/parser.py` blob `e4d487e4ea58e68ddaa9ea982cb0ceb05ac68984`
- `benefitflow_beta/optimizer.py` blob `5a5fc9423f7a28d59aad9f64159d7f964e0c7076`

The beta already has useful primitives: reimbursement percentage, one maximum, period kind/month count, visit limit, shared-pool placeholders, one R&C cap, deductible remaining, usage-to-date, referral/prescription flags, evidence excerpt, and confidence. It also appropriately refuses shared-pool optimization when reviewed data is unavailable.

## 4. Confirmed implementation gaps

### G1 — One maximum cannot encode layered constraints
A single service may simultaneously have per-visit, annual, combined-pool, multi-year, and lifetime limits.

Consequence: `maximum_amount` can overstate or understate coverage.

Recommendation: add typed `limits[]` with stable `limit_id`, kind, value, scope, period, parent/pool reference, confidence, and evidence.

### G2 — Periods require an anchor
The parser currently maps `benefit year`, `per year`, `annual`, and `annually` to a 12-month benefit-year concept. Evidence shows a benefit year may begin on first claim, while other plans use calendar-year or multi-year periods.

Consequence: a reset can occur on the wrong date.

Recommendation: model `period.kind`, `duration`, `anchor_type`, `anchor_date_if_known`, and `rolling`. Do not infer January 1 from `annual`.

### G3 — Scope/cardinality is missing
Limits can apply per person, dependent, family, practitioner type, service family, item, incident, trip, or course of treatment.

Consequence: category-level balances can conflate independent limits or fail to decrement shared ones.

Recommendation: accumulator key = `(plan_id, limit_id, covered_person/scope_instance)` rather than category alone.

### G4 — Parent/child limits are required
Examples include an equipment-family annual pool with item-specific sublimits and a vision limit containing an eye-exam sublimit.

Consequence: independent category optimization can breach a parent ceiling.

Recommendation: support `parent_limit_id` and `pool_id`, and evaluate all applicable limits before accepting a projected service.

### G5 — Eligible-charge basis is contextual
R&C, fee-guide, government-plan-first, lowest-cost-interchangeable, approval, and rental-vs-purchase rules are not equivalent to one fixed `reasonable_customary_cap`.

Consequence: a booklet parser may fabricate precision.

Recommendation: model `eligible_charge_rule` separately from a numeric amount. Unknown live values remain `unknown` and become verification dependencies.

### G6 — Deductibles and out-of-pocket maxima are shared state
The optimizer stores deductible remaining by category. Real plans can use person/family deductibles and family out-of-pocket accumulators spanning benefits.

Consequence: a deductible may be reapplied once per category and reimbursement state transitions cannot be represented.

Recommendation: plan-level accumulator objects with scope and calculation ordering.

### G7 — Dense-block money heuristics are unsafe
`parser._maximum()` selects the largest money amount from a recognized-period block. `_extract_rc()` selects the smallest amount when R&C text is present.

Adversarial clause:
`Psychology: 80%, maximum $70 per visit, 7 visits per year; practitioner maximum $300; paramedical combined maximum $500; lifetime mental-health maximum $25,000.`

Consequence: every number can be extracted correctly while its semantic relationship is wrong; the parser can still assign high confidence.

Recommendation: bind each number to a tuple `(value, unit, role, scope, period, parent/pool)` and attach confidence to the relationship. Multiple unmatched dollar amounts must fail closed.

### G8 — Authorization rules need richer status
`requires_referral` / `requires_prescription` only distinguish recognized true wording from unknown.

Recommendation: typed rule status `required | not_required | conditional | unknown`, with condition text and evidence.

## 5. Proposed minimal schema direction

```text
BenefitDefinition
  benefit_id
  service_types[]
  provider_rules[]
  reimbursement_rules[]
  limits[]
  pool_refs[]
  deductible_refs[]
  out_of_pocket_refs[]
  eligibility_rules[]
  coordination_rules[]
  evidence[]
  normalization_status

Limit
  limit_id
  kind: currency | count | duration
  value
  applies_to: visit | day | item | incident | trip | person | family | practitioner_type | benefit | pool
  period:
    kind: calendar_year | plan_year | rolling | first_claim_anchored | consecutive_years | lifetime | none | unknown
    duration
    anchor
  parent_limit_id?
  pool_id?
  confidence
  evidence_ref
```

## 6. Adversarial / acceptance tests

1. `$300/year per practitioner` plus `$500/year combined pool`: both balances decrement.
2. Psychology `$70/visit` plus `7 visits/year`: eighth visit rejected even with annual dollar headroom.
3. Vision `$200/2 years` with `$50` eye-exam sublimit: child and parent limits both apply.
4. Hospital `85%`, `$175/day`, `$5,000/year`: all constraints apply.
5. Family deductible applies across categories, not once per category.
6. Family OOP max changes coinsurance while R&C and benefit maximums still apply.
7. `12 months from first claim` does not reset January 1.
8. Dense clause with multiple dollar limits is never collapsed to one maximum.
9. `annual maximum` with unknown anchor stays unresolved.
10. Government-plan-first wording creates a verification dependency rather than a fabricated eligible amount.

## 7. Contradictions / scope differences

No evidence requires selecting a universal insurer rule. The important finding is plan-to-plan variation. Product pages demonstrate valid semantic forms but do not override an individual member's governing certificate/policy. Exact calculation ordering is plan-specific.

## 8. Privacy / security impact

No member identifier, diagnosis, plan number, or transaction credential is required for this research artifact. Production accumulator state may be person-scoped; use opaque internal covered-person IDs and do not copy sensitive identifiers into public research/evidence records. Explanation traces should minimize health-detail disclosure.

## 9. Uncertainty / missing evidence

- This is not an exhaustive catalogue of every insurer/province/union/HSA/drug/dental rule.
- Dynamic R&C values may require live insurer verification.
- Detailed coordination-of-benefits arithmetic deserves a dedicated follow-up.
- Proposed field names are architectural recommendations, not accepted project truth.

## 10. Recommended disposition

`ESCALATE_TO_PRIMARY`.

Supported architectural conclusion: before BenefitFlow automatically optimizes heterogeneous real plans, its benefit representation should evolve from a flat benefit row to an evidence-linked constraint model with explicit scopes, periods, parent/shared accumulators, and fail-closed unresolved relationships.

No accepted state was modified.
