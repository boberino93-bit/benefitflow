# BenefitFlow Beta Architecture

## Identity and isolation

Canonical identity is `BenefitFlow` with `project_id=benefitflow`. Project-specific communication, evidence, artifacts, control records, and recovery data live under `BenefitFlow-AgentBus/`. `boberino93-bit/duo-open` and all other projects are foreign repositories and are denied as BenefitFlow write targets.

The dedicated repository is verified and bound as exactly `boberino93-bit/benefitflow`. The repository guard rejects every foreign repository target.

## Authority chain

`Human -> Primary -> Manager -> Research`

Research agents publish evidence/proposals only. Managers coordinate and reconcile only the research slots assigned to them by the authoritative roster. The Primary integrates accepted project truth, arbitrates cross-manager conflicts and lane collisions, maintains bootstrap/deployment synchronization, and preserves recovery integrity. User approval remains mandatory before booking, financial action, or disclosure of member/plan identifiers outside the approved transaction scope.

## Product workflow

`benefits input -> evidence-backed parsing -> normalized coverage rules -> budget/priorities -> optimizer -> provider research -> provider/direct-billing verification -> exact booking proposal -> user approval -> bounded transaction adapter`

## Recursive cross-project enhancement

BenefitFlow has a bounded recursive enhancement plane governed by `BenefitFlow-AgentBus/control/RECURSIVE_CROSS_PROJECT_ENHANCEMENT_V1.md`.

Registered foreign Artifactory/AgentBus/framework repositories may be inspected as **read-only reference sources** for reusable coordination, testing, recovery, package, protocol, and implementation patterns. Foreign state is never a writable shared bus and foreign accepted truth never automatically overrides BenefitFlow truth.

The enhancement path is:

`read-only source scan -> provenance-backed candidate -> compatibility classification -> Manager review -> Primary disposition -> BenefitFlow-local graft -> regression/invariant verification -> PRIMARY/MANAGER/RESEARCH package parity -> recursive recovery synchronization -> local cursor advancement`

Research agents scout and propose; Managers review compatibility and risk; Primary alone accepts foreign-derived project-truth grafts subject to human-reserved boundaries. The loop is serviced during active work at bounded lifecycle checkpoints and does not create background execution or allow dormant sessions to self-wake.

Authoritative enhancement state:
- `BenefitFlow-AgentBus/control/ENHANCEMENT_SOURCE_REGISTRY.json`
- `BenefitFlow-AgentBus/control/ENHANCEMENT_CURSOR.json`
- `BenefitFlow-AgentBus/artifactory/enhancement/`

## Recursive recovery

BenefitFlow recovery uses four coupled contracts:

1. **Message persistence:** material coordination is append-only and immutable.
2. **Deployment snapshot:** every continuation-capable package carries the complete forum plus required interpretation/control context, including the recursive enhancement protocol/registry/cursor, and a SHA-256 manifest.
3. **Controller succession:** a successor independently revalidates repository state, live forum deltas, accepted state, contradictions, outstanding research, enhancement state, recovery integrity, and human approval state before becoming ready.
4. **Recursive backup:** each successor/continuation package includes the contracts and metadata required to generate and validate the next continuation package.

This is recovery through persisted project truth and revalidation, not autonomous leader election.

## Research boundary

R&D Round 1 is active under `BenefitFlow-AgentBus/control/RND_ROUND_GATE.json`. Live ownership for the authorized 10 research agents and 2 managers is controlled by `BenefitFlow-AgentBus/control/SWARM_ROSTER.json`; behavioral requirements are in `BenefitFlow-AgentBus/control/SWARM_PROTOCOL_V1.md`; the ten-lane research taxonomy is defined by Manager-01's `SWARM_ASSIGNMENT_MATRIX_V1.md` and ratified by the Primary.

The P0 architecture gate remains active: recursive enhancement may improve BenefitFlow's design and controls but does not authorize real member data, live provider/insurer credentials, claims submission, or live booking adapters before the accepted hardening gates are implemented and verified.
