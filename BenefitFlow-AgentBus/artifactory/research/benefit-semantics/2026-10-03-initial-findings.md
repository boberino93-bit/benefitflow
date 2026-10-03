# BenefitFlow R&D — Benefit Semantics Initial Findings

**Project:** BenefitFlow (`project_id=benefitflow`)  
**Lane:** `benefit-semantics`  
**Agent:** `researcher-benefit-semantics-2026-10-03-a`  
**Date:** 2026-10-03  
**Status:** Research evidence / proposal only — not accepted project state.

## Objective

Validate the beta's benefit-plan normalization model against current Canadian insurer and industry semantics, then identify places where parser or optimizer behavior could overstate coverage or create false confidence.

## Evidence reviewed

1. Canadian Life and Health Insurance Association (CLHIA), Coordination of Benefits Guideline G4 and consumer guidance.
   - https://www.clhia.ca/en-CA/Industry/clhia-guidelines/g04-coordination-of-benefits-group-health-and-dental
   - https://www.clhia.ca/en-CA/Consumers/Understanding-the-Coordination-of-Benefits
2. Canada Life, current support guidance on customary charges and coordination of benefits.
   - https://www.canadalife.com/support/my-canada-life-at-work/claims-status-questions.html
   - https://www.canadalife.com/insurance/health-and-dental-insurance/how-does-health-insurance-work/what-is-coordination-of-benefits.html
3. Canada Life, Public Service Health Care Plan member booklet and PlanDirect policy wording.
   - https://www.canadalife.com/content/dam/rfp/welcome-sites/pshcp/PSHCP-member-booklet.pdf
   - https://www.canadalife.com/content/dam/canadalife/documents/insurance/plandirect/en/70-0150.pdf
4. Sun Life, current coverage guidance and group-plan product material.
   - https://www.sunlife.ca/en/support/check-your-coverage/
   - https://www.sunlife.ca/content/dam/sunlife/regional/canada/documents/gb/sunsolutions-brochure-tm-ca1128.pdf
   - https://www.sunlife.ca/en/choices/health-coverage-choice-extended-health-care-and-dental-plans/
5. Manulife, current Guaranteed Issue Enhanced / CoverMe benefit definitions.
   - https://www-aem-prod.coverme.manulife.ca/health-insurance/guaranteed-issue-enhanced-plan.html

## Executive finding

The current `BenefitRule` is directionally strong, but the parser/optimizer still collapses several materially different insurance concepts into single numeric fields. That can produce a confident-looking utilization plan that is mathematically consistent with the parsed record while still being wrong under the actual contract.

The safest next step is not to add more regex coverage first. It is to make benefit semantics more explicit, then make the parser fail closed whenever it cannot distinguish those semantics.

## Material findings

### 1. "Per year" is not safely equivalent to `benefit_year`

Current beta behavior in `parser._period()` maps `per year`, `annual`, and `annually` to `benefit_year`.

This is unsafe. Real products distinguish at least:

- **calendar year** — Jan 1 through Dec 31;
- **anniversary year** — 12 months from policy effective date;
- **benefit year** — which may be plan-defined and can differ from calendar year;
- **first-claim anchored benefit year** — Manulife currently defines some benefits as 12 months following the first claim for that specified benefit;
- **rolling periods** — e.g. every 24 months;
- **lifetime** limits.

Sun Life group material explicitly permits benefit years based on an arbitrary 12-month period, with calendar-year constraints in some configurations. Manulife currently distinguishes anniversary year, benefit year, and calendar year in the same product.

**Recommendation:** replace `period_kind + period_months` with an explicit period object containing:
- `kind`: calendar_year | anniversary_year | plan_benefit_year | first_claim_window | rolling_window | lifetime | per_incident | per_claim | unknown
- `months`
- `anchor`: jan_1 | policy_effective_date | plan_year_start | first_claim_date | service_date | incident_date | unknown
- `start_date` / `end_date` when known
- `confidence` and evidence.

### 2. `maximum_amount` needs a basis: eligible expense vs insurer payment

Canadian plan wording can express limits as:
- maximum **eligible expense**;
- maximum **benefit payable / reimbursement**;
- a covered-expense base to which coinsurance applies;
- a per-visit cap;
- a combined pool;
- a lifetime cap.

These are not interchangeable.

A concrete example is the PSHCP explanation where $500 of eligible chiropractic expense reimbursed at 80% yields only $400 insurer-paid. Manulife also currently markets an 80%-of-$625 structure yielding a $500 combined maximum. A single `maximum_amount=500` cannot represent both safely.

**Recommendation:** add:
- `maximum_basis`: eligible_expense | insurer_payment | provider_charge | visit_count | unknown
- `maximum_amount`
- `coverage_percent`
- `calculation_order` or a normalized formula AST.

