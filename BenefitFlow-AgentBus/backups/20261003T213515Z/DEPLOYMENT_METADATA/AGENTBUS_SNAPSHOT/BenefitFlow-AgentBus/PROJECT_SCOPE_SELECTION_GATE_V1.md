# BenefitFlow Project Scope Selection Gate V1

Status: MANDATORY / FAIL-CLOSED
Project ID: `benefitflow`

Every new agent/session must establish its intended project before project-specific work or any write.

- If the user's current instruction explicitly and unambiguously names BenefitFlow, bind to this project without asking a redundant question.
- If the project is ambiguous, ask the user which project the agent should work on.
- Never infer writable scope from an open repository, current working directory, inherited chat, previous agent task, or default path.
- There is no default writable repository.
- BenefitFlow GitHub writes are permitted only to the exact bound repository `boberino93-bit/benefitflow` and only within normal role/task authority.
- BenefitFlow coordination state may be written only under `BenefitFlow-AgentBus/`.
- Duo Open, Warp Propulsion Lab, and all other project repositories/forums/artifact stores are foreign and read-only unless an explicit cross-project transfer is authorized by the user.
- A cross-project transfer must name both source and destination and must not carry project-instance state that is irrelevant to the destination.

Failure behavior: ambiguity -> ask; metadata mismatch -> stop; repo mismatch -> stop; namespace mismatch -> stop.
