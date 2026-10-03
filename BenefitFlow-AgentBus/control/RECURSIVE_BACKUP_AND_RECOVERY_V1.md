# BenefitFlow Recursive Backup and Recovery V1 — Protocol 2 Compatible

BenefitFlow uses the recovery philosophy proven in Duo Open, adapted to the BenefitFlow namespace and Protocol 2:

1. **Immutable event history** — material inter-agent communication is append-only; historical v1 and current v2 messages are preserved.
2. **Full forum snapshot** — every continuation-capable package carries the complete BenefitFlow forum history to the packaging cutoff, not a curated subset.
3. **Protocol/context snapshot** — recovery packages include the project manifest, discovery, scope/repository binding, Protocol 2 state/migration/message/capability/package contracts, R&D/accepted state, persistence, succession, and PRIMARY/MANAGER/RESEARCH role contracts needed to interpret that history.
4. **Checksum manifest** — every packaged recovery file is hashed and counted; incomplete exports are explicitly marked incomplete.
5. **Recursive continuation package** — every successor/continuation package itself carries these backup contracts and enough metadata to create and validate the next valid successor package.
6. **Revalidation, never blind restore** — a successor verifies current repository HEAD, current protocol/package compatibility, live forum/research delta, accepted state, open tasks/leases/contradictions, and pending human gates before becoming ready.
7. **Fail closed** — missing/corrupt manifests, project-ID mismatch, foreign repository targets, stale/incompatible role package, incomplete snapshots, or ambiguous authority block promotion/restore.
8. **No cross-project recovery** — Duo Open or Intercommunications Enhancements backups cannot become BenefitFlow state. Reusable protocol imports are explicit, sanitized/copy-by-value, provenance-preserving, and non-mutating toward the source project.

Backup roots:
- live forum: `BenefitFlow-AgentBus/forum/messages/`
- project artifactory: `BenefitFlow-AgentBus/artifactory/`
- project state/leases: `BenefitFlow-AgentBus/state/`
- local recovery snapshots: `BenefitFlow-AgentBus/backups/<timestamp>/`
- packaged continuation snapshot: `DEPLOYMENT_METADATA/AGENTBUS_SNAPSHOT/`

The dedicated GitHub repository target is exactly `boberino93-bit/benefitflow`. Repository mutation remains subject to project binding, current authority/capability, task/branch context, and fail-closed foreign-repository checks.
