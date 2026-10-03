# BenefitFlow Research Packet — Benefit Semantics R01

**Researcher role:** specialist / research
**Project:** BenefitFlow (`project_id=benefitflow`)
**Lane:** `benefit-semantics`
**Status:** initial evidence-backed findings
**Scope boundary:** research only; no accepted-state mutation and no external transaction execution.

## Executive finding

The current `BenefitRule` model is a strong beta baseline but is not yet expressive enough to safely normalize several benefit structures that occur in real Canadian extended-health plans. The main risk is not simple parsing error; it is **semantic collapse**: distinct plan concepts can currently be represented by the same fields and therefore produce a plausible but financially wrong utilization plan.

## Evidence-backed semantic patterns

### 1. Coinsurance can be tiered/stepwise, not a single category percentage

The Province of British Columbia's bargaining-unit extended-health plan describes reimbursement at **80% for the first $2,000 paid in a calendar year per person, then 100% for the balance of the year**, while still remaining subject to restrictions, reasonable-and-customary limits, and plan maximums.

Implication: `coverage_percent: float` cannot represent threshold-triggered reimbursement schedules. A plan-level or benefit-level `coverage_tiers[]` structure is required.

Source: Province of British Columbia, Extended health and dental plans for bargaining unit employees
https://www2.gov.bc.ca/gov/content/careers-myhr/all-employees/pay-benefits/benefits/bargaining-benefits/bargaining-benefits-health-dental

### 2. Reasonable-and-customary limits are mutable external policy data

BC's benefits glossary defines R&C as standard fees/costs, states that the limits are **reviewed regularly and subject to change at any time**, and directs members to insurer-specific coverage data for current paramedical R&C charges.

Implication: `reasonable_customary_cap: float` should not be treated as timeless plan text. It needs provenance, jurisdiction/service scope, effective/verified date, and a freshness policy. Unknown/stale R&C should fail to manual verification rather than silently assume provider price is fully eligible.

Source: Province of British Columbia, Excluded benefits guide glossary
https://www2.gov.bc.ca/gov/content/careers-myhr/all-employees/pay-benefits/benefits/excluded/excluded-benefits-glossary

### 3. Maximums may be shared across multiple services

DGC Benefits publishes paramedical coverage such as **65% or 75% up to $1,500 per person/year for all services combined** depending on plan level.

Implication: BenefitFlow's `shared_pool_id` direction is correct, but shared-pool semantics need first-class accumulator scope and pool membership. The optimizer currently sends any shared-pool rule to manual review, which is safe but limits production utility.

Source: DGC Benefits, Coverage at a Glance / Levels II and III
https://dgcbenefits.ca/coverage-and-plan-details/coverage-at-a-glance-overview/

### 4. Rolling periods can be explicitly consecutive and age-dependent

An Industrial Alliance plan description specifies vision maximums in **any period of 24 consecutive months**, while eye-exam timing is 24 months for adults and 12 months for dependents under 18.

Implication: `period_kind=rolling_months` plus `period_months` is insufficient by itself. The model needs a calculation anchor (`service_date`, `claim_date`, `fixed_anchor`, etc.), member-age eligibility predicates, and potentially sub-benefit-specific windows.

Source: Industrial Alliance plan details, Vision Care Plan
https://content.flex.ia.ca/2171/English/PlanDetails/old/PlanDetailHealthC.htm

### 5. A category can contain independent sub-benefits and independent limits

The same vision example separates eyewear/laser coverage from eye-exam coverage. DGC likewise lists eye exams, glasses/contacts, and laser eye surgery as distinct benefit lines with different maxima and periods.

Implication: a single dictionary key by `category.lower()` is unsafe for categories that have multiple covered items. The normalized model needs `benefit_item_id` / `subcategory` (e.g. `vision.eye_exam`, `vision.eyewear`, `vision.laser_surgery`) and the optimizer must not collapse duplicate category rows.

Sources:
- https://dgcbenefits.ca/coverage-and-plan-details/coverage-at-a-glance-overview/
- https://content.flex.ia.ca/2171/English/PlanDetails/old/PlanDetailHealthC.htm

