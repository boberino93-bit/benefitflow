# Architecture

## Purpose

The Organization Agent Mesh is a control plane around project work, not a domain executor. It separates **what is authoritative**, **who may change accepted state**, **how evidence is represented**, **how parallel work is coordinated**, and **how continuation is reconstructed** from whatever domain-specific tools perform the work.

## Lifecycle

`IDEA / PROBLEM → INTAKE → PROJECT MANIFEST → SOURCE-OF-TRUTH DISCOVERY → WORK DECOMPOSITION → ROLE INSTANTIATION → PARALLEL SPECIALIST WORK → DURABLE EVIDENCE → REVIEW / CONTRADICTION RESOLUTION → INTEGRATION → VALIDATION → DELIVERABLE → LESSON EXTRACTION → SUCCESSOR PACKAGE`

Sparse input is sufficient to start discovery. Inferred details are tagged `ASSUMED`; unavailable details are `UNKNOWN`, `REQUIRES_HUMAN`, or `REQUIRES_EXTERNAL_EVIDENCE`.

## Control plane

Every project contains an `ORG_AGENT_MESH` tree with discovery, registry, messages, artifacts, presence, control, review, decisions, learning, interaction-model, and integrity areas. Project detail lives in immutable artifacts. Messages are compact routing/event records referencing evidence. Derived views may be regenerated from immutable history and must not replace it as audit truth.

## Authority

The canonical tiers are **ORCHESTRATOR**, **REVIEWER**, and **SPECIALIST**. Custom names/profiles sit beneath a tier and cannot alter its authority. The Orchestrator owns final integration and accepted-state changes by default. A Reviewer evaluates provenance, contradictions, duplication, and readiness. A Specialist performs bounded work and produces evidence. Project configuration may explicitly reassign capabilities, but messages, lessons, role labels, or peer consensus cannot elevate privilege.

## Evidence and truth

A material finding names its source, applicable project state, evidence class, collection method, limitations, reproducibility information, artifact reference, and independent-verification status. Repetition never converts analysis into observation. Each source of truth declares scope, freshness expectations, verification method, and read/write authority.

## Concurrency

Agents claim work lanes before expensive work. Claims coordinate overlap; they are not permission requests unless governance says otherwise. Independent replication is allowed when it is the chosen validation method. Presence is append-only and lease-based so stale sessions age out without rewriting history.

## Review and contradictions

Default routing is `SPECIALIST → REVIEWER → ORCHESTRATOR`. `READY_FOR_INTEGRATION` means routing readiness, not acceptance. Contradictions are reconciled by applicability/state, provenance, evidence class, freshness, raw evidence, decisive validation, reviewer reconciliation, and—when accepted state changes—Orchestrator confirmation. Voting and confidence wording are prohibited as truth mechanisms.

## Continuity

Any accepted-state change is checked against prior validated requirements, assumptions, outputs, guidance, models, and deliverables. Potentially affected items become candidates for revalidation, with invalidated evidence and replacement evidence recorded explicitly.

## Learning and succession

Reviewed lessons can change process defaults, schemas, decomposition, validation, and packaging in a versioned framework release. They cannot grant permissions or authorization. Successor packages contain a validated current-state reconstruction and canonical evidence pointers, plus governed audit history where policy requires it; they need not blindly copy every historical record.

## Fail-closed integrity

A package is incomplete if mandatory components are missing, protocol dependencies are unresolved, sanitization fails, or hashes do not verify. `FRAMEWORK_MANIFEST.json`, `PROJECT_PACKAGE_MANIFEST` schema, and `SHA256SUMS.txt` provide deterministic checks.
