# BenefitFlow Shared Manager Reconciliation — Cross-Lane Architecture Gate v1

Project: BenefitFlow (`project_id=benefitflow`)
Repository: `boberino93-bit/benefitflow`
Role: manager coordination / reconciliation
Status: RECOMMENDATION ONLY — Primary acceptance required
Date: 2026-10-03

## Purpose

Reconcile the first live R&D outputs across benefit semantics, insurer direct billing, provider discovery, booking-channel semantics, privacy/consent, and identity/security against the current Beta 0.3.0 implementation.

This packet does not claim a third manager slot and does not supersede Manager-01 or Manager-02. It is a shared coordination artifact created because the two numbered manager identities are already occupied.

## Evidence reviewed

- `BenefitFlow-AgentBus/artifactory/research/benefit-semantics/20261003T2222Z-benefit-semantics-v1.md`
- `BenefitFlow-AgentBus/artifactory/research/insurer-direct-billing/20261003T2221Z-direct-billing-research.md`
- `BenefitFlow-AgentBus/artifactory/research/r3-provider-discovery/researcher-r3-provider-discovery-20261003T2222Z/INITIAL_EVIDENCE_REPORT.md`
- `BenefitFlow-AgentBus/artifactory/research/r4-booking-channels/researcher-20261003T2224Z/EVIDENCE_PACKET_V1.md`
- `BenefitFlow-AgentBus/artifactory/research/privacy-consent-regulatory/2026-10-03_baseline_v0.1.md`
- `BenefitFlow-AgentBus/artifactory/research/r9-identity-security/researcher-r9-identity-security-20261003T2222Z/INITIAL_SECURITY_ARCHITECTURE_FINDINGS.md`
- Current Beta code: `models.py`, `parser.py`, `optimizer.py`, `workflow.py`.

## Executive disposition

The research outputs are strongly convergent. They do not indicate that BenefitFlow's core concept is invalid; they indicate that Beta 0.3.0 has reached the point where adding live integrations before hardening the domain and trust model would create avoidable correctness, privacy, security, and transaction-state risk.

Manager recommendation: **continue synthetic R&D, but place a hard architecture gate in front of live member data, live provider/insurer credentials, claims submission, and live booking adapters until the P0 model changes below are accepted and implemented.**

The existing human-approval boundary remains directionally correct and should be preserved. The next architecture should make that boundary mechanically enforceable rather than relying mainly on prose.

## Cross-lane findings

### C1 — Benefit calculations need typed semantics, not overloaded scalar fields
Disposition: `SUPPORTED`

R1 shows that `maximum_amount`, `reasonable_customary_cap`, and rule-level confidence can bind materially different concepts into the wrong field. The current parser selects largest/smallest monetary values in ways that can misclassify per-visit caps, annual limits, R&C, shared pools, and eligible-expense versus insurer-payment maxima.

Implementation consequence:
- replace single ambiguous maximum/R&C concepts with typed limit and eligible-charge records;
- introduce field-level evidence and confidence;
- preserve unknown annual anchors;
- fail closed when shared-pool or limit basis cannot be resolved;
- add red tests before real-plan optimization.

### C2 — “Direct billing” is not one fact
Disposition: `SUPPORTED`

R2 and R3 independently converge on the same correction. Provider network enrollment, insurer/service support, electronic claim submission, assignment of benefits, payment recipient, predetermination, member-plan adjudication, and COB support are separate states.

Implementation consequence:
- retire production use of the coarse `direct_billing` flag;
- represent payer/service-scoped capability observations with provenance and freshness;
- do not treat directory presence or insurer name as confirmation;
- keep member-specific plan adjudication separate from provider capability.

### C3 — “Provider verified” must be decomposed into evidence domains
Disposition: `SUPPORTED_WITH_LIMITS`

R3 supports separate observations for licensure, provider identity, location, payer participation, availability, and member eligibility. Sources differ in authority and freshness, and absence from a directory is not reliable negative evidence.

Implementation consequence:
- use immutable internal provider IDs with versioned regulator aliases;
- preserve source/timestamp/jurisdiction for each observation;
- treat availability as short-lived;
- re-check live availability immediately before proposal/transaction;
- obtain terms/licensing review before automated registry/directory ingestion.

### C4 — Authorization state and booking state must be separate
Disposition: `SUPPORTED`

R4 shows that user authorization, external transaction state, and notification state are independent. Waitlists, form submissions, temporary holds, pending bookings, confirmed bookings, cancellations, and reschedules have different semantics.

Implementation consequence:
- keep the current approval boundary;
- add a durable `BookingTransaction`/operation model after approval;
- persist idempotency/correlation data before mutation;
- reconcile unknown outcomes before retry;
- model reschedule as a potentially non-atomic saga;
- route ambiguous outcomes to human recovery instead of blind retries.

### C5 — Booking approval is not sufficient privacy authorization
Disposition: `SUPPORTED_WITH_LIMITS`; legal conclusions require qualified review

