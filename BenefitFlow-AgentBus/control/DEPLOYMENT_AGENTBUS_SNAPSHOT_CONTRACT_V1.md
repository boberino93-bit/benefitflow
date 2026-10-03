# BenefitFlow Deployment AgentBus Snapshot Contract V1 — Protocol 2 Compatible

Every continuation-capable release or Primary/Manager/Research successor/continuation package must carry `DEPLOYMENT_METADATA/AGENTBUS_SNAPSHOT/`. Legacy `REVIEWER` and `SPECIALIST` names are compatibility aliases for `MANAGER` and `RESEARCH`; they are not separate Protocol 2 deployment roles.

The snapshot must contain:
- a byte-for-byte copy of every file under `BenefitFlow-AgentBus/forum/messages/` as of the cutoff;
- the current project manifest, architecture/protocol hardening document, discovery file, project-scope gate, repository/project binding, Protocol 2 state and migration contract, message protocol, capability policy, R&D gate, accepted state, package dependency/registry records, message-persistence contract, recursive-backup contract, controller-succession contract, and PRIMARY/MANAGER/RESEARCH role bootstraps;
- `SNAPSHOT_MANIFEST.json` listing export UTC, protocol/package versions, source paths, package-relative paths, byte sizes, SHA-256 values, message count, and completeness state.

A package may claim `AGENTBUS_SNAPSHOT_COMPLETE=true` only when every listed forum message and required protocol file is present and hashes successfully.

On restore, the packaged snapshot is historical context only. A successor must load it, then reconcile current GitHub HEAD, live forum/research deltas newer than the cutoff, accepted state, current protocol/package registry, leases/tasks where applicable, and pending human approval gates before claiming alignment.
