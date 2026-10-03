# BenefitFlow Beta Architecture

## Identity and isolation

Canonical identity is `BenefitFlow` with `project_id=benefitflow`. Project-specific communication, evidence, artifacts, control records, and recovery data live under `BenefitFlow-AgentBus/`. `boberino93-bit/duo-open` is a foreign repository and is denied as a BenefitFlow write target.

The dedicated repository is verified and bound as exactly `boberino93-bit/benefitflow`. The repository guard rejects every foreign repository target.

## Authority chain

`Human -> Primary -> Manager -> Research`

Research agents publish evidence/proposals only. Managers coordinate and reconcile only the research slots assigned to them by the authoritative roster. The Primary integrates accepted project truth, arbitrates cross-manager conflicts and lane collisions, maintains bootstrap/deployment synchronization, and preserves recovery integrity. User approval remains mandatory before booking, financial action, or disclosure of member/plan identifiers outside the approved transaction scope.

## Product workflow

`benefits input -> evidence-backed parsing -> normalized coverage rules -> budget/priorities -> optimizer -> provider research -> provider/direct-billing verification -> exact booking proposal -> user approval -> bounded transaction adapter`

## Recursive recovery

BenefitFlow recovery uses four coupled contracts:

1. **Message persistence:** material coordination is append-only and immutable.
2. **Deployment snapshot:** every continuation-capable package carries the complete forum plus required interpretation/control context and a SHA-256 manifest.
3. **Controller succession:** a successor independently revalidates repository state, live forum deltas, accepted state, contradictions, outstanding research, recovery integrity, and human approval state before becoming ready.
4. **Recursive backup:** each successor/continuation package includes the contracts and metadata required to generate and validate the next continuation package.

This is recovery through persisted project truth and revalidation, not autonomous leader election.

## Research boundary

R&D Round 1 is active under `BenefitFlow-AgentBus/control/RND_ROUND_GATE.json`. Live ownership for the authorized 10 research agents and 2 managers is controlled by `BenefitFlow-AgentBus/control/SWARM_ROSTER.json`; behavioral requirements are in `BenefitFlow-AgentBus/control/SWARM_PROTOCOL_V1.md`; the ten-lane research taxonomy is defined by Manager-01's `SWARM_ASSIGNMENT_MATRIX_V1.md` and ratified by the Primary.
