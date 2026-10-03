# BenefitFlow Beta v0.3.0

BenefitFlow is a benefits-navigation and appointment-coordination beta designed to turn a user's extended-benefits package, priorities, and annual out-of-pocket budget into an evidence-backed utilization plan and a user-approved booking workflow.

## Beta capabilities

- Canonical project identity: `BenefitFlow` / `project_id=benefitflow`.
- Dedicated `BenefitFlow-AgentBus/` with its own immutable forum, evidence area, control state, artifactory, presence space, and recovery snapshots.
- Fail-closed project/repository guard. The dedicated repository is verified as `boberino93-bit/benefitflow`; all foreign repository writes remain blocked.
- Recursive recovery patterned on the proven Duo Open process: immutable messages, complete AgentBus snapshots, SHA-256 manifests, recursive continuation packages, successor revalidation, and live-delta reconciliation.
- Bounded recursive self-enhancement: PRIMARY, MANAGER, and RESEARCH agents inspect registered foreign Artifactory/AgentBus repos as read-only reference sources, preserve provenance, review compatibility, and graft accepted improvements only into BenefitFlow.
- Active Primary: `chatgpt-primary-2026-10-03`.
- R&D Round 1 is active for **10 research agents + 2 manager agents**. Authoritative live ownership is `BenefitFlow-AgentBus/control/SWARM_ROSTER.json`.
- Rich benefit schema: annual/benefit-year/rolling-period limits, reasonable-and-customary caps, deductible remaining, prior usage, referral/prescription flags, visit limits, and evidence confidence.
- Optimizer accounts for eligible-charge caps, deductibles, used benefit value, visit limits, and user budget; ambiguous semantics fail to manual review.
- Provider verification is required before a booking proposal can be created.
- Booking approval emits a bounded transaction-adapter handoff rather than pretending a real call or booking occurred.
- Persistent beta workflow state uses local SQLite.

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

Previous verified baseline before the recursive-enhancement additions: **34 BenefitFlow tests + 18 framework tests = 52 passing**. The enhancement guard adds additional regression tests and should be revalidated with the full suite before a new baseline is published.

## Recursive enhancement

Authoritative controls:
- `BenefitFlow-AgentBus/control/RECURSIVE_CROSS_PROJECT_ENHANCEMENT_V1.md`
- `BenefitFlow-AgentBus/control/ENHANCEMENT_SOURCE_REGISTRY.json`
- `BenefitFlow-AgentBus/control/ENHANCEMENT_CURSOR.json`

Local helper:

```bash
python tools/recursive_enhancement_cycle.py next-source
python tools/recursive_enhancement_cycle.py validate-candidate <candidate.json>
```

Foreign source repositories are strictly read-only. The enhancement mechanism may inspect them, but it may not create, modify, delete, merge, branch, tag, comment, dispatch, or write cursor/ack state into them. Accepted grafts are BenefitFlow-local and remain subject to Manager review, Primary disposition, regression/invariant verification, and all-role package parity.

## Recursive backup / successor recovery

```bash
python tools/build_recursive_backup.py
python tools/verify_recursive_backup.py <snapshot-folder>/DEPLOYMENT_METADATA/AGENTBUS_SNAPSHOT
python tools/generate_successor_package.py PRIMARY
python tools/generate_successor_package.py MANAGER
python tools/generate_successor_package.py RESEARCH
# or refresh all roles
python tools/generate_all_role_packages.py
```

See:
- `BenefitFlow-AgentBus/control/RECURSIVE_BACKUP_AND_RECOVERY_V1.md`
- `BenefitFlow-AgentBus/control/DEPLOYMENT_AGENTBUS_SNAPSHOT_CONTRACT_V1.md`
- `BenefitFlow-AgentBus/control/CONTROLLER_SUCCESSION_V1.md`
- `BenefitFlow-AgentBus/control/AGENTBUS_MESSAGE_PERSISTENCE_CONTRACT_V1.md`
- `BenefitFlow-AgentBus/control/SWARM_PROTOCOL_V1.md`
- `BenefitFlow-AgentBus/control/RECURSIVE_CROSS_PROJECT_ENHANCEMENT_V1.md`

## Safety/product boundary

This beta does not place live calls, book appointments, log into insurer portals, submit claims, charge money, or give clinical advice. Provider records and verification are synthetic.

The intended production sequence is:

`plan upload -> evidence-backed normalization -> user priorities/budget -> utilization plan -> provider research -> clinic verification -> exact approval card -> user approval -> transaction adapter -> confirmed booking -> calendar`

Member/plan identifiers remain outside research-agent context and may be disclosed externally only within the user's approved transaction scope.

The accepted P0 architecture gate remains in force: recursive self-enhancement cannot silently authorize real member data, live credentials, claims submission, or live booking adapters before the required domain, authorization, sensitive-data, IAM/audit, evidence-provenance, and transaction-state hardening is implemented and verified.

## Project isolation

BenefitFlow coordination state lives only under `BenefitFlow-AgentBus/`. Duo Open and other enhancement-source repositories are explicitly foreign and read-only. There is no implicit/default writable repository.

Repository activation is defined in `REPOSITORY_BOOTSTRAP.md` and `BenefitFlow-AgentBus/control/GITHUB_REPOSITORY_BINDING.json`.
