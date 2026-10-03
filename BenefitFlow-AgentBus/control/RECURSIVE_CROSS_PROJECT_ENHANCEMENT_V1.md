# BenefitFlow Recursive Cross-Project Enhancement Protocol V1

**Status:** ACTIVE / HUMAN-AUTHORIZED  
**Project:** `BenefitFlow` / `project_id=benefitflow`  
**Writable repository:** exactly `boberino93-bit/benefitflow`

## 1. Purpose

BenefitFlow agents continuously improve the project during active work by inspecting approved foreign Artifactory/AgentBus/framework repositories for reusable patterns, controls, tests, recovery practices, schemas, coordination mechanisms, and implementation techniques.

This is **read-only cross-project learning** followed by **BenefitFlow-local grafting**. It is not shared mutable state and it is not permission to modify another project.

## 2. Absolute foreign-repository invariant

For every source repository other than `boberino93-bit/benefitflow`:

- reads, metadata inspection, comparison, and provenance capture are allowed;
- creating, updating, deleting, renaming, merging, force-pushing, branching, tagging, commenting, dispatching workflows, opening/closing issues or PRs, or otherwise mutating foreign state is prohibited;
- source history is never rewritten to make it conform to BenefitFlow;
- foreign accepted truth never automatically becomes BenefitFlow accepted truth;
- secrets, credentials, personal data, production identifiers, or project-private payloads are not imported merely because an agent can see them.

Any attempted foreign mutation is a policy failure and must fail closed.

## 3. Authority model

`Human -> Primary -> Manager -> Research`

### Research

Research agents may scout registered foreign sources, identify reusable patterns, preserve provenance, classify uncertainty, and publish **enhancement candidates**. They do not graft candidates directly into accepted state.

### Manager

Managers review enhancement candidates for provenance, novelty, compatibility, safety, privacy, regression impact, project fit, duplication, and package consequences. They publish a disposition/recommendation to Primary.

### Primary

Primary alone may accept a candidate as BenefitFlow project truth and authorize a BenefitFlow-local graft, subject to human-reserved approval boundaries. Primary owns cross-candidate reconciliation, implementation coherence, regression validation, package parity, and recovery synchronization.

## 4. Source registry and cursor

The authoritative source list is `control/ENHANCEMENT_SOURCE_REGISTRY.json`.

The local scan cursor is `control/ENHANCEMENT_CURSOR.json`.

The cursor is BenefitFlow-owned state. Foreign repositories do not receive acknowledgements, markers, locks, or cursor writes.

A source cursor advances only after the scan result and any candidate/no-delta record have been durably persisted inside BenefitFlow.

## 5. Recursive enhancement algorithm

For each bounded enhancement interval:

1. **REVALIDATE**
   - confirm `project_id=benefitflow`;
   - confirm writable repository is exactly `boberino93-bit/benefitflow`;
   - confirm role and current swarm/bootstrap contracts;
   - load source registry and local cursor.

2. **SELECT**
   - choose the next registered foreign source deterministically by round-robin cursor unless Primary explicitly prioritizes a source;
   - inspect at most the configured number of sources for the interval.

3. **READ-ONLY SCAN**
   - fetch current foreign HEAD/ref;
   - inspect only relevant Artifactory, AgentBus, protocol, bootstrap, deployment, test, recovery, or tooling surfaces;
   - compare with the last locally recorded source ref;
   - perform no foreign mutation.

4. **EXTRACT CANDIDATES**
   - identify reusable *patterns*, not wholesale foreign project state;
   - record source repository, path, source ref/SHA, source file digest when available, observed behavior, rationale, expected BenefitFlow value, affected local surfaces, risks, tests, rollback, and package impact;
   - preserve the distinction between evidence and interpretation.

5. **CLASSIFY**
   Each candidate receives exactly one primary compatibility state:
   - `SAFE_REUSABLE` — concept can be adopted locally without semantic conflict;
   - `ADAPT_REQUIRED` — useful pattern but must be translated to BenefitFlow semantics;
   - `CONFLICT` — contradicts accepted BenefitFlow truth or safety/control boundaries;
   - `DUPLICATE` — already present or previously consumed;
   - `OUT_OF_SCOPE` — not materially useful to BenefitFlow;
   - `SENSITIVE_OR_PROHIBITED` — would import protected data, weaken isolation, or violate a human/safety boundary.

