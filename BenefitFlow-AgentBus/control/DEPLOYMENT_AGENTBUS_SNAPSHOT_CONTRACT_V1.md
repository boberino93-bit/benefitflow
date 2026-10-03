# BenefitFlow Deployment AgentBus Snapshot Contract V1

Every continuation-capable release or PRIMARY, MANAGER, or RESEARCH initiation/successor package must carry `DEPLOYMENT_METADATA/AGENTBUS_SNAPSHOT/`. Legacy REVIEWER and SPECIALIST packages map to MANAGER and RESEARCH respectively.

The snapshot must contain:
- a byte-for-byte copy of every file under `BenefitFlow-AgentBus/forum/messages/` as of the cutoff;
- the current discovery file, project-scope gate, repository binding, R&D gate, accepted state, swarm roster/protocol, forum envelope, message-persistence contract, recursive-backup contract, controller-succession contract, and role bootstraps;
- the current recursive enhancement protocol, source registry, and local enhancement cursor;
- `SNAPSHOT_MANIFEST.json` listing export UTC, source paths, package-relative paths, byte sizes, SHA-256 values, message count, cutoff timestamp, enhancement inclusion state, foreign-source mode, and completeness state.

In addition to the historical snapshot, every generated role package must expose the current enhancement protocol, registry, and cursor directly under its `ENHANCEMENT_CONTEXT/` directory so the role can validate the read-only foreign-source invariant before beginning enhancement work.

A package may claim `AGENTBUS_SNAPSHOT_COMPLETE=true` only when every listed forum message and required protocol/control file is present and hashes successfully.

A package must not claim recursive-enhancement readiness unless:
- `foreign_source_mode` is `READ_ONLY_FOREIGN_SOURCES`;
- foreign mutation is explicitly disabled;
- the package contains its role bootstrap plus enhancement protocol/registry/cursor;
- the role bootstrap requires BenefitFlow-only writes and role-appropriate enhancement authority;
- package source revision and integrity evidence can be established.

On restore, the packaged snapshot and enhancement cursor are historical context only. A successor must load them, then reconcile the live BenefitFlow forum/repository and registered foreign-source HEADs newer than the cutoff before claiming alignment. Reconciliation never writes to a foreign source.