The optimizer must apply the maximum at the correct step.

### 3. Reasonable & Customary (R&C) is usually not a static plan-document number

Current `parser._extract_rc()` scans any R&C block and uses the smallest monetary amount in that block as the cap.

That is high risk. Canada Life states customary charges vary by geography and professional fee guides, are continually updated, and can differ by plan. Sun Life describes R&C as an insurer-determined normal range. R&C therefore often behaves like an **external eligibility rule resolved at claim time**, not a constant in the plan booklet.

In a block containing an annual maximum, per-visit amount, and R&C language, choosing the minimum dollar amount can silently invent an R&C cap.

**Recommendation:**
- replace `reasonable_customary_cap: float | None` with an object:
  - `applies: true/false/unknown`
  - `source`: insurer_dynamic | explicit_contract_amount | fee_guide | statutory | unknown
  - `amount` only when explicitly evidenced for the exact service/region/duration
  - `province_or_territory`
  - `service_duration_minutes`
  - `as_of_date`
  - `requires_live_verification`.
- If R&C applies but no exact current amount is evidenced, optimization should model a range or require verification rather than assume provider cost is fully eligible.

### 4. Combined/shared maxima are currently detected but not encoded

The parser adds a note when it sees `combined maximum`, but it does not populate `shared_pool_id` or `shared_pool_maximum`.

The optimizer only fails closed if those structured fields are populated. Therefore a combined maximum can currently pass through as if each category has its own independent maximum.

This is a P0 correctness issue because it can overstate available coverage across related practitioners.

**Recommendation:** when `combined`, `shared`, `aggregate`, or equivalent language is detected:
- create a shared-pool entity;
- attach all member benefit rules to the same pool ID;
- store pool maximum and period;
- set confidence low/manual review unless membership is unambiguous;
- never promote the individual category to high confidence merely because a percentage and one dollar amount were found.

### 5. Deductible and used-to-date defaults can overstate remaining coverage

`deductible_remaining` defaults to `0` and `benefit_used_to_date` defaults to `0`.

Those are not neutral defaults; they assert that the deductible is fully satisfied and no benefit has been consumed. If actual state is unknown, the optimizer can overstate insurer payment.

**Recommendation:**
- make both nullable/unknown;
- separate contract deductible from live member state:
  - deductible amount;
  - deductible scope (person/family/category/plan);
  - deductible period;
  - deductible satisfied-to-date / remaining;
- separate maximum from current utilization:
  - amount paid-to-date;
  - eligible expense accumulated-to-date;
  - visit count used;
  - source and `as_of`.
- Optimizer should require member-state evidence or present bounded scenarios rather than silently use zero.

### 6. Referral/prescription requirements need tri-state plus conditions

Current detection only sets true for a narrow set of phrases and otherwise leaves `None`.

Real plan requirements can be:
- required;
- explicitly not required;
- required only after a threshold;
- required for selected practitioner types;
- required for equipment/supplies but not services;
- waived under certain plan versions.

**Recommendation:** replace booleans with `RequirementRule`:
- `state`: required | not_required | conditional | unknown
- `condition`
- `issuer/provider_type`
- `validity_period`
- `evidence`.

Unknown must block an automated "covered" assertion when the requirement would materially affect eligibility.

### 7. Practitioner category and eligible provider credential must be separate

The beta categories combine terms such as psychologist, psychotherapist, counsellor, and social worker under `psychology`. Plans can cover these differently or place them in a shared pool. Eligibility also depends on recognized licensing/registration and location.

Canada Life policy wording ties coverage to licensed/registered providers; insurer product pages enumerate specific practitioner types rather than a generic mental-health category.

**Recommendation:** use:
- `service_category` (e.g. mental_health_therapy);
- `practitioner_type` (psychologist, social_worker, psychotherapist, clinical_counsellor, etc.);
- `credential_requirement`;
- `jurisdiction`;
- `shared_pool_id`.

Provider discovery should verify both category match and credential eligibility.

### 8. Coordination of Benefits (COB) is a separate multi-plan calculation layer

CLHIA G4 establishes payer-order rules and a total-payment ceiling of 100% of the eligible expense. Canada Life's current guidance confirms own plan vs dependent plan ordering and the birthday rule for children.

The current optimizer is single-plan. It should not try to "fold in" secondary coverage as a larger reimbursement percentage.

**Recommendation:** create a COB layer:
1. determine payer order;
2. adjudicate primary plan independently;
3. pass the primary explanation-of-benefits result / residual eligible amount to the secondary model;
4. cap aggregate payment at the applicable eligible expense;
5. retain each plan's independent R&C and eligibility semantics.

This should be a separate future lane or module, not an overloaded `BenefitRule`.

