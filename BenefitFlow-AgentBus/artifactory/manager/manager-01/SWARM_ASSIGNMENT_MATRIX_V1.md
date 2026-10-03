# BenefitFlow Swarm Assignment Matrix v1

Owner: Manager-01
Status: PREPARED — DO NOT LAUNCH WHILE R&D GATE IS CLOSED
Project: BenefitFlow
Repository: `boberino93-bit/benefitflow`

## Purpose

Convert the six broad prepared research lanes into ten bounded specialist assignments suitable for a ten-agent research swarm. Each assignment must be independently executable, evidence-first, privacy-minimized, and traceable back to the prepared lane taxonomy.

## Global specialist rules

Every specialist must:
- Resolve `project_id=benefitflow` and repository binding before work.
- Read the role bootstrap, R&D gate, accepted state, relevant forum messages, and this lane packet.
- Write only to the BenefitFlow research namespace assigned to that specialist.
- Use public/synthetic information only unless the human explicitly authorizes a narrower data scope.
- Never request or expose member IDs, plan IDs, credentials, claim numbers, authentication secrets, or unrelated personal data.
- Separate `observed evidence`, `interpretation`, `hypothesis`, `recommendation`, and `unknown`.
- Record source, publication/update date when available, jurisdiction/applicability, confidence, and contradictions.
- Treat vendor marketing claims as claims, not project truth, until corroborated.
- Escalate contradictory or safety-critical evidence rather than silently choosing a preferred answer.
- Never self-promote findings into accepted project state.

## Ten specialist assignments

### R1 — Benefit Semantics and Normalization
Prepared lane: `benefit-semantics`

Research scope:
- Benefit-year vs calendar-year vs rolling-period rules.
- Percentage coverage, fixed-dollar limits, deductibles, co-pay/co-insurance, visit limits, R&C/eligible-charge caps, exclusions, referral/prescription requirements, coordination-of-benefits interactions at a conceptual level.
- Ambiguity taxonomy and normalization failure modes.

Required output:
- Evidence-backed semantic model gaps.
- Edge-case matrix.
- Recommended parser/normalizer test cases.
- Explicit list of semantics that must fail to manual review.

### R2 — Insurer Direct Billing and Payer Variability
Prepared lane: `insurer-direct-billing`

Research scope:
- Direct-billing capability patterns.
- Provider/payer variability.
- Verification methods and freshness problems.
- Cases where direct billing does not imply final eligibility/payment.

Required output:
- Capability/constraint matrix.
- Verification evidence hierarchy.
- Staleness/failure modes.
- Product implications for wording and approval cards.

### R3 — Provider Discovery and Identity Resolution
Prepared lane: `provider-discovery-booking`

Research scope:
- Provider directories and authoritative vs aggregator sources.
- Specialty/service taxonomy mismatch.
- Location and identity resolution.
- Provider/clinic identity, duplicate records, stale listings, licensing/credential source boundaries where applicable.

Required output:
- Source-quality hierarchy.
- Entity-resolution risks.
- Freshness strategy.
- Recommended provider record provenance fields.

### R4 — Booking Channels and Confirmation Semantics
Prepared lane: `provider-discovery-booking`

Research scope:
- Booking APIs, hosted booking pages, forms, phone-only flows, email flows, waitlists, manual confirmation.
- Appointment-hold vs request vs confirmed-booking semantics.
- Cancellation/rescheduling/failure states.

Required output:
- Booking channel taxonomy.
- Transaction state model recommendations.
- Confirmation evidence requirements.
- Retry/idempotency and human-recovery concerns.

### R5 — Privacy, Consent, Data Minimization, and Regulatory Applicability
Prepared lane: `privacy-consent-regulatory`

Research scope:
- Consent boundaries.
- Data minimization, retention, disclosure, purpose limitation, and jurisdiction-dependent requirements relevant to a benefits-navigation/booking product.
- Distinguish legal text, regulator guidance, industry practice, and product recommendation.

Required output:
- Jurisdiction/applicability map.
- Data-classification and minimization recommendations.
- Consent/disclosure checkpoints.
- Unresolved questions requiring qualified legal review.

Restriction:
- Do not present legal conclusions as definitive legal advice.

### R6 — Voice and Phone Transaction Workflow
Prepared lane: `voice-transaction-workflow`

Research scope:
- Phone/voice booking workflows.
- Identity disclosure sequencing.
- Consent/recording considerations at a product-design level.
- Verification prompts, agent handoff, bounded transaction authorization, confirmation capture.

Required output:
- Call-state model.
- Sensitive-data disclosure gates.
- Failure/escalation conditions.
- Required audit evidence for a completed transaction.

### R7 — Product Economics and Operational Feasibility
Prepared lane: `product-economics-abuse`

Research scope:
- Unit economics for research/verification/booking assistance.
- Human-support burden.
- API/telephony/data-provider costs where publicly available.
- Value hypotheses, pricing models, and cost drivers.

Required output:
- Cost-driver model.
- Sensitivity ranges rather than false precision.
- Operational bottlenecks.
- Pilot metrics needed to validate economics.

### R8 — Abuse, Fraud, and Adversarial Product Risks
Prepared lane: `product-economics-abuse`

Research scope:
- Provider impersonation.
- Fabricated availability or verification.
- Benefit misuse incentives.
- Social engineering.
- Approval spoofing/replay.
- Prompt/data poisoning affecting research or transaction routing.

Required output:
- Threat/abuse catalog.
- Severity/likelihood assessment.
- Prevent/detect/recover controls.
- Red-team test scenarios.

### R9 — Identity, Authentication, Security, and Hosted Data
Prepared lane: `privacy-consent-regulatory` with security extension

Research scope:
- Authentication and account-recovery patterns.
- Least privilege.
- Secret isolation.
- Audit logs.
- Data-at-rest/in-transit expectations.
- Multi-tenant separation and hosted-state risks.

Required output:
- Security control baseline.
- High-risk trust boundaries.
- Authentication/account-recovery abuse cases.
- Security acceptance criteria for pilot readiness.

### R10 — Integration and Transaction Adapter Architecture
Prepared lane: `voice-transaction-workflow` with integration extension

Research scope:
- Calendar integration.
- Booking confirmation ingestion.
- Transaction adapter boundaries.
- Claims/insurer touchpoint constraints at an architectural level.
- Observability, retries, idempotency, reconciliation, and rollback/human recovery.

Required output:
- Adapter contract recommendations.
- Event/state transition model.
- Error taxonomy.
- Human-in-the-loop recovery requirements.

## Dependency graph

- R1 informs optimizer and parser assumptions for all downstream lanes.
- R2 + R3 inform provider verification and direct-billing confidence.
- R3 + R4 inform the booking proposal/transaction state machine.
- R5 constrains R6, R9, and R10.
- R8 adversarially reviews assumptions emerging from R2-R6 and R9-R10.
- R7 evaluates the operational cost consequences of R3, R4, R6, R9, and R10.
- R10 integrates architectural implications after evidence from R4-R6 and R9.

No dependency grants one specialist authority to overwrite another specialist's evidence. Contradictions are routed to manager reconciliation.

## Completion definition

A specialist lane is complete only when it provides:
1. Source-indexed evidence.
2. Applicability/freshness notes.
3. Contradictions and unresolved unknowns.
4. Implementation implications.
5. Recommended next tests or decisions.
6. A clear statement of what the evidence does **not** establish.

Manager review follows the separate evidence-review contract before anything is recommended to Primary.
