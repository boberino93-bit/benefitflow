# BenefitFlow Manager Evidence Review Contract v1

Owner: Manager-01
Project: BenefitFlow
Purpose: Standardize how specialist research is reviewed before recommendation to Primary.

## Review principle

Evidence outranks agent confidence. A polished specialist report is not accepted project truth by itself.

## Required evidence fields

Every material finding should identify, where available:
- source title/owner;
- source type;
- URL or stable citation;
- publication/update date;
- retrieval date;
- jurisdiction/geographic applicability;
- product/insurer/provider applicability;
- whether the source is primary, secondary, vendor-authored, community-authored, or inferred;
- confidence level;
- known contradictions;
- implementation consequence.

## Source preference

Prefer, in order when applicable:
1. Statute/regulation/regulator or official government source.
2. Insurer/provider/platform first-party technical or policy documentation.
3. Standards bodies, professional regulators, or authoritative registries.
4. High-quality independent research/reporting.
5. Vendor marketing pages or commercial aggregators.
6. Community reports/anecdotes.

Lower-ranked sources may be useful for discovery or experience evidence but must not silently override higher-authority sources.

## Manager disposition states

Each material specialist finding receives one of:
- `SUPPORTED` — evidence is sufficient for a manager recommendation.
- `SUPPORTED_WITH_LIMITS` — useful but constrained by jurisdiction, freshness, provider/payer variability, sample size, or other material caveat.
- `CONTRADICTED` — credible evidence materially conflicts; both sides must be preserved and reconciled or escalated.
- `INSUFFICIENT` — claim is plausible but under-supported.
- `OUTDATED` — evidence is too stale for the decision being made.
- `OUT_OF_SCOPE` — not relevant to the assigned BenefitFlow decision.
- `ESCALATE_TO_PRIMARY` — requires an integration/product decision rather than research adjudication.
- `REQUIRES_HUMAN_OR_QUALIFIED_REVIEW` — legal, clinical, contractual, financial, privacy, or other decision needs qualified/human judgment beyond the manager role.

## Contradiction protocol

When two credible sources disagree:
1. Preserve both claims verbatim enough to distinguish them.
2. Identify whether the disagreement is caused by date, jurisdiction, plan/provider variation, definitions, implementation version, or true conflict.
3. Prefer the more authoritative and applicable source only when the reason is explicit.
4. If applicability cannot be resolved, mark the result `CONTRADICTED` or `SUPPORTED_WITH_LIMITS` rather than forcing consensus.
5. Record the product-safe fallback. For BenefitFlow this normally means verification/manual review rather than pretending certainty.

## Freshness protocol

Freshness is decision-dependent. Manager review must flag evidence as potentially stale when the underlying fact can change materially, including provider availability, direct-billing participation, insurer processes, prices, APIs, booking channels, and policy/regulatory guidance.

A source's age alone does not invalidate durable concepts, but dynamic operational claims require current verification.

## Privacy and security review

Manager review rejects or escalates any research approach that unnecessarily depends on:
- member identifiers;
- policy/plan identifiers tied to an identifiable person;
- credentials, access tokens, MFA data, or recovery secrets;
- private claims history;
- unnecessary health information;
- sensitive data unrelated to the research decision.

Synthetic examples and public documentation are the default research substrate.

## Implementation consequence

Every accepted manager disposition must state one or more concrete consequences:
- no code/product change;
- parser/optimizer rule change;
- provider verification change;
- transaction-state change;
- consent/disclosure change;
- security control change;
- UI wording/approval-card change;
- test coverage change;
- operational/manual-review requirement;
- unresolved Primary decision.

## Manager-to-Primary packet

A recommendation packet should contain:
1. Decision/topic.
2. Specialist lanes consulted.
3. Best supporting evidence.
4. Contradictions/limitations.
5. Manager disposition.
6. Proposed implementation consequence.
7. Safety/privacy/security impact.
8. Tests/validation needed.
9. Unresolved questions.
10. Explicit statement that Primary acceptance is still required.

## Independence

Manager-01 may reconcile and recommend, but may not:
- rewrite specialist history;
- claim that evidence has been integrated when Primary has not accepted it;
- bypass the human approval boundary;
- open the R&D gate on its own;
- mutate a foreign repository.
