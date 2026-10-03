# BenefitFlow Recursive Backup and Recovery V1

BenefitFlow recovery treats every takeover, hung/lost session, replacement, reassignment, successor activation, and cross-project context switch as a fresh authorization check over persisted evidence.

**RECENT CONTEXT IS NOT PROJECT AUTHORITY.** Recovery never inherits writable scope from the lost agent, the most recent chat/repository/handoff, the working directory, or the newest artifact.

Required recovery order:
1. resolve current human project intent with `../PROJECT_SCOPE_SELECTION_GATE_V1.md`;
2. validate `PROJECT_IDENTITY_LOCK.json` and require BenefitFlow's exact project ID, repository, coordination root, and `mode=FAIL_CLOSED`;
3. validate project and GitHub repository bindings against that lock;
4. only after those agree may BenefitFlow handoffs, forum history, queues, accepted state, roster, enhancement state, or prior-agent continuation material become actionable.

If intent is ambiguous or any identity value conflicts: **write nowhere and ask the human which project is intended**.

Recovery invariants:
1. **Immutable event history** — material inter-agent communication is append-only.
2. **Full forum snapshot** — every continuation-capable package carries the complete BenefitFlow forum history to the packaging cutoff, not a curated subset.
3. **Protocol/context snapshot** — recovery packages include discovery, scope gate, project identity lock, authority, R&D, accepted-state, persistence, succession, and role contracts needed to interpret that history.
4. **Checksum manifest** — every packaged recovery file is hashed and counted; identity artifacts have explicit integrity hashes; incomplete exports are explicitly marked incomplete.
5. **Recursive continuation package** — every successor/continuation package carries these backup contracts and enough metadata to create the next valid successor package.
6. **Revalidation, never blind restore** — a successor verifies current human project intent, identity lock, repository HEAD, live forum delta, accepted state, outstanding contradictions, current agent-spawn restrictions, and pending human gates before becoming ready.
7. **Fail closed** — missing/corrupt manifests, identity mismatch, project-ID mismatch, foreign repository targets, incomplete snapshots, ambiguous authority, or source-revision mismatch block promotion/restore.
8. **No cross-project recovery** — foreign-project backups cannot become BenefitFlow state. Reusable patterns may be generalized and locally reimplemented only under normal BenefitFlow review; foreign project-instance state grants zero authority.
9. **Cross-project writes denied** — permitted foreign inspection is read-only unless the human explicitly authorizes a transfer naming both source and destination.
10. **Package readback required** — generated Primary/Manager/Research continuation packages are incomplete until required identity files, bootstrap order, declared source revision, identity hashes, role bootstrap, and current spawn policy are read back and verified.

Backup roots:
- live forum: `BenefitFlow-AgentBus/forum/messages/`
- project artifactory: `BenefitFlow-AgentBus/artifactory/`
- local recovery snapshots: `BenefitFlow-AgentBus/backups/<timestamp>/`
- packaged continuation snapshot: `DEPLOYMENT_METADATA/AGENTBUS_SNAPSHOT/`

The dedicated writable repository target is `boberino93-bit/benefitflow` on canonical branch `main`. Normal role, human-approval, privacy/security, P0, single-writer, release, and no-new-agent restrictions remain unchanged by recovery.
