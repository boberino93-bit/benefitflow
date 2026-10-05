# Research Swarm Rollout Overlay — BenefitFlow

Status: ACTIVE PRE-FIRST-SCHEDULED-RUN
Project ID: `benefitflow`
Repository: `boberino93-bit/benefitflow`
Project forum authority: `BenefitFlow-AgentBus/forum/`
Canonical framework repository: `boberino93-bit/intercommunicationsenhancements`
Canonical framework revision: `db46c9ab0316f5ad1fab38ce6552387d01991842`

This overlay distributes the post-hardening recurring research-swarm launcher into BenefitFlow without copying the framework implementation into this repository. BenefitFlow keeps its project-local bootstrap, handoff, forum, ownership, review, and mutation authority. The central framework is consumed by exact revision as a shared protocol dependency; this overlay does not create a second control plane.

Before each scheduled role acts, it must load BenefitFlow's current local bootstrap/handoff/context and authoritative forum state, then read the applicable central role prompt and storage policy at the canonical revision above.

Canonical central paths include `protocols/primary_recurring_swarm_protocol.md`, `protocols/post_normalization_successor.md`, `research_swarm/five_task_schedule.json`, `research_swarm/STORAGE_HYGIENE_POLICY.md`, `research_swarm/storage_budget.json`, and `research_swarm/prompts/{master,manager,researcher_1,researcher_2,researcher_3}.md`.

## Storage operating boundary

The physical internal Artifactory/account quota is 20 GiB combined across registered projects. The swarm operating cap is 16 GiB combined, preserving 4 GiB / 20% headroom. BenefitFlow agents must avoid redundant artifacts, reuse canonical evidence, compact superseded working data, and perform safe hygiene work when storage pressure rises.

At or above 16 GiB measured combined usage, nonessential internal growth stops until cleanup reduces usage. If combined usage cannot be measured, report `STORAGE_USAGE_UNKNOWN`, minimize bulky writes, and do not perform unverified deletion.

Historical internal forum/cache/artifact material may be pruned only after exact-scope review, confirmation it is not active/current truth, verification of durable GitHub backup where retention is required, valid project-local destructive authority, and post-delete verification. Current handoff, claims/leases/fences, blockers, pending decisions, unresolved contradictions, operative approvals, and active evidence remain protected.

## Hourly behavior

Scheduled wake-ups are opportunities for useful work, not quotas for producing files. If no material research delta exists, do dedupe, compaction, backup verification, stale-cache cleanup, evidence indexing, checkpoint hygiene, or a compact `NO_MATERIAL_DELTA` update instead of filler.

The first scheduled invocation must occur only after this overlay is present on the default branch.
