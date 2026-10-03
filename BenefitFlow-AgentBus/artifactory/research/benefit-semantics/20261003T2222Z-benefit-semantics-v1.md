# BenefitFlow Research Evidence — Benefit Semantics v1

**Project:** BenefitFlow  
**Project ID:** `benefitflow`  
**Role:** specialist researcher  
**Lane:** `benefit-semantics`  
**Status:** evidence/proposal only; requires reviewer disposition before Primary acceptance  
**Date:** 2026-10-03

## Executive finding

BenefitFlow's current beta has the right safety instinct—fail closed on ambiguity—but its benefit model still collapses several materially different insurance concepts into single scalar fields. The largest near-term risk is not missing a category; it is assigning the *right number to the wrong semantic slot* (for example, treating a contractual per-visit maximum as a reasonable-and-customary cap, or treating an annual maximum on eligible expenses as an insurer-payment maximum).

Before the optimizer is trusted with real plan documents, BenefitFlow should move from a flat `BenefitRule` toward explicitly typed limit, eligibility, and coordination objects with field-level provenance and confidence.

## Current implementation reviewed

Current beta model and parser reviewed:

- `benefitflow_beta/models.py`
- `benefitflow_beta/parser.py`
- `benefitflow_beta/optimizer.py`
- repository README / Beta v0.3.0 architecture

Observed current fields include `coverage_percent`, `maximum_amount`, `period_kind`, `visit_limit`, `shared_pool_id`, `reasonable_customary_cap`, deductible/usage state, referral/prescription flags, rule-level confidence, and one evidence excerpt.

The optimizer currently assumes `maximum_amount` is an insurer-payment ceiling and treats `reasonable_customary_cap` as a static per-visit eligible-charge ceiling. Those assumptions are not universally safe across Canadian benefit designs.

## External evidence

### 1. Reasonable & customary (R&C) is not just another fixed plan maximum

Pacific Blue Cross describes R&C limits as usual fees for comparable services in a geographic area and notes that paramedical R&C can apply per treatment and to the number of treatments in a timeframe. It also states that a lower contractual dollar or visit limit governs when the plan contract is more restrictive.

Source: Pacific Blue Cross, “Understanding Reasonable and Customary Limits”  
https://pac.bluecross.ca/advicecentre/story/reasonable-customary/

Sun Life similarly describes R&C as the normal range for a specific health-related service or procedure, while separately exposing plan-specific visit and other limits.

Source: Sun Life, “Check Your Coverage”  
https://www.sunlife.ca/en/support/check-your-coverage/

Canada Life’s PSHCP material states that R&C varies by geographic area and may use published provincial/territorial association fee guides.

Source: Canada Life, “Public Service Health Care Plan — Member booklet”  
https://www.canadalife.com/content/dam/rfp/welcome-sites/pshcp/PSHCP-member-booklet.pdf

**Implication:** `reasonable_customary_cap: float` is too narrow as a canonical semantic. R&C should be represented as an eligibility-pricing rule that may depend on geography, service type/code, duration, date, and external fee tables.

### 2. Per-visit, per-practitioner, visit-count, and combined-pool limits coexist

Sun Life publishes designs where paramedical benefits can have reimbursement percentages, a per-visit maximum, a per-practitioner annual maximum, and a combined annual maximum across multiple practitioners. Other designs use a visit-count limit instead.

Sources:
- Sun Life, “Health Coverage Choice”  
  https://www.sunlife.ca/en/choices/health-coverage-choice-extended-health-care-and-dental-plans/
- Sun Life, Benefit Choices Program Guide  
  https://www.sunlife.ca/content/dam/sunlife/regional/canada/documents/cxo/hsbc-2024-benefit-choices-actives-guide-en-online.pdf
- Pacific Blue Cross, Personal Health FAQ  
  https://www.pac.bluecross.ca/personal-health/faq

**Implication:** a single `maximum_amount` plus `visit_limit` cannot safely express all common combinations. BenefitFlow needs multiple concurrent limit records with explicit scope and basis.

### 3. “Maximum” can mean different accounting bases

Canada Life’s PSHCP examples distinguish billed cost, R&C eligible expense, co-payment, and maximum eligible expense. Reimbursement is then calculated from the eligible amount rather than simply applying the percentage to the provider’s bill.

Source: Canada Life, PSHCP Member booklet  
https://www.canadalife.com/content/dam/rfp/welcome-sites/pshcp/PSHCP-member-booklet.pdf

**Implication:** BenefitFlow must distinguish at least:
- billed amount,
- eligible amount,
- insurer payable amount,
- member co-pay,
- deductible,
- amount consumed from a plan limit.

The optimizer currently treats `maximum_amount` as a cap on insurer dollars paid. That can be wrong when a plan maximum is defined as maximum eligible expenses.

### 4. Coordination of benefits is a first-class semantic, not an afterthought

CLHIA Guideline G4 establishes ordering rules when a covered individual can claim under multiple group plans and states that combined payments cannot exceed 100% of the eligible expense.

Source: Canadian Life and Health Insurance Association, Guideline G4  
https://www.clhia.ca/en-CA/Industry/clhia-guidelines/g04-coordination-of-benefits-group-health-and-dental

Canada Life also instructs PSHCP members to submit to applicable provincial/territorial or other third-party sources first, then submit remaining eligible expense with the other payer’s explanation of benefits.

**Implication:** BenefitFlow needs payer-order and residual-claim semantics. A single-plan optimizer can otherwise overstate available reimbursement or recommend the wrong submission sequence.

## High-risk semantic defects in the current parser

### A. `annual` / `per year` is over-resolved

`_period()` maps `benefit year`, `per year`, `annual`, and `annually` to `benefit_year`.