### 9. Waiting periods, eligibility prerequisites, and government-plan-first rules need representation

Current insurer materials include:
- waiting periods;
- coverage conditional on provincial health-plan eligibility;
- government/provincial plan first-payer requirements in some contexts;
- age-based cessation;
- per-claim deductibles and per-incident limits.

These are not required for the first paramedical optimizer milestone, but the schema needs an extensible eligibility/constraint model so they are not later forced into notes.

## Current-code risk map

### `benefitflow_beta/parser.py`

**P0**
- `_period()` incorrectly treats generic yearly wording as `benefit_year`.
- `_maximum()` selects the largest dollar amount in a text block without identifying what the amount means.
- `_extract_rc()` can invent an R&C cap by selecting the minimum dollar amount from a mixed block.
- combined maxima are only noted, not structurally represented.

**P1**
- confidence can become `high` when percentage + one maximum + a recognized period are present even if the amount basis or pool semantics are ambiguous.
- negative requirement phrases (`no referral required`) and conditional requirements are not normalized.
- line-block extraction can cross-associate adjacent values from a different practitioner row in complex plan tables.

### `benefitflow_beta/models.py`

**P0**
- `maximum_amount` has no semantic basis.
- unknown live state is represented by numeric zero for deductible remaining and benefit used to date.
- period anchors are missing.

**P1**
- provider credential/jurisdiction semantics are not attached to benefit eligibility.
- R&C is modeled as a scalar instead of a dynamic rule/evidence record.

### `benefitflow_beta/optimizer.py`

**P0**
- assumes `maximum_amount` means insurer-paid maximum.
- assumes missing R&C amount means full provider charge is eligible.
- assumes missing deductible/usage state is zero.

**P1**
- cannot model shared pools until parser populates them.
- does not model per-visit maximums separately from annual/lifetime maximums.
- does not distinguish eligible-expense maxima from benefit-payable maxima.

## Proposed normalized model shape

```text
BenefitRule
  service_category
  practitioner_types[]
  reimbursement
    percent
    maximum
      amount
      basis
      period
    per_visit_cap
      amount
      basis
    reasonable_customary
      applies
      source
      amount?
      jurisdiction?
      duration_minutes?
      as_of?
      requires_live_verification
  shared_pool_id?
  eligibility_constraints[]
  referral_requirement
  prescription_requirement
  provider_credential_rule
  evidence[]
  confidence

BenefitPool
  pool_id
  member_rule_ids[]
  maximum
    amount
    basis
    period

MemberBenefitState
  rule_id / pool_id
  deductible_remaining?
  insurer_paid_to_date?
  eligible_expense_to_date?
  visits_used?
  as_of
  evidence_source
```

## Required fail-closed tests

1. `80% of $500 eligible expenses` must not be normalized as `$500 insurer-paid maximum`.
2. `$500 maximum benefit payable at 80%` must not be treated as `$500 eligible-expense maximum`.
3. `combined $500/year across physio, massage, chiropractic` must never yield $500 independently for each category.
4. `benefit year begins on first claim` must not be reset on Jan 1.
5. `every 24 months` must preserve the correct anchor, not just `period_months=24`.
6. R&C language with no explicit current amount must not synthesize a numeric cap.
7. A block containing `$65 first visit`, `$45 subsequent visit`, `10 visits`, and a yearly maximum must preserve each semantic separately.
8. Unknown `benefit_used_to_date` must not be treated as zero.
9. Unknown deductible status must not be treated as fully satisfied.
10. Practitioner eligibility must preserve psychologist/social-worker/psychotherapist distinctions when the plan does.
11. A shared mental-health pool must decrement once across all member practitioner types.
12. Secondary-plan COB must never cause combined reimbursement to exceed the eligible expense.

## Recommended implementation order

1. **P0 schema hardening:** maximum basis, anchored periods, nullable member state, structured R&C, shared-pool representation.
2. **P0 parser hardening:** remove unsafe amount heuristics; emit ambiguity objects/manual-review state.
3. **P0 optimizer hardening:** refuse optimization on unknown maximum basis, unresolved pool membership, unknown deductible/usage state when material, and unresolved dynamic R&C when the result would depend on it.
4. **P1 table-aware extraction:** parse rows/cells rather than adjacent-line heuristics for insurer PDFs.
5. **P1 multi-plan COB module:** separate adjudication stages per plan.
6. **P1 provider credential rules:** jurisdiction-aware credential verification.

## Research disposition

**Finding:** The beta is conceptually viable, but benefit semantics should be hardened before expanding insurer coverage or automating more booking behavior. The most important near-term principle is: **do not convert textual ambiguity into a numeric zero or a confident maximum.**

This artifact does not modify accepted state and should be reviewed before integration.
