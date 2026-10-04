# BenefitFlow Alpha v0.4.1

BenefitFlow is an evidence-backed benefits-navigation and appointment-coordination proof of concept. The synthetic product flow remains evidence-backed normalization through scoped approval and a simulated transaction lifecycle; only `CONFIRMED_BOOKED` counts as a confirmed appointment, and ambiguous outcomes require reconciliation rather than blind retry.

## Multi-project coordination hardening

BenefitFlow project protocol is `3.1.0`. Canonical identity is `project_id=benefitflow`, repository `boberino93-bit/benefitflow`, stable repository ID `1403645790`; `project_id` is an authorization boundary.

Protocol 3.1 enforces agent lifecycle binding, inherited child project identity, task/artifact project ownership in executable messages, project-qualified routing, instance-scoped leases, stale-write protection, stable repository-ID checks, project-local pause/read-only controls, and an explicit human-approved copy-by-value cross-project bridge. The root communication-awareness routing contract is also packaged and validated so role bundles do not lag behind bootstrap policy.

The executable envelope contract is `BenefitFlow-AgentBus/control/MESSAGE_ENVELOPE_SCHEMA.json`; runtime enforcement is in `benefitflow_beta/coordination.py` and `benefitflow_beta/project_guard.py`. PRIMARY, MANAGER, and RESEARCH are a coordinated release set; CI builds all three from one source revision and validates embedded hashes/metadata before publishing ZIP artifacts.

## Run and test

```bash
python -m pip install -r requirements.txt
python run_beta.py
python -m pytest -q
python framework_reference/tests/run_all.py
python tools/verify_role_package_enhancement_sync.py
```

R&D Round 1 is closed; current phase is P0 hardening/implementation. GitHub/AgentBus is authoritative; Slack is secondary operational visibility. Registered foreign enhancement sources are read-only.

Alpha 0.4.x does not place live calls, create real appointments, log into insurer/provider accounts, use live credentials, submit claims, charge money, disclose real member/plan identifiers, or provide clinical advice. The accepted P0 architecture gate remains active.
