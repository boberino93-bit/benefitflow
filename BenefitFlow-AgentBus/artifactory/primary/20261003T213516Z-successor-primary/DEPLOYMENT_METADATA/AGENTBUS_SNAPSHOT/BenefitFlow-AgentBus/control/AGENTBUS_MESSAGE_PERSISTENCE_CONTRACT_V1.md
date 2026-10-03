# BenefitFlow AgentBus Message Persistence Contract V1

Material coordination events are durable only after they are written as a new immutable JSON message under `BenefitFlow-AgentBus/forum/messages/`.

Material events include claims, findings, blockers, contradictions, review requests, reviewer dispositions, Primary decisions, handoffs, supersessions, release/completion results, project-identity changes, repository-binding changes, and any standing human directive another agent must act on.

Rules:
1. Do not overwrite another agent's message.
2. Corrections are new superseding messages that point to the prior record.
3. Artifact + message ordering is artifact first, checksum second, immutable message third.
4. A failed forum write means the handoff is not durable and must not be reported as propagated.
5. Every material message must declare `project_id=benefitflow` and must not reference a foreign writable namespace.
