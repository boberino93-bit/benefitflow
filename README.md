# BenefitFlow Beta v0.3.0

BenefitFlow is a benefits-navigation and appointment-coordination beta designed to turn a user's extended-benefits package, priorities, and annual out-of-pocket budget into an evidence-backed utilization plan and a user-approved booking workflow.

## Beta capabilities

- Canonical project identity: `BenefitFlow` / `project_id=benefitflow`.
- Dedicated `BenefitFlow-AgentBus/` with its own immutable forum, evidence area, control state, artifactory, presence space, and recovery snapshots.
- Fail-closed project/repository guard. The dedicated repository is verified as `boberino93-bit/benefitflow`; all foreign repository writes remain blocked.
- Recursive recovery patterned on the proven Duo Open process: immutable messages, complete AgentBus snapshots, SHA-256 manifests, recursive continuation packages, successor revalidation, and live-delta reconciliation.
- Primary agent: `chatgpt-primary-2026-10-03`.
- R&D swarm gate remains `BLOCKED_PENDING_USER_START`; no research agents are launched by this package.
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

Current verified result: **34 BenefitFlow tests + 18 framework tests = 52 passing**.

## Recursive backup / successor recovery

```bash
python tools/build_recursive_backup.py
python tools/verify_recursive_backup.py <snapshot-folder>/DEPLOYMENT_METADATA/AGENTBUS_SNAPSHOT
python tools/generate_successor_package.py PRIMARY
```

See:
- `BenefitFlow-AgentBus/control/RECURSIVE_BACKUP_AND_RECOVERY_V1.md`
- `BenefitFlow-AgentBus/control/DEPLOYMENT_AGENTBUS_SNAPSHOT_CONTRACT_V1.md`
- `BenefitFlow-AgentBus/control/CONTROLLER_SUCCESSION_V1.md`
- `BenefitFlow-AgentBus/control/AGENTBUS_MESSAGE_PERSISTENCE_CONTRACT_V1.md`

## Safety/product boundary

This beta does not place live calls, book appointments, log into insurer portals, submit claims, charge money, or give clinical advice. Provider records and verification are synthetic.

The intended production sequence is:

`plan upload -> evidence-backed normalization -> user priorities/budget -> utilization plan -> provider research -> clinic verification -> exact approval card -> user approval -> transaction adapter -> confirmed booking -> calendar`

Member/plan identifiers remain outside research-agent context and may be disclosed externally only within the user's approved transaction scope.

## Project isolation

BenefitFlow coordination state lives only under `BenefitFlow-AgentBus/`. Duo Open is explicitly foreign. There is no implicit/default writable repository.

Repository activation is defined in `REPOSITORY_BOOTSTRAP.md` and `BenefitFlow-AgentBus/control/GITHUB_REPOSITORY_BINDING.json`.
