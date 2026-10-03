# BenefitFlow Research — Benefit Semantics Lane, Initial Findings v0.1

**Project:** BenefitFlow (`project_id=benefitflow`)  
**Role:** specialist/researcher  
**Lane:** `benefit-semantics`  
**Researcher ID:** `researcher-benefit-semantics-r01`  
**Date:** 2026-10-03  
**Status:** evidence/proposal only; not accepted project state

## Objective

Validate the beta benefit-normalization model against current public Canadian insurer language before the optimizer is allowed to treat parsed benefit rules as deterministic coverage.

## Evidence reviewed

1. Sun Life, *Health Coverage Choice — Extended health care and dental plans*:
   https://www.sunlife.ca/en/choices/health-coverage-choice-extended-health-care-and-dental-plans/
2. Manulife CoverMe, *Guaranteed Issue Enhanced Plan*:
   https://www-aem-prod.coverme.manulife.ca/health-insurance/guaranteed-issue-enhanced-plan.html
3. Manulife, *Flexcare with Vitality sample policy contract*:
   https://www-aem-prod.coverme.manulife.ca/content/dam/affinity/coverme/english/documents/sample-policy-flexcare-with-vitality-contract.pdf
4. Pacific Blue Cross, *Understanding Reasonable and Customary Limits*:
   https://www.pac.bluecross.ca/advicecentre/story/reasonable-customary
5. Pacific Blue Cross, *Personal Health FAQ / plan comparison*:
   https://www.pac.bluecross.ca/personal-health/faq
6. Canada Life, *Find an eligible health and dental service provider*:
   https://www.canadalife.com/insurance/workplace-benefits/eclaims-provider-listing.html
7. Canada Life, *Public Service Health Care Plan member booklet*:
   https://www.canadalife.com/content/dam/rfp/welcome-sites/pshcp/PSHCP-member-booklet.pdf
8. Canada Life, *PlanDirect policy booklet — Guaranteed Plus without drugs*:
   https://www.canadalife.com/content/dam/canadalife/documents/insurance/plandirect/en/70-0108.pdf
9. Sun Life, *eClaims for paramedical providers*:
   https://www.sunlife.ca/sl/provider/en/paramedical/eclaims/

## High-confidence findings

### F1 — “Per year” cannot safely be normalized to one universal period type

The beta parser currently maps `benefit year`, `per year`, `annual`, and `annually` to `benefit_year`.

Public insurer language shows this is unsafe:

- Sun Life explicitly states many maximums are **per calendar year** unless otherwise stated.
- Manulife explicitly distinguishes **calendar year** from **benefit year**, and defines benefit year for at least one product as a 12-month period beginning with the first claim for the specified benefit.
- Pacific Blue Cross product examples also use yearly limits, but other benefit constructs can be tied to multi-year or staged periods.

**Proposal:** a bare phrase such as `per year` or `annual` should remain unresolved until the document's governing definitions/defaults are found. Do not infer `benefit_year` from wording alone.

### F2 — Reasonable-and-customary (R&C) is usually an adjudication rule, not a static numeric cap

Pacific Blue Cross describes R&C as the range of usual fees for comparable services in a geographic area, says the allowed amounts are reviewed on a continual basis, and notes that R&C can interact with per-treatment and treatment-count constraints.

Manulife describes usual/reasonable/customary charges as insurer-determined relative to standard fees charged by providers of similar standing in the same geographical area.

This creates a material parser risk: the current `_extract_rc()` function treats the minimum dollar amount found in any block containing R&C language as the R&C cap. A nearby annual maximum, visit amount, deductible, or unrelated limit can therefore be mislabeled as the eligible-charge cap.

**Proposal:** represent R&C as a policy constraint unless the source explicitly ties a numeric amount to the R&C limit. Numeric extraction should require a local syntactic relationship, not mere co-occurrence.

### F3 — A single `maximum_amount + period_kind` is not expressive enough

Current insurer examples routinely layer multiple simultaneous limits:

- reimbursement percentage;
- per-visit maximum;
- annual maximum;
- practitioner-specific maximum;
- combined/shared maximum;
- visit-count maximum;
- lifetime maximum;
- equipment replacement frequency;
- incident-specific maximum.

Sun Life examples combine per-visit limits, per-practitioner annual limits, combined annual limits, and reimbursement percentages. Manulife examples combine annual, every-N-year, and lifetime limits. Pacific Blue Cross examples include per-visit and visit-count limits.

**Proposal:** move from one maximum field to a list of limit objects. Keep the current scalar fields only as backward-compatible projections when the rule is truly simple.

### F4 — “Every N years” has multiple semantics and should not be collapsed into rolling months

Insurer materials use constructs such as:

- every two calendar years;
- every five years;
- lifetime;
- per incident;
- first policy year versus later policy years;
- benefit year anchored to first claim.

These are not equivalent to a generic rolling 24/60-month window.

**Proposal:** period semantics should include both `window_kind` and `anchor_kind`, for example:
`calendar_year`, `calendar_years`, `benefit_year`, `policy_year`, `rolling_months`, `first_claim_anchored`, `policy_anniversary`, `tenure_year`, `incident`, and `lifetime`.

