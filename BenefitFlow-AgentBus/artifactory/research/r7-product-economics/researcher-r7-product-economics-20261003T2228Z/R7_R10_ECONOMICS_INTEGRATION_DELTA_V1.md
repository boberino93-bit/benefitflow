# R7 ↔ R10 Economics Integration Delta v1

Project: BenefitFlow (`project_id=benefitflow`)  
R7 agent: `researcher-r7-product-economics-20261003T2228Z`  
Dependency reviewed: R10 Integration and Transaction Adapter Architecture v0.1  
Status: CROSS-LANE RESEARCH RECOMMENDATION / NOT ACCEPTED STATE  
Date: 2026-10-03

## Executive conclusion

R10's proposed transaction primitives give R7 the missing authoritative denominator model.

R7 should **not** create an independent booking-status store. Economics telemetry should derive transaction outcome from R10's normalized transaction/event stream and attach cost/work observations to R10 identifiers:

- `transaction_id`
- `operation_id`
- `attempt_id`

The critical economic distinction is:

- one business transaction may contain several logical operations;
- one logical operation may contain several transport attempts;
- multiple attempts are not multiple booking opportunities;
- a retry after transport failure is not a new booking unless material intent changed;
- reconciliation and human recovery are economic work that must be attributed to the original transaction.

## Identifier alignment

### R10 `transaction_id`

Use as the durable booking lifecycle key.

R7 interpretation:
- denominator unit for lifecycle cost;
- cancellation/reschedule work can be attributed to the original confirmed transaction;
- do not generate a competing economics-only transaction identifier.

### R10 `operation_id`

Use for one logical mutation/read objective.

R7 interpretation:
- unit for idempotency-safe retry analysis;
- all attempts for the same logical mutation roll up to the same operation;
- new material intent/new approval creates a new operation and therefore a new cost segment.

### R10 `attempt_id`

Use for each network/phone execution attempt.

R7 interpretation:
- unit for transport cost;
- voice minutes, API calls, message sends and transport failures attach here;
- repeated attempts increase cost without increasing the transaction denominator.

## R10 state → R7 economic outcome mapping

| R10 normalized state | R7 economic interpretation |
|---|---|
| `DRAFT` | no transaction cost denominator yet |
| `READY_FOR_EXECUTION` | approved opportunity |
| `EXECUTING` | transaction attempt in progress |
| `REQUEST_SUBMITTED` | request cost incurred; not confirmed |
| `AWAITING_EXTERNAL_CONFIRMATION` | wall-clock latency; follow-up may create human cost |
| `HOLD_ACTIVE` | temporary external state; not confirmed |
| `WAITLISTED` | transaction work incurred; not confirmed |
| `CONFIRMED_BOOKED` | authoritative confirmed-booking numerator |
| `REAPPROVAL_REQUIRED` | rework/approval-friction event |
| `RESCHEDULE_PENDING` | post-confirmation operating cost |
| `CANCELLATION_PENDING` | post-confirmation operating cost |
| `CANCELLED` | lifecycle outcome; original confirmation remains historically real |
| `REJECTED` | failed conversion with incurred cost |
| `FAILED_RETRYABLE` | attempt/operation cost; not terminal transaction failure yet |
| `FAILED_FINAL` | terminal failed transaction |
| `RECONCILIATION_REQUIRED` | exception-cost event; block blind retry |
| `HUMAN_RECOVERY_REQUIRED` | highest-cost exception class |
| `SUPERSEDED` | preserve historical cost; do not double-count active transaction |
| `FULFILLED` | post-booking outcome when completion can be established |

## Confirmation denominator

R7 confirms the following hard metric rule:

```text
confirmed_booking_count
=
count(distinct transaction_id
      whose normalized state reached CONFIRMED_BOOKED)
```

Do not increment for:

- `REQUEST_SUBMITTED`
- `WAITLISTED`
- `HOLD_ACTIVE`
- successful adapter HTTP response alone
- completed phone call alone
- calendar projection alone
- hosted-page open/handoff alone.

## Attempt economics

Recommended per-attempt measures:

- adapter ID/version;
- channel type;
- transport start/end;
- API request count;
- voice seconds;
- SMS segments;
- email/messages;
- model calls where attributable;
- direct vendor charge;
- active human time;
- transport failure class.

Formula:

```text
operation_transport_cost =
sum(attempt vendor costs for operation_id)
```

This must include failed/retried attempts.

## Reconciliation economics

When R10 enters `RECONCILIATION_REQUIRED`, R7 should emit/derive:

- reconciliation started timestamp;
- reconciliation ended timestamp;
- active human reconciliation time;
- read-back/API calls;
- external status queries;
- additional phone/message contacts;
- result:
  - equivalent state found;
  - booking confirmed;
  - booking absent/safe retry;
  - duplicate found;
  - material conflict;
  - human escalation unresolved.

Metrics:

```text
reconciliation_rate =
transactions entering RECONCILIATION_REQUIRED
/
transactions with at least one execution attempt
```

```text
reconciliation_cost_per_100_attempted_transactions =
sum(reconciliation variable + scenario labour cost)
/
attempted transactions
* 100
```

Report p50/p95 human reconciliation time.

