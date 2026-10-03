# BenefitFlow R1 / 5f9d — Adversarial Parser + Optimizer Gap Analysis v2

**Project:** BenefitFlow  
**Project ID:** `benefitflow`  
**Researcher:** `researcher-benefit-semantics-5f9d`  
**Lane:** R1 — Benefit Semantics and Normalization  
**Sublane:** current code/schema/parser/optimizer gap analysis, adversarial examples, implementation recommendations, and tests  
**Status:** evidence/proposal only; requires manager disposition and Primary acceptance  
**Date:** 2026-10-03

## 1. Claim / question

Does BenefitFlow beta v0.3.0 safely represent and calculate common Canadian extended-health plan structures, or can its current flat schema and extraction heuristics produce confident-but-materially-wrong reimbursement estimates?

## 2. Current code surface reviewed

Static review targets:

- `benefitflow_beta/models.py` — current `BenefitRule`
- `benefitflow_beta/parser.py` — category block extraction and numeric binding
- `benefitflow_beta/optimizer.py` — eligible-charge, deductible, maximum and budget calculation
- `tests/test_parser.py`
- `tests/test_optimizer.py`

The existing tests validate clean annual/rolling periods, adjacent-category isolation, a basic R&C cap, user-budget enforcement, and fail-closed behavior when the maximum/period is missing. They do not currently exercise mixed per-visit + annual limits, shared pools, maximum-eligible-expense accounting, waiting periods, ambiguous annual anchors, or coordination of benefits.

## 3. External evidence

### E1 — Sun Life current product pages: concurrent limit types are normal

**Authority:** Sun Life (first-party insurer/product source)  
**Applicability:** Canadian individual health products; useful as real-world plan-language evidence, not universal plan rules.  
**Freshness:** current page retrieved 2026-10-03; page update date not stated.  
**Source quality:** primary commercial source.

Sun Life publishes plan designs containing, concurrently:

- reimbursement percentage;
- per-visit maximum;
- annual maximum per practitioner/type;
- combined annual maximum;
- visit-count limits;
- lifetime and multi-year limits;
- waiting periods.

Examples include $25 per visit plus $250 per year per practitioner, and other tiers with $300 per practitioner plus a combined $500/$650 calendar-year maximum. Psychology/social-work designs can use a dollar-per-visit limit plus a visit-count limit.

Sources:
- https://www.sunlife.ca/en/choices/health-coverage-choice-extended-health-care-and-dental-plans/
- https://www.sunlife.ca/en/health/personal-health-insurance/basic-plan/
- https://www.sunlife.ca/en/health/personal-health-insurance/enhanced-plan/

### E2 — Pacific Blue Cross: R&C and contractual limits are separate concepts

**Authority:** Pacific Blue Cross  
**Applicability:** Canadian benefits; conceptual evidence for R&C semantics.  
**Freshness:** article originally published 2013; still publicly maintained/retrievable as of 2026-10-03, but exact current operational values are time-sensitive.  
**Source quality:** primary insurer source.

Pacific Blue Cross describes reasonable-and-customary limits as usual fees for comparable services in a geographic area. It separately states that contractual dollar or visit limits can be lower than the R&C limit and then govern reimbursement.

Source:
- https://pac.bluecross.ca/advicecentre/story/reasonable-customary/

### E3 — Canada Life PSHCP: “maximum eligible expense” is not the same as insurer-payment maximum

**Authority:** Canada Life / Public Service Health Care Plan member material  
**Applicability:** PSHCP example; demonstrates a real accounting basis that BenefitFlow must distinguish.  
**Freshness:** current member booklet retrieved 2026-10-03.  
**Source quality:** primary administrator/plan source.

Canada Life gives an example where:
- provider charge = $75;
- R&C eligible charge = $60;
- reimbursement = 80%;
- chiropractic maximum eligible expense = $500/calendar year;
- therefore maximum annual reimbursement = $400, not $500.