### F5 — Eligibility conditions extend well beyond referral/prescription flags

Current public product language includes conditions such as:

- waiting periods before a benefit becomes eligible;
- expense must occur in the home province/territory;
- physician documentation after a treatment threshold;
- provincial-plan-first rules;
- provider registration/eligibility;
- predetermination or insurer review for some services.

**Proposal:** add a structured `eligibility_conditions` collection rather than continuing to add one-off booleans.

### F6 — “Direct billing confirmed” is too coarse for production decisions

Canada Life states that a provider appearing on its provider list may be eligible, but claims are **not guaranteed** and remain subject to the member's plan rules. Sun Life describes eClaims as a mechanism for a provider to direct bill on a patient's behalf. Canada Life's PSHCP booklet explains that registered providers can submit claims electronically and, in that plan context, the insurer can pay the provider directly.

These are distinct facts:

1. provider can submit eClaims;
2. provider accepts assignment/direct payment;
3. insurer supports that transaction type for the provider;
4. member's specific plan covers the service;
5. the particular claim is payable.

**Proposal:** replace a single direct-billing enum with separate capability and claim-eligibility state. Never present provider eClaims capability as a coverage guarantee.

### F7 — Coordination of benefits / payer sequencing affects the optimizer

Public insurer materials show that some expenses must first be submitted to another payer (for example, provincial coverage in specified cases) and that coordination rules can change the member's remaining payable amount.

The current optimizer assumes one insurer and one member out-of-pocket remainder.

**Proposal:** future optimization should model payer sequence / coordination-of-benefits separately from the base benefit rule. Until then, plans with known secondary-payer semantics should fail to manual review rather than produce a precise reimbursement estimate.

### F8 — Predetermination is a first-class workflow state, not just another benefit note

Canada Life materials expose electronic predetermination transactions and product policy language describes a predetermination as an estimated amount payable for a proposed treatment within a defined validity window.

**Proposal:** add `predetermination_required/recommended`, `predetermination_status`, `valid_until`, and evidence fields to the workflow model. A predetermination result should not be represented as final claim payment.

## Recommended schema direction

```text
PlanDefinitions
  default_period_semantics
  defined_terms[]
  jurisdiction
  policy_effective_date

BenefitRule
  category
  reimbursement_rules[]
  limits[]
  eligibility_conditions[]
  reasonable_customary_policy
  coordination_rules[]
  evidence[]

LimitRule
  limit_type: monetary | visit_count | per_visit | frequency | lifetime | incident
  amount_or_count
  scope: category | practitioner | shared_pool | item | person
  window_kind
  window_size
  anchor_kind
  effective_from / effective_to
  confidence
  evidence

ReasonableCustomaryPolicy
  applies
  numeric_cap (optional)
  geography_basis (optional)
  provider_category_basis (optional)
  externally_adjudicated
  effective_date (optional)
  confidence
  evidence

BillingCapability
  provider_eclaims_capable
  assignment_of_benefits_supported
  insurer_provider_transaction_supported
  plan_claim_eligibility: unknown | verified | not_eligible
  evidence
```

## Immediate parser hardening recommendations

1. Change `_period()` so bare `per year` / `annual` does **not** become `benefit_year` without a governing definition.
2. Change `_extract_rc()` so R&C plus any dollar amount in the same block is insufficient to create a numeric cap.
3. Detect multiple limits in one block and force manual review rather than selecting `max(amounts)`.
4. Detect shared/combined pools structurally instead of only adding a note.
5. Extract document-level definitions before category-level rules.
6. Preserve source span/page identifiers for every normalized field, not only one combined excerpt.
7. Add explicit ambiguity codes so the optimizer can fail closed for specific reasons.

## Priority test fixtures to add

- **T1:** Sun Life paramedical rule with reimbursement %, per-visit max, annual practitioner max, and combined max.
- **T2:** Manulife benefit-year definition anchored to first claim.
- **T3:** Pacific Blue Cross R&C language with no explicit numeric R&C cap.
- **T4:** Canada Life provider listed/eClaims-capable but claim not guaranteed.
- **T5:** multi-year replacement limit (`every 2/5 years`) versus rolling-month semantics.
- **T6:** waiting-period and home-province eligibility condition.
- **T7:** coordination-of-benefits / provincial-plan-first scenario.
- **T8:** predetermination estimate with validity window.

## Severity / project impact

**Severity: HIGH for beta-to-pilot hardening.**

The current beta correctly fails some ambiguous cases to manual review, but several existing normalization shortcuts can turn ambiguous text into falsely precise optimizer inputs. The highest-risk cases are:

- `per year` -> `benefit_year`;
- R&C phrase + unrelated dollar amount -> false numeric R&C cap;
- one selected monetary maximum standing in for multiple concurrent limits.

These should be hardened before using real plan documents to generate user-facing reimbursement estimates.

## Handoff

This artifact is a specialist proposal for reviewer/Primary reconciliation. It does not modify accepted state and does not authorize live insurer/provider transactions.
