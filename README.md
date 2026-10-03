# BenefitFlow Alpha v0.4.0

BenefitFlow is an evidence-backed benefits-navigation and appointment-coordination proof of concept. It turns plan wording, user priorities, and an annual out-of-pocket budget into a utilization plan, provider-evidence workflow, scoped approval, and a simulated booking lifecycle.

## Alpha 0.4 demonstrator

The end-to-end demo now supports:

`benefit text/PDF -> evidence-backed normalization -> budgeted utilization plan -> synthetic provider discovery -> field-level provider evidence -> transaction-time verification -> exact approval card -> irreversible scoped authorization -> synthetic transaction lifecycle -> confirmation/reconciliation state -> sanitized audit trail`

The simulator deliberately demonstrates that a request, hold, waitlist, successful transport, completed call, or calendar projection is **not** a confirmed appointment. Only the `CONFIRMED_BOOKED` state is treated as a confirmed booking, and a calendar projection is created only after that state.

Available synthetic transaction scenarios:
- confirmed booking;
- waitlisted / not booked;
- retryable transport failure before business action;
- ambiguous outcome after request submission, requiring reconciliation rather than blind retry;
- provider rejection.

## P0 hardening demonstrated in this build

- Benefit semantics/provenance primitives remain fail-closed on material ambiguity.
- Demo upload/text size bounds protect hosted parser paths from unbounded input.
- Approval decisions are durably recorded and cannot be reversed on the same proposal.
- Approval and allowed disclosure categories are explicit.
- Raw demo plan/member identifiers are not persisted in proposal workflow state; only masked tails/categories are retained.
- Provider facts are represented as assertion-level evidence with separate freshness/provenance.
- The local transaction simulator uses stable transaction/operation/attempt identities and is idempotent per proposal.
- Ambiguous post-send outcomes enter `RECONCILIATION_REQUIRED` and block blind retry.
- Calendar projection is downstream of authoritative confirmation.
- Sanitized audit output contains no raw member/plan identifiers.

These are proof-of-concept controls, not a claim that the complete production P0 gate is satisfied.

## Run

```bash
python -m pip install -r requirements.txt
python run_beta.py
```

Open `http://127.0.0.1:8000`.

## Test

```bash
python -m pytest -q
python framework_reference/tests/run_all.py
```

CI runs both suites on pushes to `main` and also validates/generates PRIMARY, MANAGER, and RESEARCH successor packages.

## Project state

- Canonical identity: `BenefitFlow` / `project_id=benefitflow`.
- R&D Round 1: **CLOSED** by explicit human directive.
- All R1-R10 research slots: `COMPLETE_ROUND1`.
- Current phase: **P0 hardening / implementation**.
- Primary: `chatgpt-primary-2026-10-03`.
- GitHub/AgentBus is authoritative project state. Slack is an optional secondary operational tool only; material results must be persisted back to the repository/forum.
- Foreign enhancement-source repositories are read-only. Reusable patterns may be inspected and grafted only into BenefitFlow through the accepted review/disposition process.

Authoritative controls live under `BenefitFlow-AgentBus/control/`.

## Safety boundary

Alpha 0.4 does **not**:
- place live phone calls;
- create real appointments;
- log into insurer/provider accounts;
- use live provider or insurer credentials;
- submit claims;
- charge money;
- disclose real member/plan identifiers;
- provide clinical advice.

The accepted P0 architecture gate remains active. Real member data, credentials, claims submission, live booking adapters, and financial actions remain blocked until the required authorization, privacy, security, IAM/audit, evidence-provenance, transaction-state, and verification controls are implemented and verified.

## Intended progression

1. **Alpha 0.4 PoC** — synthetic end-to-end demonstrator.
2. **Closed pilot** — limited real plan information + curated provider evidence, no autonomous external transactions.
3. **Integration pilot** — one sanctioned provider/insurer/booking integration after P0 controls and qualified privacy/legal review.

## Project isolation and recovery

BenefitFlow coordination state lives only under `BenefitFlow-AgentBus/`. Recursive backups, successor packages, forum persistence, project binding, cross-project enhancement controls, swarm history, and package parity requirements remain in force.
