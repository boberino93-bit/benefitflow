# BenefitFlow R1 Secondary Validation — Fail-Closed Semantics Matrix

**Project:** BenefitFlow (`project_id=benefitflow`)  
**Lane:** R1 — benefit semantics / normalization  
**Agent:** `researcher-benefit-semantics-2026-10-03-a`  
**Date:** 2026-10-03  
**Status:** independent research evidence / proposal only; not accepted state  
**Purpose:** deconflicted validation of the existing R1 packet, focused on accumulator scope, incurred-date semantics, COB, maximum basis, and deterministic manual-review gates.

## 1. Executive disposition

The first R1 packet's core conclusion is independently supported: the dominant production risk is **semantic collapse**, not simple extraction failure.

This validation adds five concrete requirements that should be treated as P0 before BenefitFlow relies on projected reimbursement:

1. A deductible must be modeled as a scoped accumulator, not only as `deductible_remaining` on one benefit row.
2. Benefit-period consumption needs an explicit event anchor. Service/incurred date, submission date, adjudication date, and payment date must not be conflated.
3. Coordination of benefits must adjudicate each plan independently and preserve each plan's eligible-expense basis; it cannot be represented by increasing a reimbursement percentage or by subtracting the first payment from provider price.
4. Monetary maximums need an explicit basis such as `eligible_expense`, `benefit_payable`, `provider_charge`, `per_visit`, or `unknown`.
5. A parser result should be optimization-eligible only when all material semantic axes are resolved. A high extraction confidence score alone is not enough.

## 2. Evidence register

### E1 — Sun Life, Sun Solutions group-benefits guide

- **Owner/source:** Sun Life Assurance Company of Canada
- **Source type:** first-party insurer product/design guide
- **URL:** https://www.sunlife.ca/content/dam/sunlife/regional/canada/documents/gb/sunsolutions-tm-gb10118.pdf
- **Publication/update:** source currently published by Sun Life; document itself states descriptions are illustrative and contract wording prevails
- **Retrieved:** 2026-10-03
- **Jurisdiction/applicability:** Canadian group benefits; product-design capability evidence, not member-specific contract truth
- **Observed evidence:**
  - an EHC benefit year may be any 12-month period and may be calendar-year based;
  - yearly deductibles can be single or family;
  - EHC and drug deductibles can be separate, or Pay-Direct Drug coverage can share an annual deductible with EHC;
  - deductible carry-over can exist;
  - paramedical maximums can be per practitioner, combined across all practitioners, or combined across a selected subset;
  - per-visit maximums are an optional plan feature.
- **Confidence:** high that these semantic patterns exist; medium for any specific member plan.
- **Implementation consequence:** deductible, maximum and period scope must be explicit and must support shared accumulators.

### E2 — Manulife CoverMe, current Guaranteed Issue Enhanced / Flexcare product information

- **Owner/source:** Manulife / CoverMe
- **Source type:** first-party insurer product page / marketing information
- **URLs:**
  - https://www-aem-prod.coverme.manulife.ca/health-insurance/guaranteed-issue-enhanced-plan.html
  - https://www.coverme.com/content/experience-fragments/cmm/affinity/covme/en/categories/combo-plus/combo-plus.html
- **Retrieved:** 2026-10-03
- **Jurisdiction/applicability:** Canadian individual health products; demonstrates live semantic variants, but policy wording remains authoritative
- **Observed evidence:**
  - Manulife distinguishes calendar year, anniversary year, and benefit year;
  - some benefit-year definitions are anchored to the first claim/incurred date for the specified benefit;
  - a practitioner group can have a combined maximum with coinsurance;
  - mental-health coverage can use first-visit and subsequent-visit caps plus a combined visit count.
- **Confidence:** high on existence of distinct period anchors and mixed monetary/visit limits; medium on portability to other Manulife products.
- **Implementation consequence:** generic words such as `annual`, `yearly`, and `per year` cannot be promoted to a single period kind without an anchor.

### E3 — Canada Life, PlanDirect Guaranteed Plus sample policy

- **Owner/source:** The Canada Life Assurance Company
- **Source type:** first-party sample policy wording
- **URL:** https://www.canadalife.com/content/dam/canadalife/documents/insurance/plandirect/en/70-0109.pdf
- **Document marker:** 70-019 10/25 SAMPLE
- **Retrieved:** 2026-10-03
- **Jurisdiction/applicability:** Canadian individual health policy sample
- **Observed evidence:**
  - healthcare expenses are considered incurred when the person receives the covered service or supply;
  - reimbursement levels and a maximum benefit amount are separately stated.
- **Confidence:** high for this sample policy.
- **Implementation consequence:** record an explicit `incurred_at`/`service_at` anchor separately from claim submission and adjudication timestamps; do not infer maximum basis solely from a nearby percentage.

### E4 — CLHIA, current Coordination of Benefits guidance and Guideline G4

