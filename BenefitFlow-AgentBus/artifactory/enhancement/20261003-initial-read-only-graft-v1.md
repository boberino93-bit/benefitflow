# BenefitFlow Recursive Enhancement — Initial Read-Only Graft V1

Date: 2026-10-03
Primary: `chatgpt-primary-2026-10-03`
Authority: explicit human directive to build recursive, read-only cross-project self-enhancement into PRIMARY, MANAGER, and RESEARCH packages.

## Source boundary

The following repositories were inspected as **read-only reference sources**:

1. `boberino93-bit/duo-open` at observed HEAD `43974424dc195de82c871418854defce487ee091`.
2. `boberino93-bit/intercommunicationsenhancements` at observed HEAD `707865e0125a16039ac8fb36dde6dcd5597fce6a`.

No data was deleted, renamed, rewritten, or otherwise mutated in either source repository.

## Seed graft BF-ENH-0001 — Active-service cursor discipline

Source:
- repository: `boberino93-bit/duo-open`
- path: `ACTIVE_AGENT_SERVICE_INTERVAL_V1.md`
- source SHA: `55349b04d2656442b3dae94982a5ec51462d50a7`
- observed repository HEAD: `43974424dc195de82c871418854defce487ee091`

Observed pattern:
- recurring service obligations apply only while an agent is actively executing;
- dormant sessions cannot self-wake;
- durable checkpoints/cursors are used to preserve continuity;
- cursors should advance only after durable state publication;
- re-entry requires revalidation rather than assuming alignment.

Compatibility: `ADAPT_REQUIRED`.

BenefitFlow graft:
- enhancement scanning is a recurring duty during active work, not a background-daemon claim;
- source cursor advances only after BenefitFlow-local persistence;
- bootstrap/re-entry and pre-handoff scans are explicit lifecycle triggers;
- bounded scan budgets prevent enhancement work from starving assigned project work.

Primary disposition: `ACCEPTED_AS_HUMAN_DIRECTED_BOOTSTRAP_GRAFT`.

## Seed graft BF-ENH-0002 — Cross-project provenance and compatibility

Source:
- repository: `boberino93-bit/intercommunicationsenhancements`
- path: `protocols/cross_project_exchange.md`
- source SHA: `22c1d1d006cb9ce073336466c229bee4b579ed06`
- observed repository HEAD: `707865e0125a16039ac8fb36dde6dcd5597fce6a`

Observed pattern:
- cross-project sharing is default-deny;
- source/destination identity, purpose, bounded use, explicit artifacts, and provenance matter;
- trust is non-transitive.

Compatibility: `ADAPT_REQUIRED`.

BenefitFlow graft:
- foreign repositories are read-only reference sources, not ordinary writable channels;
- every candidate retains source repository/path/ref/digest and compatibility state;
- foreign accepted truth never automatically overrides BenefitFlow truth;
- incompatible or sensitive patterns remain reference-only or are rejected.

Primary disposition: `ACCEPTED_AS_HUMAN_DIRECTED_BOOTSTRAP_GRAFT`.

## Seed graft BF-ENH-0003 — Role-package parity after protocol change

Source:
- repository: `boberino93-bit/intercommunicationsenhancements`
- path: `protocols/deployment_package_sync.md`
- source SHA: `f86a6ec19008e3dfad1bc53eee0f3d0a2901fe9e`
- observed repository HEAD: `707865e0125a16039ac8fb36dde6dcd5597fce6a`

Observed pattern:
- a control-plane/protocol change is incomplete while dependent PRIMARY, MANAGER, or RESEARCH deployment packages remain stale;
- manifests, package validation, and release coherence are Primary responsibilities.

Compatibility: `SAFE_REUSABLE` with BenefitFlow naming adaptation.

BenefitFlow graft:
- accepted enhancement changes that affect control semantics require all-role bootstrap/package synchronization;
- recursive recovery context must contain the enhancement protocol, registry, and cursor;
- enhancement completion includes package parity and recovery synchronization, not only a live-repo edit.

Primary disposition: `ACCEPTED_AS_HUMAN_DIRECTED_BOOTSTRAP_GRAFT`.

## Isolation reinforcement

A second Intercommunications Enhancements source, `protocols/project_isolation.md` (SHA `14ce2289cb86f9ef357244a3a04c6ea9ac1da0a4`), reinforces the BenefitFlow rule that project identity is an authorization boundary and project mismatch must fail closed. This is treated as corroborating evidence rather than a separate imported authority.

## Resulting BenefitFlow-local control surfaces

- `BenefitFlow-AgentBus/control/RECURSIVE_CROSS_PROJECT_ENHANCEMENT_V1.md`
- `BenefitFlow-AgentBus/control/ENHANCEMENT_SOURCE_REGISTRY.json`
- `BenefitFlow-AgentBus/control/ENHANCEMENT_CURSOR.json`
- `BenefitFlow-AgentBus/artifactory/enhancement/`

## Future candidate rule

These seed grafts establish the mechanism under explicit human authority. Future foreign-derived project-truth changes follow the normal pipeline:

`Research candidate -> Manager compatibility/review -> Primary disposition -> BenefitFlow-local graft -> verification -> all-role package/recovery sync -> cursor advancement`.

At no point does this pipeline mutate the foreign source repository.
