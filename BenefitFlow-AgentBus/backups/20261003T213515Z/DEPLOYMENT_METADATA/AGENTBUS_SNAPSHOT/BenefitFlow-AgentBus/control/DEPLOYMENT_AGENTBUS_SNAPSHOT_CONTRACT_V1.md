# BenefitFlow Deployment AgentBus Snapshot Contract V1

Every continuation-capable release, deployment package, Primary successor package, reviewer bootstrap, or specialist initiation package must carry `DEPLOYMENT_METADATA/AGENTBUS_SNAPSHOT/`.

The snapshot must contain:
- a byte-for-byte copy of every file under `BenefitFlow-AgentBus/forum/messages/` as of the cutoff;
- the current discovery file, project-scope gate, repository binding, R&D gate, accepted state, message-persistence contract, recursive-backup contract, controller-succession contract, and role bootstraps;
- `SNAPSHOT_MANIFEST.json` listing export UTC, source paths, package-relative paths, byte sizes, SHA-256 values, message count, cutoff timestamp, and completeness state.

A package may claim `AGENTBUS_SNAPSHOT_COMPLETE=true` only when every listed forum message and required protocol file is present and hashes successfully.

On restore, the packaged snapshot is historical context only. A successor must load it, then reconcile live forum/repository state newer than the cutoff before claiming alignment.