Source:
- https://www.welcome.canadalife.com/content/dam/rfp/welcome-sites/pshcp/PSHCP-member-booklet.pdf

### E4 — CLHIA G4: coordination uses plan-specific eligible expense and total payment ceiling

**Authority:** Canadian Life and Health Insurance Association  
**Applicability:** Canadian group health/dental coordination framework.  
**Freshness:** current CLHIA page retrieved 2026-10-03.  
**Source quality:** industry standards/guideline body.

CLHIA states that combined plan payments for a particular item cannot exceed 100% of eligible medical/dental expense, and defines eligible expense before some payment limitations. Each plan can calculate eligible expense using its own R&C/fee-guide basis.

Sources:
- https://www.clhia.ca/en-ca/industry/clhia-guidelines/g04-coordination-of-benefits-group-health-and-dental
- https://www.clhia.ca/en-CA/Consumers/Understanding-the-Coordination-of-Benefits

## 4. Observed facts from current implementation

### F1 — `maximum_amount` has no accounting basis

`BenefitRule.maximum_amount` does not say whether the value caps:
- eligible expense;
- insurer payment;
- billed/provider charge;
- per-visit reimbursement;
- per-practitioner annual reimbursement;
- a shared pool.

`optimizer.py` subtracts `benefit_used_to_date` and `insurer_used` directly from `maximum_amount`, which operationally treats every maximum as an insurer-payment ceiling.

### F2 — `_maximum()` chooses the largest dollar value in the extracted block

For a recognized period, `_maximum()` collects all dollar values and returns the maximum numeric amount. Numeric magnitude is therefore used as a proxy for semantic type.

### F3 — `_extract_rc()` chooses the smallest dollar value when R&C language is present

If a block contains R&C/eligible-charge language, `_extract_rc()` returns the smallest dollar amount in that block, even when that amount is a contractual per-visit limit.

### F4 — “annual” is normalized to `benefit_year`

`_period()` maps `annual` and `annually` to `benefit_year` when no explicit calendar-year string is present. “Annual” alone does not establish the reset anchor.

### F5 — shared-pool language is noted but not normalized

The parser can append a note when “combined maximum” appears, but it does not construct `shared_pool_id` or `shared_pool_maximum`, so the optimizer’s shared-pool fail-closed path is not reliably activated.

### F6 — block extraction reads at most one following non-category line

A benefit whose reimbursement, R&C language, and annual maximum are split across three lines can lose the third-line maximum and be forced to manual review.

This is a safe false-negative compared with a wrong estimate, but it is an expected real-document layout failure.

## 5. Adversarial fixtures and deterministic current behavior

### A1 — Per-visit dollar cap + visit-count limit

Input:

> Psychologists and social workers: 100% reimbursement, $75 per visit up to 10 visits per year.

Current parser semantics:
- coverage = 100%;
- period = `benefit_year`;
- maximum_amount = $75;
- visit_limit = 10.

**Problem:** `$75` is a per-visit cap, but because “10 visits per year” establishes a recognized annual period, `$75` is also promoted into `maximum_amount`. The optimizer can therefore cap the entire year at $75 of insurer payment rather than applying up to $75 to each of 10 visits.

**Severity:** P0 — confident material underestimation.

### A2 — R&C phrase + contractual per-visit + annual maximum

Input:

> Massage therapy: 80% reimbursement, subject to reasonable and customary charges, maximum $25 per visit and $250 per year.

Current parser semantics:
- maximum_amount = $250;
- reasonable_customary_cap = $25.

**Problem:** the parser relabels the contractual $25/visit maximum as the R&C cap. The source evidence explicitly distinguishes these concepts.

**Severity:** P0 semantic corruption even if some simple arithmetic cases coincidentally produce the same payable amount.

### A3 — Per-practitioner max + combined pool

Input:

> Physiotherapy: 100% reimbursement, $300 per year per practitioner and combined maximum $500 per calendar year.