- **Owner/source:** Canadian Life and Health Insurance Association
- **Source type:** industry association guideline / current consumer clarification
- **URLs:**
  - https://www.clhia.ca/en-CA/Industry/clhia-guidelines/g04-coordination-of-benefits-group-health-and-dental
  - https://www.clhia.ca/en-CA/Consumers/Understanding-the-Coordination-of-Benefits
- **Retrieved:** 2026-10-03
- **Jurisdiction/applicability:** Canadian group health/dental coordination; individual policy wording can alter applicability
- **Observed evidence:**
  - payer order is governed by coverage status/rules rather than whichever plan is most generous;
  - combined payments cannot exceed 100% of the eligible expense;
  - the second payer may have its own eligible-expense/R&C determination, so a remaining provider balance does not guarantee a secondary payment;
  - current CLHIA clarification preserves special ordering rules for employee/student/dependent status and dependent children.
- **Confidence:** high for general COB design constraints; policy-specific ordering still requires the actual contracts.
- **Implementation consequence:** create a separate COB adjudication layer and preserve `eligible_expense` per plan.

### E5 — Canada Life, PSHCP member booklet

- **Owner/source:** Canada Life / Public Service Health Care Plan
- **Source type:** first-party plan member booklet
- **URL:** https://www.canadalife.com/content/dam/rfp/welcome-sites/pshcp/PSHCP-member-booklet.pdf
- **Retrieved:** 2026-10-03
- **Jurisdiction/applicability:** PSHCP only; useful as a concrete COB calculation example
- **Observed evidence:** for an eligible second-plan claim, the booklet describes reimbursement as the lesser of what the second plan would have paid as first payer and the remaining eligible expense after the first payer, with total reimbursement capped at 100% of eligible expense.
- **Confidence:** high for PSHCP.
- **Implementation consequence:** BenefitFlow must retain the first payer result and independently evaluate the second plan; `secondary_percent * residual_provider_charge` is not a safe formula.

### E6 — Sun Life, mental-health practitioner coverage update

- **Owner/source:** Sun Life
- **Source type:** first-party insurer operational/product update
- **URL:** https://workplace.sunlife.ca/en/group-benefits/advisor/advisor-latest-news/adding-new-mental-health-practitioners-to-standard-ehc-benefits-plans/
- **Published:** 2024 update for coverage effective May 12, 2024
- **Retrieved:** 2026-10-03
- **Jurisdiction/applicability:** Sun Life standard EHC plans, subject to plan design
- **Observed evidence:** Sun Life distinguishes practitioner types and states claim adjudication is based on credentials recognized through provincial regulatory bodies and/or associations.
- **Confidence:** high for Sun Life standard-plan credential handling.
- **Implementation consequence:** service category and practitioner credential/type must be separate normalized dimensions.

## 3. New implementation findings

### F1 — Deductible state must be an accumulator object

Current beta:

```text
BenefitRule.deductible_remaining: float = 0
```

That field collapses at least four dimensions:

- **scope** — member, family, category, drug/EHC combined, or plan-level;
- **period** — benefit year/calendar year/other;
- **sharing** — one deductible can be referenced by multiple benefit items;
- **state provenance** — amount remaining is live member state and can be stale or unknown.

Recommended normalized shape:

```text
Accumulator
  accumulator_id
  kind = deductible | maximum | visit_count | eligible_expense | insurer_paid
  scope = member | family | benefit_item | category | shared_pool | plan
  period_rule_id
  limit_amount?
  used_amount?
  remaining_amount?
  as_of?
  evidence_source?
  confidence
```

**Fail closed:** `remaining_amount = null` is not equivalent to zero.

### F2 — Incurred date must be first-class

At minimum preserve:

```text
service_at / incurred_at
claim_submitted_at
adjudicated_at
paid_at
```

A limit can apply by incurred/service date even if the claim is submitted or paid in a later period. The current model has no explicit claim-event anchor, creating a year-boundary failure mode.

**Example failure:** a December 2026 physiotherapy service submitted in January 2027 must not automatically consume 2027 benefits if the governing policy assigns it to the service/incurred date.

### F3 — COB needs per-plan adjudication records

Recommended shape:

```text
PlanAdjudication
  plan_id
  payer_order
  provider_charge
  eligible_expense
  deductible_applied
  reimbursement_before_max
  maximum_applied
  insurer_paid
  member_responsibility
  evidence
```

Then:

```text
COBResult
  adjudications[]
  total_insurer_paid
  total_member_paid
  unresolved_order_or_eligibility
```

Do not collapse COB into one synthetic coverage percentage.

### F4 — Maximum basis is mandatory for optimization

Minimum enum:

```text
eligible_expense
benefit_payable
provider_charge
per_visit_eligible_expense
per_visit_benefit_payable
visit_count
unit_count
unknown
```

`unknown` must block reimbursement optimization if the distinction changes the dollar result.

### F5 — Period anchor and accumulator scope are separate concepts

A period rule describes **when** the counter resets or rolls. An accumulator describes **what shares the counter**.

Do not encode both in category names or notes.

## 4. Deterministic fail-closed acceptance matrix

