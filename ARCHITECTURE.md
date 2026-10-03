# BenefitFlow Beta Architecture

## Identity and isolation

Canonical identity is `BenefitFlow` with `project_id=benefitflow`. Project-specific communication, evidence, artifacts, control records, and recovery data live under `BenefitFlow-AgentBus/`. `boberino93-bit/duo-open` is a foreign repository and is denied as a BenefitFlow write target.

The dedicated repository is verified and bound as exactly `boberino93-bit/benefitflow`. The repository guard rejects every foreign repository target.

## Authority chain

`Human -> Primary -> Reviewer -> Specialist`

Specialists publish evidence/proposals only. Reviewer reconciles and promotes/rejects. Primary integrates accepted project truth. User approval remains mandatory before booking, financial action, or disclosure of member/plan identifiers outside the approved transaction scope.

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

The research swarm is prepared but not started. `BenefitFlow-AgentBus/control/RND_ROUND_GATE.json` remains the authoritative block until the user explicitly starts the BenefitFlow R&D round.
