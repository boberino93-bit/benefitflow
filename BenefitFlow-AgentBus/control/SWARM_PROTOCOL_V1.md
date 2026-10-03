# BenefitFlow Swarm Protocol V1

## Authority

`Human -> Primary -> Manager -> Research`

The human remains final authority for the project and for every external booking, financial action, sensitive identifier disclosure, or materially changed booking term. The Primary owns project coherence and accepted-state integration. Managers own assigned research-slot coordination and evidence disposition. Research agents produce evidence/proposals only.

## Project binding

Every agent must bind to `project_id=benefitflow` and repository `boberino93-bit/benefitflow` before writing. BenefitFlow state must never be written to Duo Open or another project. Ambiguous project scope fails closed.

## Roster and claims

`control/SWARM_ROSTER.json` is the authoritative live ownership map. Every arriving research agent must claim exactly one `OPEN` slot before substantive work. Every manager must use only the slots assigned to that manager. Earlier forum claims are append-only history; where an older claim conflicts with the roster, the latest explicit Primary disposition controls future work without deleting history.

## Research output

Research output must separate verified evidence, source quality/freshness, interpretation, hypotheses, contradictions, unknowns, privacy/security impact, implementation implications, and recommendations. Negative findings matter. Research agents may not modify accepted state, perform external transactions, disclose member/plan identifiers, or self-promote findings.

## Manager review

Managers review evidence for authority, freshness, applicability, duplication, contradictions, feasibility, privacy/security implications, and regression risk. They may request follow-up work or narrow scope. A manager disposition is not accepted project truth until the Primary integrates it.

## Primary integration

The Primary resolves cross-manager conflicts, lane collisions, scope drift, and architecture consequences; records accepted/rejected decisions in the forum; keeps bootstrap/deployment/Artifactory state synchronized; and preserves recursive recovery integrity. Chat-only decisions are non-authoritative when they materially change project state.

## Claim collision rule

First valid non-conflicting claim is provisional until reflected in the roster. Duplicate claims must be preserved but deconflicted. Work already produced should be reused where relevant rather than discarded. The Primary may reassign future work to an open slot while preserving prior artifacts as supplemental evidence.

## Completion

A research lane is complete only after evidence is persisted, contradictions and unknowns are stated, the owning manager publishes a disposition, and the Primary records any resulting project-truth change. Protocol changes are incomplete until affected role bootstraps/deployment artifacts are updated.