### 6. Prior authorization is a distinct eligibility gate, not merely a prescription/referral flag

UBC's extended-health description states that some specialty drugs require prior authorization and supporting evidence before coverage applies.

Implication: BenefitFlow needs a generic `authorization_requirement` / `preapproval_status` concept distinct from `requires_prescription` and `requires_referral`.

Source: UBC Extended Health Benefits
https://hr.ubc.ca/benefits/benefit-plan-details/extended-health-benefits

## Current-model risks observed in Beta v0.3.0

1. **Duplicate category overwrite:** `benefit_map = {b.category.lower(): b ...}` retains only one rule per category.
2. **Single percentage assumption:** one `coverage_percent` cannot represent stepped coinsurance or threshold transitions.
3. **Maximum-type ambiguity:** `maximum_amount` does not distinguish a maximum eligible expense from a maximum insurer reimbursement or a combined pool maximum.
4. **Accumulator-scope ambiguity:** `deductible_remaining` and `benefit_used_to_date` live on each rule even when the real accumulator may be per person, per family, per plan, or shared across categories.
5. **R&C freshness gap:** a scalar cap lacks evidence source, effective date, jurisdiction, and verification timestamp.
6. **Rolling-window ambiguity:** no anchor/event semantics or member-age predicate exists for rolling periods.
7. **Eligibility gates incomplete:** prior authorization/preapproval cannot be represented distinctly.
8. **Plan-level reimbursement logic is modeled as category-level logic:** this can produce wrong projections for plans where reimbursement changes based on aggregate paid amounts.

## Recommended schema changes for Primary/Manager review

Proposed additions (conceptual; names can change):

- `BenefitItem`
  - `benefit_item_id`
  - `category`
  - `subcategory`
  - `eligible_member_predicates[]`
- `MaximumRule`
  - `amount`
  - `maximum_basis`: `eligible_expense | insurer_paid | visits | units`
  - `accumulator_scope`: `member | family | category | shared_pool | plan`
  - `period`
- `CoverageTier[]`
  - threshold basis and threshold amount
  - reimbursement percent
- `PeriodRule`
  - `kind`
  - `months`
  - `anchor_event`
  - `fixed_start_date` / benefit-year start where applicable
- `ExternalLimitEvidence`
  - `limit_type=reasonable_customary`
  - amount
  - jurisdiction/service/provider-class scope
  - source
  - `verified_at`
  - `effective_at`
- `EligibilityGate[]`
  - `prescription`
  - `referral`
  - `prior_authorization`
  - `medical_necessity`
  - `provider_credential`
- `Accumulator`
  - stable ID referenced by multiple rules so plan-level/shared state is not duplicated.

## Optimizer changes recommended

1. Replace one-rule-per-category mapping with a multi-rule / benefit-item graph.
2. Calculate eligibility first, then R&C/eligible charge, then deductible/other accumulator effects, then tiered coinsurance, then maximums.
3. Treat stale or unknown dynamic limits as a manual-verification requirement.
4. Track accumulators by explicit IDs and scopes rather than category names.
5. Generate a deterministic explanation trace for every planned service showing which rule reduced eligibility/payment.

## High-priority tests to add

- Two vision sub-benefits under one category must not overwrite each other.
- 80% until aggregate threshold, then 100%, with threshold crossing mid-claim/visit.
- Shared $1,500 paramedical pool consumed by physiotherapy and massage together.
- 24-consecutive-month vision window versus calendar-year window.
- Dependent age causes a 12-month eye-exam window while adult remains 24 months.
- R&C below provider charge leaves the excess fully user-paid.
- R&C marked stale/unknown forces manual review.
- Prior authorization required but unknown/not-approved blocks auto-planning.

## Confidence and next work

**Confidence:** high on the existence of these semantic patterns; medium on exact production schema until additional insurers and real plan booklets are sampled.

Next research should deliberately sample Sun Life, Canada Life, Manulife and provincial/employer plan booklets for: coordination-of-benefits ordering, deductible scopes, benefit-year anchors, practitioner credential constraints, claim-incurred versus claim-paid dates, and maximum-basis wording.