| Semantic axis | Safe normalized state | Unsafe/unknown state | Required product behavior |
|---|---|---|---|
| Coverage percentage | single known rate or fully specified tiers | missing, conflicting, or tier threshold unresolved | manual review |
| Maximum amount | known amount + known basis | amount found but basis unknown | manual review |
| Period | kind + anchor resolved | `annual`/`yearly` with unknown anchor when timing matters | manual review |
| Shared maximum | pool membership + shared accumulator resolved | text says combined/shared but members unclear | manual review |
| Deductible | accumulator scope + live state known, or deductible explicitly not applicable | remaining state defaulted/unknown | manual review or bounded scenario |
| R&C | explicit current cap or verified external rule with provenance | applies but amount/source/freshness unresolved | verification/manual review |
| Visit/unit limit | count + period + scope resolved | visit count found without period/scope | manual review |
| Referral/prescription/preapproval | explicit not-required, satisfied, or condition resolved | requirement unknown/conditional and material | manual review |
| Practitioner eligibility | practitioner type + credential rule resolved | only generic service label available | provider verification required |
| COB | payer order and first-payer adjudication evidence available | multiple plans exist but order/result unknown | no combined reimbursement projection |
| Incurred-date anchor | contract/event semantics known | only submission/payment date available | do not assign period consumption |
| Member utilization | as-of usage state known | usage silently defaulted to zero | manual review or worst/best-case range |

## 5. Concrete tests missing from Beta v0.3.0

### Parser / normalizer

1. `annual maximum $750` with no definition of annual period must not become a high-confidence `benefit_year`.
2. `80% of the first $625 of eligible expenses` must normalize maximum basis as `eligible_expense`, not `benefit_payable`.
3. `maximum benefit payable $500 at 80%` must normalize basis as `benefit_payable`.
4. `single $25 / family $50 deductible` must create a shared family accumulator rather than duplicate `$25` on each benefit.
5. `EHC and drugs share deductible` must point both benefit domains to the same accumulator ID.
6. `combined $1,500 for physiotherapy, massage, chiropractic` must create one pool and three membership references.
7. `calendar year`, `anniversary year`, and `12 months following first claim` must normalize to distinct period anchors.
8. first-visit `$65`, later-visit `$45`, and 10 combined visits must remain three distinct constraints.
9. generic `psychology` must not silently absorb psychotherapist/social-worker credential semantics when the plan distinguishes them.
10. `service received Dec 30; claim submitted Jan 4` must preserve Dec 30 as incurred date where policy wording uses service receipt.

### Optimizer

11. Unknown deductible state must not behave as zero.
12. Unknown benefit-used state must not behave as zero.
13. Eligible-expense maximum and benefit-payable maximum must produce different insurer-paid totals in a test where coinsurance is below 100%.
14. Shared family/category accumulator must decrement exactly once across multiple benefit items.
15. COB second-payer calculation must use the second plan's own eligible expense, not provider charge residual.
16. COB total must never exceed the applicable eligible expense.
17. An unresolved R&C rule must not assume the full provider charge is eligible.
18. A plan with known percentage/maximum but unknown maximum basis must enter `manual_review_categories`.

## 6. Proposed acceptance predicate

A benefit item should be eligible for automated dollar projection only when:

```text
coverage_rule_resolved
AND maximum_basis_resolved
AND period_anchor_resolved
AND shared_pool_membership_resolved
AND material_eligibility_gates_resolved
AND deductible_state_not_assumed
AND utilization_state_not_assumed
AND dynamic_eligible_charge_rule_resolved_or_bounded
AND provider_credential_requirement_resolved_when_material
AND cob_context_resolved_if_multiple_plans_present
```

If any predicate is false, the system may still explain the benefit text, but it should not present a single reimbursement number as a confident forecast.

## 7. Contradictions / limitations

- Sun Life's group-design guide documents supported configurations, not the terms of every Sun Life plan. Treat it as evidence of semantic possibilities, not as member coverage.
- Manulife product pages are product information/marketing. The issued policy remains authoritative.
- CLHIA guidance is a strong Canadian industry reference but explicitly notes policy wording and special cases can alter outcomes.
- The Canada Life sample policy is authoritative for the sample wording only, not all Canada Life group products.
- This packet does not establish insurer-specific R&C amounts, current member accumulator balances, or any individual member's coverage.
- This packet does not recommend implementing a full claims adjudicator. The immediate goal is to prevent BenefitFlow from expressing unsupported reimbursement certainty.

## 8. Recommendation to Manager / Reviewer

**Disposition requested:** `SUPPORTED_WITH_LIMITS`

Recommended P0 integration decision:

1. Replace zero defaults for unknown deductible/utilization state with nullable/explicit-unknown state.
2. Add `maximum_basis`, period anchor, and accumulator identity/scope before broadening the parser.
3. Add a separate COB context/result model instead of embedding secondary-plan math inside `BenefitRule`.
4. Gate dollar optimization on the acceptance predicate above.
5. Add the 18 tests above before expanding live insurer/plan coverage.

Primary acceptance is still required. This research packet does not modify accepted project state.
