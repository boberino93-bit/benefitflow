# BF-ENH-0004 — Executable local-only recursive enhancement engine

Status: `DISCOVERED / AWAITING_MANAGER_REVIEW`
Compatibility: `ADAPT_REQUIRED`
Target project: BenefitFlow

## Provenance

Source repository: `boberino93-bit/intercommunicationsenhancements`
Previous locally recorded source HEAD: `707865e0125a16039ac8fb36dde6dcd5597fce6a`
Observed current source HEAD: `a0799ffcf429801dfd165916d22e0a27ce4244ae`
Comparison: source advanced by 15 commits.

Relevant source surfaces:
- `protocols/recursive_self_enhancement.md`
- `org_agent_mesh/self_enhancement.py`
- `schemas/enhancement_candidate.schema.json`
- `tests/test_self_enhancement.py`

Foreign source remains reference-only and was not mutated.

## Observed reusable pattern

The source now contains an executable bounded recursive enhancement engine rather than protocol text alone. Notable controls include:
- a read-only peer adapter surface with no mutation methods;
- traversal-free relative peer-path validation;
- exact peer revision pinning per cycle;
- source-content SHA-256 provenance;
- deterministic candidate IDs;
- local-project-root path enforcement;
- no-overwrite collision failure for candidate persistence;
- bounded recursion depth, candidate count, and artifacts per peer;
- explicit local cycle persistence.

## Expected BenefitFlow value

BenefitFlow already has the policy and governance layer for recursive enhancement, but currently relies primarily on protocol/control artifacts. A BenefitFlow-native executable helper could mechanically enforce read-only observation, local-only persistence, provenance, bounded recursion, and collision safety instead of depending only on agent compliance.

## Adaptation required

Do not copy framework semantics wholesale. A BenefitFlow implementation would need to:
- bind specifically to `project_id=benefitflow` and `boberino93-bit/benefitflow`;
- use `ENHANCEMENT_SOURCE_REGISTRY.json` and `ENHANCEMENT_CURSOR.json` as authoritative local controls;
- emit BenefitFlow candidate compatibility states and role-review fields;
- preserve current Manager -> Primary promotion rules;
- preserve the P0 gate and all human approval boundaries;
- integrate with all-role package parity and recovery verification;
- keep foreign repository operations strictly read-only.

## Validation requested

Manager review should determine whether this belongs as:
1. a BenefitFlow-local executable helper/tool plus tests;
2. a protocol-only pattern already sufficiently covered; or
3. a deferred candidate until more implementation surfaces exist.

If recommended for grafting, validation should include traversal rejection, same-project rejection, write-surface absence, candidate idempotency, collision failure, bounded recursion, cursor persistence ordering, project-scope enforcement, and package parity tests.

## Primary disposition

`DEFERRED_PENDING_MANAGER_REVIEW`.

No executable graft has been accepted yet.