Current parser semantics:
- maximum_amount = $500;
- no structured per-practitioner $300 limit;
- no structured shared pool.

**Problem:** one category can be allowed to consume $500 even though its own practitioner/category cap is $300, and separate categories can each independently receive the same $500 ceiling because the pool relationship is absent.

**Severity:** P0 overestimation risk.

### A4 — Maximum eligible expense misread as insurer-payment maximum

Real PSHCP-like configuration:
- billed = $75/visit;
- R&C eligible charge = $60/visit;
- reimbursement = 80%;
- 10 visits;
- maximum eligible expense = $500/calendar year.

Correct plan logic from the Canada Life example:
- first $500 of eligible expense is reimbursable at 80%;
- annual insurer reimbursement ceiling = $400;
- on 10 x $75 visits with $60 R&C, annual insurer reimbursement = $400;
- total member out-of-pocket = $350.

Current optimizer if represented as:
`coverage_percent=80`, `maximum_amount=500`, `reasonable_customary_cap=60`:
- insurer payment = $480;
- member payment = $270.

**Error:** insurer reimbursement overstated by $80 and member cost understated by $80 because the model lacks `maximum_basis=eligible_expense`.

**Severity:** P0 — material financial estimate error.

### A5 — Ambiguous annual anchor

Input:

> Vision care: 100% reimbursement, maximum $300 annually.

Current parser:
- period = `benefit_year`;
- maximum = $300;
- confidence can reach high.

**Problem:** the reset anchor was never established. Treating an unspecified annual period as benefit-year can produce the wrong remaining-balance/reset date.

**Severity:** P1; must fail to manual review until anchor is resolved.

### A6 — Waiting period ignored

Input:

> Vision care: 100% reimbursement, $300 maximum every 24 months. One-year waiting period applies.

Current parser:
- 100%;
- $300;
- rolling 24 months;
- no structured waiting-period eligibility constraint.

**Problem:** a structurally “high-confidence” benefit can be scheduled before coverage is active.

**Severity:** P0 for booking/utilization recommendations.

### A7 — Three-line document wrapping

Input:

> Physiotherapy: 80% reimbursement  
> subject to reasonable and customary charges  
> annual maximum $750 per calendar year.

Current block extraction retains only the category line plus the next non-category line. The annual maximum on line three can be dropped.

**Result:** incomplete semantics/manual review.

**Severity:** P1 usability/coverage; fail-closed behavior is correct, extraction robustness is not.

## 6. Contradictions / nuance

1. R&C treatment is insurer- and plan-specific. Pacific Blue Cross evidence supports geography-sensitive R&C and contractual override behavior, but it does not establish one universal calculation order for every payer.
2. A contractual per-visit maximum and an R&C cap can sometimes produce the same numeric eligible amount. That does not make the concepts interchangeable because appeals, updates, geographic tables, and downstream explanations differ.
3. “Annual maximum” language is common on insurer marketing pages without always exposing the full legal reset definition. Marketing-page language must not be treated as sufficient to infer the authoritative reset anchor.
4. Coordination-of-benefits rules vary with plan type and circumstance; R1 should define the schema/need for payer ordering, while detailed transaction behavior belongs with downstream lanes and qualified policy review.

## 7. Implementation consequences

### P0 schema changes

Replace ambiguous `maximum_amount` semantics with typed limits, minimally:

- `amount`
- `unit`: `currency | visits | days | units`
- `basis`: `eligible_expense | insurer_payment | billed_expense | reimbursement_per_visit | unknown`
- `scope`: `per_visit | per_practitioner | per_category | shared_pool | per_person | family | lifetime`
- `period_kind`
- `period_anchor`
- `pool_id`
- `confidence`
- `evidence_span`

R&C / eligible-charge logic should be separate from contractual limits:

