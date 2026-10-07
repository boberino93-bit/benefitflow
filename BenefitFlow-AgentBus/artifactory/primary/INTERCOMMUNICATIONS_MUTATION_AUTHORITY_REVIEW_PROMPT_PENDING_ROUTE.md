# Pending Outbound Proposal — Intercommunications Mutation Authority Review

Status: **NON-BINDING / BENEFITFLOW-LOCAL STORAGE ONLY / DESTINATION REVIEW REQUIRED**  
Origin project: `benefitflow`  
Intended destination project: `intercommunicationsenhancements`  
Intended reviewer: first appropriately authorized `PRIMARY`, otherwise `MANAGER` for independent review  
Authority conveyed to destination: **NONE**

This prompt is stored in BenefitFlow only. It must not be treated as an Intercommunications Enhancements task, decision, or authorization merely because it exists here.

---

You are the first appropriately authorized PRIMARY or MANAGER reviewing this proposal inside the `intercommunicationsenhancements` project.

This is a REVIEW ASSIGNMENT proposal, not deployment authority. Apply your own project's authority, identity, mutation, and review gates before persisting or deploying anything.

## Originating incident

On 2026-10-07, BenefitFlow exposed a distinction that should be analyzed for possible generalization:

1. Task intent alone must not automatically become mutation authority.
2. A current explicit human directive, combined with an agent correctly bound to the same project, may be sufficient authority for bounded project-local mutations when that project's governance defines it that way.
3. Project-local authority must not automatically propagate into another project, the communication framework, swarm-global policy, or protected external transactions.
4. The enforcement boundary must live in executable mutation paths, not policy prose alone.

BenefitFlow implemented a local model:

`CURRENT HUMAN BENEFITFLOW DIRECTIVE + PROJECT-BOUND AGENT + CORRECT LOCAL TARGET -> BOUNDED BENEFITFLOW-LOCAL MUTATION`

while denying:

`LOCAL AUTHORITY -> CROSS-PROJECT / INTERCOMMUNICATIONS / SWARM-GLOBAL / PROTECTED EXTERNAL ACTION`

## Required forensic analysis

Perform an end-to-end causal review of how intent, project binding, human authorization, role authority, connector capability, repository mutation, CI/scheduler side effects, and audit controls interact across the framework.

Distinguish clearly between:

- human task assignment;
- project-local mutation authorization;
- role authority;
- repository/tool capability;
- cross-project authority;
- universal/swarm governance authority;
- protected transactional/external-action approval.

Do not assume they should all use the same authorization mechanism.

## Core question

Should the framework adopt an explicit two-level model in which:

### Project-local mutations
A current explicit human directive plus correct project binding may authorize a coherent bounded set of local source/configuration/test/documentation/coordination changes, subject to local role and safety gates.

### Cross-project / universal / protected actions
Separate stronger authority remains required for cross-project mutation, framework-wide governance, root authority, credential/security boundaries, production promotion, financial effects, destructive operations, and protected external transactions.

Attempt to falsify this model. Evaluate whether it reduces accidental mutation while avoiding unnecessary approval friction that would make autonomous project execution impractical.

## Enforcement architecture to assess

Review whether every mutation-capable path should consume an explicit structured authority object containing at minimum:

- project identity;
- authority source;
- bounded scope;
- target repository/namespace;
- role capability;
- consequence class;
- optional expected revision / state version;
- prohibited scope expansions.

The mutation path should fail closed when the target or consequence exceeds that authority object.

Consider a flow equivalent to:

`READ/PLAN -> RESOLVE CURRENT HUMAN DIRECTIVE -> BIND PROJECT/ROLE -> CLASSIFY MUTATION SCOPE -> BUILD BOUNDED AUTHORITY -> REVALIDATE TARGET/REVISION -> EXECUTE -> VERIFY -> AUDIT`

For cross-project or universal actions, insert the stronger destination/root authorization mechanism required by the governing project.

## Adversarial test matrix

Test at minimum:

- intent without explicit authorization;
- explicit local authorization with correct project binding;
- correct repository but absent human authority;
- local authority reused for a foreign repository;
- local authority reused for Intercommunications Enhancements;
- local authority reused for swarm-global governance;
- local authority reused for a protected transaction;
- role escalation attempts;
- stale project context;
- HEAD/state drift after authority binding;
- widened scope after approval;
- concurrent writes;
- scheduler/child-agent inheritance;
- recovery/rollback behavior;
- connector direct-call bypass.

Tests must demonstrate whether the durable side effect can actually be prevented, not merely whether policy text contains the right words.

## BenefitFlow evidence to examine

Review the local implementation and incident artifact, including:

- `BenefitFlow-AgentBus/control/PROJECT_MUTATION_AUTHORITY_V1.json`
- `benefitflow_beta/project_guard.py`
- `tests/test_project_isolation.py`
- `tests/test_mutation_authority_contract.py`
- `AGENT_BOOTSTRAP.md`
- `AGENT_BOOTSTRAP.json`
- `REPOSITORY_BOOTSTRAP.md`
- `AUTHORITY_SECURITY_OVERLAY.json`
- `BenefitFlow-AgentBus/bootstrap/PRIMARY.md`
- `BenefitFlow-AgentBus/bootstrap/MANAGER.md`
- `BenefitFlow-AgentBus/bootstrap/RESEARCH.md`
- `BenefitFlow-AgentBus/artifactory/primary/20261007_MUTATION_AUTHORITY_FORENSIC_HARDENING_V1.md`

Treat BenefitFlow as evidence, not as automatic framework truth.

## Deliverable

Produce:

- forensic causal graph;
- distinction between intent, local authority, cross-project authority, and universal authority;
- control-gap matrix;
- adversarial test results;
- proposed canonical authority schema if warranted;
- connector-interposition recommendation;
- migration/compatibility plan;
- rollback plan;
- residual-risk statement;
- explicit PRIMARY/MANAGER disposition.

If you are MANAGER, review and recommend; do not self-promote universal governance.

If you are PRIMARY, integrate only under the Intercommunications Enhancements project's own human/governance gates.

No BenefitFlow artifact, confidence score, role seniority, or cross-project relevance grants mutation authority in the destination project.