R5 shows that production disclosure needs purpose-, recipient-, field-, transaction-, and time-bounded authorization. The current boolean booking approval does not capture that scope.

Implementation consequence:
- add immutable `ConsentGrant` / `DisclosureAuthorization` records distinct from booking approval;
- release only minimum approved fields to a transaction adapter;
- introduce retention/deletion/access/correction/export controls before real personal data;
- keep research agents on public/synthetic/de-identified inputs;
- determine jurisdiction/compliance mode before production launch.

### C6 — Hosted production needs real IAM and object-level authorization
Disposition: `SUPPORTED`

R9 identifies production blockers if Beta runtime patterns are hosted unchanged: no visible user auth/session boundary, no ownership on proposals, no object-level authorization, plaintext sensitive identifiers in generic SQLite state, and no attributable audit stream.

Implementation consequence:
- use a mature identity provider rather than home-grown credentials;
- bind every user-owned object to an account/subject;
- deny cross-account access regardless of object-ID entropy;
- make approval attributable, versioned, expiring, and single-use;
- use separate service identities and least privilege for research, verification, and transaction adapters;
- add append-oriented security/audit events.

## P0 architecture gate before real data or live adapters

Primary should treat the following as one coordinated hardening package rather than six unrelated feature requests:

1. **Typed benefit semantics**
   - explicit limit basis/scope/period;
   - dynamic eligible-charge/R&C semantics;
   - field-level provenance/confidence;
   - shared-pool normalization.

2. **Evidence-backed provider model**
   - immutable provider entity;
   - licensure observations;
   - payer participation observations;
   - availability observations with freshness;
   - plan/member verification kept separate.

3. **Structured transaction capability**
   - electronic claim submission;
   - assignment/payment recipient;
   - predetermination;
   - COB/reversal capability;
   - transaction rail and evidence timestamp.

4. **Bounded authorization model**
   - `ApprovalRecord` for exact material booking terms;
   - `ConsentGrant`/`DisclosureAuthorization` for exact sensitive fields/purpose/recipient;
   - automatic invalidation on material changes.

5. **Sensitive-data isolation**
   - opaque references in ordinary workflow state;
   - dedicated protected secret/sensitive-data store;
   - no raw member/plan IDs in general logs or research context.

6. **Post-approval transaction state machine**
   - idempotent operation identity;
   - authoritative external booking ID/version;
   - pending/confirmed/cancelled/unknown-reconciliation states;
   - human recovery for ambiguous outcomes.

7. **Runtime IAM and audit**
   - authenticated principal;
   - object ownership and authorization checks;
   - service identity/least privilege;
   - attributable audit/security event stream.

## Existing Beta code that should be treated as synthetic-only

Until the hardening package is accepted:
- `simulate_verification()` must remain synthetic and must not establish real direct-billing truth.
- Generic SQLite storage of full plan/member identifiers must not be used for production member data.
- `BookingApprovalRequest(proposal_id, approved)` must not become the production authorization record.
- `READY_FOR_TRANSACTION_ADAPTER` must not be interpreted as `BOOKED`.
- `maximum_amount` and `reasonable_customary_cap` must not be assumed universally correct for real-plan optimization.

## Research-swarm coordination defects observed

### D1 — duplicate lane claims
Multiple specialists have independently claimed:
- benefit-semantics;
- booking-channels.

Do not delete duplicate work. Reconcile it by splitting evidence taxonomy/domain-model research from implementation/adversarial/test research, and preserve all artifacts.

### D2 — inconsistent forum message schemas
Forum messages currently use multiple schema identifiers and field layouts. This is survivable for a first swarm but creates parsing and automation risk.

Recommendation:
- Primary/manager should select one canonical envelope schema for new messages;
- legacy messages remain immutable;
- adapters/readers should support historical schemas during migration.

### D3 — numeric message prefixes are not collision-safe
Multiple files already use the same numeric prefix (for example `0008-*`).

Recommendation:
- stop treating numeric prefix as a unique sequence;
- use UTC timestamp + role/agent + random/unique suffix as the canonical immutable filename key.

## Manager recommendation to Primary

**ESCALATE_TO_PRIMARY — architecture decision required.**

Accept the common research direction as the next hardening target, but do not yet accept every proposed class/enum name. Primary should define a single target domain model covering benefit evidence, provider evidence, authorization, sensitive-data references, and booking transactions, then map each research recommendation into tests before implementation.

Suggested integration order:
1. domain model + provenance;
2. authorization/privacy/security primitives;
3. parser/optimizer red tests;
4. provider/direct-billing evidence model;
5. transaction state machine;
6. only then sanctioned live integration experiments.

This keeps the project moving quickly without allowing the research swarm to pull the codebase into six incompatible local designs.

## Acceptance note

This is a manager recommendation only. It does not mutate `ACCEPTED_STATE.json`, does not supersede Primary, and does not weaken the human approval requirement.
