# BenefitFlow Beta v0.4.0-beta.1

BenefitFlow is a benefits-navigation and appointment-coordination beta designed to turn a user's extended-benefits package, priorities, and annual out-of-pocket budget into an evidence-backed utilization plan and a user-approved booking workflow.

## Product capabilities

- Evidence-backed benefit parsing and normalized coverage rules.
- Budget-aware utilization optimization with ambiguity routed to manual review.
- Provider/direct-billing verification before a booking proposal exists.
- Exact booking proposal followed by explicit user approval.
- Bounded transaction handoff rather than pretending a real call/booking occurred.
- Persistent beta workflow state using local SQLite.

## Protocol 2 multi-agent hardening

- Canonical project identity: `BenefitFlow` / `project_id=benefitflow`.
- Canonical repository: exactly `boberino93-bit/benefitflow`; foreign repositories are denied write targets.
- Agent lifecycle with an UNBOUND no-mutation state and immutable project binding.
- Child agents automatically inherit project/repository/protocol/package identity and receive fresh execution-instance IDs.
- Structured project-scoped message envelope with lineage, idempotency, TTL, artifact ownership and payload integrity.
- Fail-closed routing: foreign, ambiguous, malformed, expired, stale or protocol-incompatible operations do not silently execute.
- Atomic idempotency claims, expiring work leases, compare-and-set state mutation, immutable versioned artifacts, quarantine and acknowledgement records.
- Cross-project exchange is a distinct deny-by-default capability/approval boundary; ordinary AgentBus channels cannot cross projects.
- Synchronized PRIMARY/MANAGER/RESEARCH deployment ZIPs built and verified from an exact Git commit SHA.
- Recursive recovery remains enabled through immutable forum messages, checksummed AgentBus snapshots and successor revalidation.

See `PROJECT_MANIFEST.json`, `ARCHITECTURE.md`, and `PROTOCOL_HARDENING_V2.md`.

## Role authority

- **PRIMARY / ORCHESTRATOR** — project integration and release coherence.
- **MANAGER / REVIEWER** — coordination/review without silent authority escalation.
- **RESEARCH / SPECIALIST** — bounded evidence work only.

No role package grants `external_action`, `cross_project_exchange`, or `deploy` by default. Research/planning cannot bypass BenefitFlow's explicit user confirmation requirement for booking, financial action, claims submission, or full member/plan identifier disclosure.

## R&D gate

The BenefitFlow R&D round is **active by explicit user instruction**. Protocol 2 hardening preserves current in-flight work: existing v1 agents may finish already-claimed tasks, while newly launched agents must use the current Protocol 2 role package and inherited BenefitFlow binding.

## Run

```bash
python -m pip install -r requirements.txt
python run_beta.py
```

Open `http://127.0.0.1:8000`.

## Test and package

```bash
python -m pytest -q
python framework_reference/tests/run_all.py
python tools/build_agent_packages.py --source-revision <exact-git-sha>
python tools/verify_agent_packages.py --source-revision <exact-git-sha>
```

GitHub Actions performs the same sequence on the exact source revision and uploads the synchronized role release set.

## Recursive backup / successor recovery

```bash
python tools/build_recursive_backup.py
python tools/verify_recursive_backup.py <snapshot-folder>/DEPLOYMENT_METADATA/AGENTBUS_SNAPSHOT
python tools/generate_successor_package.py PRIMARY
```

See `BenefitFlow-AgentBus/control/RECURSIVE_BACKUP_AND_RECOVERY_V1.md` and related recovery contracts.

## Safety/product boundary

The beta does not itself place live calls, submit claims, charge money, or give clinical advice. Member/plan identifiers remain outside Research-agent context and may be disclosed externally only inside a separately approved transaction scope.