6. **DE-DUPLICATE / IDEMPOTENCY CHECK**
   - create a stable candidate fingerprint from source repo + source ref/path + concept identifier;
   - do not repeatedly re-import the same unchanged candidate;
   - a changed source ref may reopen evaluation only when the relevant pattern materially changed.

7. **ROLE REVIEW**
   - Research publishes candidate evidence;
   - owning Manager reviews and classifies disposition;
   - Primary accepts, rejects, defers, or requests more evidence.

8. **GRAFT LOCALLY**
   For an accepted candidate:
   - modify only BenefitFlow-owned files/code/protocols/tests;
   - adapt naming, authority, schemas, safety, and domain semantics to BenefitFlow;
   - never copy foreign accepted-state authority wholesale;
   - retain provenance back to the source pattern.

9. **VERIFY**
   - run or define relevant regression/contract checks;
   - verify project isolation and human approval invariants remain intact;
   - verify no sensitive foreign data was imported;
   - if verification fails, roll back or supersede the BenefitFlow-local graft only. Foreign state remains untouched.

10. **SYNCHRONIZE PACKAGES**
    If a graft changes identity, control-plane semantics, bootstraps, capabilities, schemas, routing, role responsibilities, safety boundaries, or recovery behavior:
    - update all affected PRIMARY, MANAGER, and RESEARCH bootstraps/packages;
    - rebuild/refresh recursive recovery context;
    - persist package parity and verification state before declaring the graft complete.

11. **ADVANCE CURSOR**
    - only after durable BenefitFlow persistence;
    - record source HEAD, scan time, candidate IDs or `NO_DELTA`, and disposition state.

12. **RECURSE TO FIXED POINT**
    - rescan local interfaces affected by the graft for newly exposed compatibility gaps;
    - optionally evaluate the next source on a later interval;
    - stop when there is no material delta, no unreviewed candidate, the configured recursion depth is reached, or further change would require human approval.

## 6. Bounded service model

This protocol does **not** create an autonomous background daemon and cannot wake dormant agents.

During an active work unit, each role treats enhancement scanning as a recurring service obligation at these checkpoints:

- at bootstrap/re-entry after project and role validation;
- once per meaningful active work cycle when bounded scan budget permits;
- after a material manager/Primary protocol or architecture acceptance;
- before successor/deployment package refresh or handoff;
- after recovery/succession revalidation;
- whenever the human explicitly requests enhancement review.

Default budget per interval:

- maximum foreign sources scanned: **1**;
- maximum new candidates emitted: **3**;
- maximum local recursive compatibility depth: **3**.

These bounds prevent self-enhancement from starving assigned project work or creating uncontrolled recursive self-modification.

## 7. Non-regression invariants

No recursively learned improvement may silently weaken or bypass:

- BenefitFlow project/repository isolation;
- human approval for external booking, financial action, sensitive identifier disclosure, or materially changed booking terms;
- the P0 architecture gate;
- role authority boundaries;
- evidence provenance and auditability;
- sensitive-data minimization;
- append-only material coordination history;
- package/recovery parity requirements;
- the foreign-repository read-only invariant itself.

A candidate that proposes weakening one of these is `CONFLICT` or `SENSITIVE_OR_PROHIBITED` and requires explicit human decision before any local policy change.

## 8. Candidate minimum record

Every material candidate must include:

- candidate ID and fingerprint;
- source project/repository;
- source path/ref/SHA and digest when available;
- observed pattern/evidence;
- compatibility state;
- expected BenefitFlow benefit;
- affected BenefitFlow surfaces;
- safety/privacy/security impact;
- regression/test plan;
- rollback/supersession plan;
- role package impact;
- Manager disposition;
- Primary disposition;
- implementation/graft refs when accepted.

## 9. Completion rule

An enhancement is not complete because a useful foreign pattern was found. Completion requires durable provenance, compatibility classification, Manager review, Primary disposition, BenefitFlow-local implementation when accepted, regression/invariant verification, package parity where affected, recovery synchronization, and cursor advancement.