- `eligible_charge_method`: `fixed_cap | reasonable_customary | fee_guide | negotiated_schedule | unknown`
- `eligible_charge_amount` only when explicitly stated
- `jurisdiction`
- `service_code/duration` where relevant
- `lookup_required`
- `evidence_span`

### P0 parser changes

1. Do not choose semantic type by largest/smallest dollar value.
2. Bind each amount to nearby lexical labels and units.
3. Preserve multiple simultaneous limits.
4. Treat “R&C applies” as a rule reference, not a fixed numeric cap, unless the exact R&C amount is explicitly present.
5. Do not map bare `annual/annually` to a known reset anchor.
6. Parse waiting periods and exclusions as eligibility gates or mark manual review.
7. Create structured shared-pool membership when combined-maximum language is present; otherwise fail the affected categories to manual review.

### P0 optimizer changes

Use an explicit calculation path:

1. confirm eligibility / waiting period / provider requirements;
2. provider billed amount;
3. determine eligible charge;
4. apply deductible;
5. apply reimbursement percentage;
6. apply each typed limit according to its accounting basis and scope;
7. apply prior usage to the same bucket;
8. apply shared-pool depletion;
9. apply payer-order/COB rules if present;
10. calculate member out-of-pocket.

No estimate should be auto-optimized when a material limit’s `basis`, `scope`, or period anchor is unresolved.

## 8. Proposed red tests

The following tests should fail against the current beta and become acceptance tests for the hardened model:

- `test_parser_does_not_promote_per_visit_cap_to_annual_maximum`
- `test_parser_does_not_label_contractual_per_visit_limit_as_rc`
- `test_parser_preserves_per_practitioner_and_combined_pool_limits`
- `test_optimizer_distinguishes_max_eligible_expense_from_max_insurer_payment`
- `test_parser_bare_annually_keeps_period_anchor_unknown`
- `test_waiting_period_blocks_planning_until_effective`
- `test_shared_pool_depletes_once_across_categories`
- `test_field_level_confidence_can_block_only_material_unknowns`
- `test_wrapped_three_line_benefit_preserves_semantics_or_fails_closed`
- `test_cob_never_exceeds_plan_specific_eligible_expense_and_requires_prior_payer_result`

A companion proposed test skeleton is stored beside this report.

## 9. Privacy / security impact

The recommended schema does not require additional member identifiers. It can be implemented using plan-rule metadata, provenance, usage totals, and jurisdictional/service context.

Field-level evidence should store the minimum excerpt/span needed to justify an extracted rule, not entire member documents when unnecessary. Sensitive plan/member identifiers should remain outside specialist research context and outside reusable evidence fixtures.

## 10. Uncertainty / missing evidence

- Exact insurer-specific R&C tables and calculation procedures are dynamic and may not be public.
- Marketing pages do not replace authoritative policy documents.
- The correct cross-plan coordination engine requires further insurer/plan-specific evidence and downstream R2/R10 input.
- The project still needs a formal migration design from the current `BenefitRule` API to typed-limit objects without breaking existing beta clients.

## 11. Recommended disposition

**ESCALATE_TO_PRIMARY**

Reason: A1, A3, A4, and A6 are not cosmetic parser limitations; they can create materially wrong benefit availability or reimbursement estimates while the current object may appear sufficiently complete to optimize.

Recommended Primary decision:
- declare the current flat `maximum_amount` representation **synthetic-beta-only**;
- block real-plan auto-optimization until typed limit basis/scope and eligibility gates are implemented;
- accept the proposed adversarial tests as P0 hardening criteria.

## 12. What this evidence does not establish

This report does **not** establish:
- that every insurer uses the cited plan structures;
- that BenefitFlow can determine actual claim eligibility from marketing material;
- any guaranteed reimbursement amount for a real member;
- legal conclusions about plan administration;
- that all required schema fields listed above are sufficient for every Canadian benefit product.

It establishes that the current beta representation is not expressive enough to safely distinguish several common, documented plan structures and that specific current heuristics can deterministically misclassify them.