## Human recovery economics

`HUMAN_RECOVERY_REQUIRED` should have explicit reason codes.

Minimum cost-relevant classes:

- external state cannot be determined;
- provider changed material terms;
- unsupported adapter capability;
- authentication/partner-access blocker;
- counterparty identity uncertainty;
- disclosure authorization insufficient;
- booking duplicate risk;
- cancellation/reschedule conflict;
- clinic requires unsupported manual process.

R7 recommendation:

Set an explicit pilot `human_recovery_budget` measured in active minutes or scenario cost. Crossing the budget should route to user-visible fallback rather than creating an unbounded concierge obligation.

The exact threshold is a Primary/product decision after pilot data; R7 does not prescribe it yet.

## Adapter capability economics

R10 adapter descriptors should be extended or joined with economics metadata:

```json
{
  "economics": {
    "commercial_terms_status": "KNOWN|UNKNOWN|NOT_APPLICABLE",
    "pricing_model": "PER_CALL|PER_TRANSACTION|SUBSCRIPTION|PARTNER_CONTRACT|FREE_PUBLIC|UNKNOWN",
    "marginal_cost_observable": true,
    "manual_fallback_required_when_unsupported": true
  }
}
```

This is recommendation-only; commercial pricing belongs in a separate versioned cost catalog rather than in immutable adapter logic.

## Cost catalog separation

Do not hard-code vendor prices into transaction events.

Recommended structure:

```text
cost_rate_catalog
- rate_id
- vendor/system
- cost_type
- source_currency
- unit
- unit_price
- pricing_source
- effective_from
- effective_to
- observed_at
- contract_reference_or_public_source
```

Transaction/economics events should reference the observed rate/version used.

This allows:
- price changes without rewriting events;
- contract vs list-price comparison;
- FX scenarios;
- historical re-costing.

## Calendar projection economics

R10 correctly treats calendar state separately from booking authority.

R7 recommendation:

Track calendar projection operational cost separately:

- projection API calls;
- sync/push subscription maintenance;
- projection reconciliation;
- calendar conflicts;
- support contacts caused by calendar mismatch.

Never charge calendar failure against `booking_confirmation_rate`.

Report a separate:

```text
calendar_projection_success_rate
```

and

```text
calendar_projection_support_minutes_per_confirmed_booking
```

## Reschedule economics

A reschedule can be more expensive than a new booking because it can involve:

1. read current external state;
2. fresh user approval;
3. cancellation/change operation;
4. creation or confirmation of replacement slot;
5. reconciliation;
6. calendar update.

R7 recommends treating reschedule as a linked operation saga and reporting:

- cost per reschedule;
- p50/p95 human minutes;
- percent requiring fresh approval;
- percent requiring human recovery;
- failed-reschedule rate.

Do not hide reschedule cost inside original booking cost without also reporting it separately.

## Cancellation economics

Report:

- cancellations per confirmed booking;
- automated cancellation rate;
- human minutes per cancellation;
- ambiguous cancellation rate;
- provider fee/penalty observation where explicitly known and safely represented.

Cancellation penalties should not be treated as BenefitFlow operating cost unless BenefitFlow itself bears them; otherwise they are user/provider financial outcomes.

## Funnel integration

Recommended lifecycle funnel now becomes:

```text
proposal presented
-> proposal approved
-> R10 READY_FOR_EXECUTION
-> execution attempted
-> request/hold/waitlist/pending
-> CONFIRMED_BOOKED
-> calendar projected
-> rescheduled/cancelled/fulfilled
```

Each stage has its own conversion and cost.

## Required cross-lane invariants

1. R7 telemetry must never override R10 normalized transaction state.
2. R10 transaction state must not embed labour-rate assumptions.
3. R7 price catalogs must not determine authorization.
4. A transport retry with the same `operation_id` is cost, not a new booking denominator.
5. A new material operation after reapproval is separate work but remains linked to the transaction lifecycle.
6. Calendar projection never establishes booking confirmation.
7. Reconciliation cost is first-class and cannot be dropped from unit economics.
8. Human recovery cost must be reason-coded.
9. Unknown partner fees remain unknown, not zero.
10. Synthetic beta events must never contaminate production unit-economics metrics.

## Instrumentation compatibility change to R7 draft schema

The R7 draft economics event schema should add nullable fields:

- `transaction_id`
- `operation_id`
- `attempt_id`
- `adapter_id`
- `adapter_version`
- `transaction_state_before`
- `transaction_state_after`

R7 should defer the exact state enum to R10 rather than copy it into a permanently separate enum.

## Manager/Primary recommendation

Reconcile R7 instrumentation and R10 transaction architecture as one event architecture:

- R10 owns business/audit truth;
- R7 consumes/augments those events with time/resource/cost observations;
- reporting derives metrics from the combined event stream.

This prevents two state machines, denominator drift, and duplicated sensitive workflow data.

## What this delta does not establish

- It does not accept R10 architecture into project state.
- It does not define production storage technology.
- It does not set vendor prices or labour rates.
- It does not authorize external transactions.
- It does not change the current human approval boundary.

## Research disposition

`CROSS_LANE_ALIGNMENT_READY_FOR_MANAGER_REVIEW`
