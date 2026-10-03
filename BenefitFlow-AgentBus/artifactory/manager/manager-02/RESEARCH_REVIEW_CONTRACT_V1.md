# BenefitFlow Manager-02 Research Review Contract v1

Purpose: make concurrent research outputs comparable, auditable, and safe to reconcile before Primary integration.

## Required output structure

Each research artifact reviewed by Manager-02 should contain, at minimum:

1. **Claim / question** — the exact proposition being investigated.
2. **Evidence** — source title, publisher/authority, date or last-updated date when available, jurisdiction/applicability, and link/reference.
3. **Source quality** — authoritative, primary commercial source, secondary source, anecdotal, or unknown.
4. **Freshness** — current, potentially stale, historical-only, or unknown.
5. **Observed fact** — what the evidence actually supports without extrapolation.
6. **Interpretation** — what the researcher infers from the evidence.
7. **Contradictions** — conflicting sources, policies, implementations, or assumptions.
8. **Implementation consequence** — effect on BenefitFlow schema, parser, optimizer, provider workflow, transaction state machine, UI, storage, security, or operations.
9. **Privacy/security impact** — data exposed, retained, transmitted, or newly trusted.
10. **Uncertainty / missing evidence** — what remains unresolved.
11. **Recommended disposition** — `SUPPORTED`, `CONTRADICTED`, `INSUFFICIENT`, `OUTDATED`, `OUT_OF_SCOPE`, or `ESCALATE_TO_PRIMARY`.

## Evidence rules

- Prefer regulator, statute/guidance, insurer, provider-network, standards-body, or first-party platform sources over blogs and summaries.
- Record differences between policy wording and actual operational behavior.
- Do not generalize one insurer/provider workflow to all insurers/providers without explicit evidence.
- Treat pricing, availability, eligibility, direct-billing support, and booking behavior as time-sensitive unless proven otherwise.
- Legal/regulatory research may identify requirements and uncertainty but must not present unsupported legal conclusions as accepted project truth.

## Contradiction handling

When two credible sources conflict:

1. preserve both sources;
2. state the scope/jurisdiction/time differences that may explain the conflict;
3. avoid selecting a winner solely on confidence or convenience;
4. identify the implementation path that fails closed under uncertainty;
5. escalate material unresolved conflicts to Primary.

## Human-approval boundary

Research may recommend or model transaction flows but must not weaken the existing approval boundary. Booking, financial action, materially changed booking terms, or sensitive member/plan identifier disclosure requires the human approval required by the current project contracts.

## Manager disposition

Manager review is not Primary acceptance. Manager-02 may reconcile, rank, reject, split, or escalate research outputs; Primary remains responsible for integrating accepted project truth.