That is unsafe. “Annual” does not necessarily reveal the reset anchor. A plan may mean calendar year, policy year, benefit year, or another defined anniversary.

**Recommendation:** add `annual_unspecified` or an explicit `period_anchor` with `unknown` until the plan definition is found.

### B. `_maximum()` binds by numeric magnitude, not meaning

The parser gathers dollar values from a block and uses the largest amount as the maximum.

This can confuse:
- per-visit cap vs annual cap,
- one practitioner’s maximum vs another practitioner’s maximum,
- combined pool maximum vs category maximum,
- eligible-expense maximum vs insurer-payable maximum.

**Recommendation:** bind every amount to nearby labels and units; never infer semantic type from largest/smallest numeric value.

### C. `_extract_rc()` can create a false R&C cap

When R&C language occurs in a block, `_extract_rc()` returns the smallest dollar value in that block.

A plan sentence can simultaneously say “subject to R&C” and “$25 maximum per visit.” In that case `$25` is contractual, not necessarily the insurer’s R&C value.

**Recommendation:** R&C should be `dynamic/lookup/unknown` unless the document explicitly provides an R&C amount for the exact service context.

### D. Rule-level confidence is too coarse

A rule can correctly identify a category and reimbursement percentage while misbinding its period maximum. One overall confidence label hides this.

**Recommendation:** attach confidence and evidence provenance per extracted field/constraint.

### E. Shared pools are detected but not normalized

The parser only adds a note when it sees “combined maximum”; it does not create a stable pool object or members.

The optimizer correctly refuses to auto-optimize when a shared pool is explicitly populated, but the parser does not reliably populate it.

**Recommendation:** make combined-pool extraction a structured output or force the entire affected group to manual review.

## Proposed canonical model direction

Do not simply add more scalar fields to `BenefitRule`. Split the concept.

### `BenefitCoverageRule`
- `category`
- `reimbursement_percent`
- `reimbursement_basis`: `eligible_expense | billed_expense | schedule_amount | unknown`
- `member_scope`: `individual | family | dependent | unknown`
- `effective_from`
- `effective_to`
- `field_evidence[]`

### `BenefitLimit`
- `limit_type`: `currency | visits | days | units`
- `amount`
- `basis`: `eligible_expense | insurer_payment | billed_expense | visit_count | unknown`
- `scope`: `per_service | per_visit | per_practitioner | per_category | shared_pool | per_person | family`
- `period_kind`: `calendar_year | plan_year | benefit_year | rolling_months | lifetime | annual_unspecified | unknown`
- `period_months`
- `pool_id`
- `service_duration_minutes` / service-code discriminator when relevant
- `field_evidence[]`

### `EligibleChargeRule`
- `method`: `fixed_cap | reasonable_customary | fee_guide | negotiated_schedule | unknown`
- `fixed_amount`
- `jurisdiction`
- `service_code`
- `service_duration_minutes`
- `effective_date`
- `external_lookup_required`
- `field_evidence[]`

### `EligibilityRequirement`
- `requirement_type`: `licensed_provider | registered_provider | referral | prescription | prior_authorization | medical_necessity | government_plan_first | other`
- `value`
- `jurisdiction`
- `field_evidence[]`

### `CoordinationRule`
- `payer_id`
- `payer_type`
- `priority`
- `residual_claim_allowed`
- `requires_eob_from_prior_payer`
- `combined_payment_cap_percent`
- `field_evidence[]`

## Calculation pipeline recommendation

The optimizer should calculate in an explicit sequence rather than treating plan inputs as interchangeable caps:

1. Start with provider billed amount.
2. Apply service eligibility and provider credential requirements.
3. Determine eligible charge using contractual cap / R&C / fee guide.
4. Apply deductible rules.
5. Apply reimbursement percentage/co-insurance.
6. Apply the correct plan limit according to its accounting basis.
7. Apply prior usage to the same limit bucket.
8. If coordination applies, process payer order and residual eligible expense.
9. Compute member out-of-pocket.
10. Optimize only when all material fields in the calculation path meet a minimum confidence threshold.

This sequence should be represented in explainable output so a user can see *why* a visit is expected to cost a given amount.

## Immediate red-test fixtures

These should be added before expanding real-document parsing:

1. **Per-visit + annual practitioner max**
   - 80% reimbursement
   - $25 per visit
   - $250/year per practitioner
   - prove the parser does not label $25 as R&C.

2. **Combined pool**
   - 70% reimbursement
   - $1,500 combined annual maximum across multiple paramedical practitioners
   - prove categories share one depletion bucket.

3. **R&C below billed price**
   - provider bills $75
   - R&C = $60
   - reimbursement = 80%
   - expected insurer amount $48 before other limits.

4. **Visit-count limit**
   - $25/visit
   - 12 visits/year
   - prove visit count and dollar cap remain independent.

5. **Annual period with unknown anchor**
   - text says “$500 annually” but no calendar/benefit/policy definition nearby
   - parser must preserve unknown anchor and require review.

6. **COB**
   - primary and secondary plans
   - combined payment never exceeds 100% eligible expense
   - secondary calculation requires the primary result/EOB.

## Priority recommendation

**P0 before real-plan optimization:** correct amount-to-semantic binding and field-level evidence.

**P1:** explicit multiple-limit representation, shared pools, dynamic R&C, period anchors.

**P1:** coordination-of-benefits model and payer sequencing.

**P2:** richer service-code/duration semantics, claim deadlines, prior authorization, and jurisdiction-specific credential requirements.

## Research disposition

This report is evidence/proposal only. It does not modify application code, accepted control state, or release artifacts. Reviewer should validate the proposed model boundaries, then Primary can decide whether to harden the beta schema/parser before the next implementation package.
