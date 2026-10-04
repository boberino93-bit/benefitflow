# BenefitFlow Alpha v0.4.2

BenefitFlow is an evidence-backed benefits-navigation and appointment-coordination proof of concept. The synthetic product flow remains evidence-backed normalization through scoped approval and a simulated transaction lifecycle; only `CONFIRMED_BOOKED` counts as a confirmed appointment, and ambiguous outcomes require reconciliation rather than blind retry.

## Multi-project coordination hardening

BenefitFlow project protocol is `3.1.0`. Canonical identity is `project_id=benefitflow`, repository `boberino93-bit/benefitflow`, stable repository ID `1403645790`; `project_id` is an authorization boundary.

Protocol 3.1 enforces agent lifecycle binding, inherited child project identity, task/artifact project ownership in executable messages, project-qualified routing, stable repository-ID checks, project-local pause/read-only controls, and an explicit human-approved copy-by-value cross-project bridge.

Alpha 0.4.2 adds durable multi-process coordination in `benefitflow_beta/durable_store.py` + `benefitflow_beta/durable_coordination.py`. Shared mutable coordination now has a SQLite/WAL transactional implementation with durable idempotency, instance-owned expiring leases, compare-and-set state, durable project control, an append-only SHA-256 audit chain, append-only outbox events, and append-only delivery receipts. Process-local primitives remain useful for isolated tests but are not the authority for coordinated multi-process work.

`python tools/prove_multi_project_isolation.py` deliberately runs eight simultaneous BenefitFlow workers plus a disposable Project-C fixture using colliding human-readable identifiers in the same physical database. The release gate verifies one effective BenefitFlow mutation, safe replay, crash/TTL lease recovery, independent project pause behavior, restart durability, and audit/outbox integrity.

The executable envelope contract is `BenefitFlow-AgentBus/control/MESSAGE_ENVELOPE_SCHEMA.json`; durable semantics are defined in `BenefitFlow-AgentBus/control/DURABLE_COORDINATION_V1.md`. The root communication-awareness and new-project factory contracts are also packaged and validated so role bundles do not lag behind bootstrap policy.

## Run and test

```bash
python -m pip install -r requirements.txt
python run_beta.py
python -m pytest -q
python tools/prove_multi_project_isolation.py
python framework_reference/tests/run_all.py
python tools/verify_role_package_enhancement_sync.py
```

PRIMARY, MANAGER, and RESEARCH are a coordinated release set; CI builds all three from one exact source revision and validates embedded hashes/metadata before publishing ZIP artifacts.

R&D Round 1 is closed; current phase is P0 hardening/implementation. GitHub/AgentBus is authoritative; Slack is secondary operational visibility. Registered foreign enhancement sources are read-only.

The CI package workflow uses `contents: read`. Interactive/runtime write credentials must remain repository-scoped or equivalently least-privileged and still pass BenefitFlow's name + stable-repository-ID guard. Server-side GitHub App installation scope and branch-protection settings are account controls, not something BenefitFlow code can silently broaden.

Alpha 0.4.x does not place live calls, create real appointments, log into insurer/provider accounts, use live credentials, submit claims, charge money, disclose real member/plan identifiers, or provide clinical advice. The accepted P0 architecture gate remains active.
