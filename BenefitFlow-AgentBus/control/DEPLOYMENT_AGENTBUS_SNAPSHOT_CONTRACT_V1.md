# BenefitFlow Deployment AgentBus Snapshot Contract V1

Every continuation-capable release or PRIMARY, MANAGER, or RESEARCH initiation/successor package must carry `DEPLOYMENT_METADATA/AGENTBUS_SNAPSHOT/`. Legacy REVIEWER and SPECIALIST packages map to MANAGER and RESEARCH respectively.

**Project identity is an authorization boundary.** No packaged task, handoff, forum message, queue, accepted state, or recency signal becomes actionable until current human intent and the packaged/live BenefitFlow identity artifacts are revalidated.

The snapshot must contain:
- a byte-for-byte copy of every file under `BenefitFlow-AgentBus/forum/messages/` as of the cutoff;
- the project-scope gate, `control/PROJECT_IDENTITY_LOCK.json`, project-scope binding, repository binding, and discovery manifest;
- the current R&D gate, accepted state, swarm roster/protocol, forum envelope, message-persistence contract, recursive-backup contract, controller-succession contract, deployment contract, and Primary/Manager/Research role bootstraps;
- the current recursive enhancement protocol, source registry, and local enhancement cursor;
- `SNAPSHOT_MANIFEST.json` listing project ID, repository target, canonical branch, coordination namespace, identity mode, export UTC, source paths, package-relative paths, byte sizes, SHA-256 values, message count, current agent-spawn policy, identity-artifact hashes, enhancement inclusion state, foreign-source mode, and completeness state.

In addition to the historical snapshot, every generated role package must expose the current project-scope gate, project identity lock, project/repository bindings, and discovery manifest directly under `IDENTITY_CONTEXT/`. It must expose the current enhancement protocol, registry, and cursor directly under `ENHANCEMENT_CONTEXT/`.

The role-package manifest must identify at minimum:
- `project_id=benefitflow` and project name `BenefitFlow`;
- canonical repository `boberino93-bit/benefitflow` and branch `main`;
- coordination and artifact namespaces;
- exact Git source revision;
- role/package type;
- current human agent-spawn policy;
- identity mode `FAIL_CLOSED`;
- integrity hashes for every identity artifact.

A package may claim `AGENTBUS_SNAPSHOT_COMPLETE=true` only when every listed forum message and required protocol/control/identity file is present and hashes successfully.

A package must fail readback validation if identity files are absent, identity values disagree, another project's identifiers appear as local authority, scope/identity validation occurs after task or handoff loading, checksums fail, the declared source revision is unavailable/mismatched, or the current agent-spawn policy is missing.

A package must not claim recursive-enhancement readiness unless:
- `foreign_source_mode` is `READ_ONLY_FOREIGN_SOURCES`;
- foreign mutation is explicitly disabled;
- the package contains its role bootstrap plus identity and enhancement contexts;
- the role bootstrap requires BenefitFlow-only writes and role-appropriate enhancement authority;
- package source revision and integrity evidence can be established.

On restore, the packaged snapshot, handoffs, and enhancement cursor are historical context only. A successor must first resolve current human project intent, validate the BenefitFlow identity lock and bindings, and only then reconcile the live BenefitFlow forum/repository and registered foreign-source HEADs newer than the cutoff before claiming alignment. Reconciliation never writes to a foreign source.
