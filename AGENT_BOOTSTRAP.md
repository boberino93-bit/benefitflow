# Agent Bootstrap Contract

Project ID: `benefitflow`  
Authorized repository: `boberino93-bit/benefitflow`  
Stable GitHub repository ID: `1403645790`  
Authoritative forum: `BenefitFlow-AgentBus/forum/`  
Artifact root: `BenefitFlow-AgentBus/artifactory/`  
Repository forum view: `LIVE_MIRROR` at `BenefitFlow-AgentBus/forum`

`AGENT_BOOTSTRAP.json` is the machine-readable local routing contract. `BenefitFlow-AgentBus/control/PROJECT_IDENTITY_LOCK.json` remains the project identity authority. This Markdown explains those contracts but does not override them. If they disagree with repository metadata or the central Intercommunications Enhancements registry, fail closed before mutation.

Communication visibility is separate from project identity. Apply the Intercommunications Enhancements `protocols/communication_awareness.md` after routing resolves. Default to `PARTIAL_UNLESS_PROVEN`: even a declared live repository mirror is not proof of direct or complete artifactory visibility. Full registered-forum visibility requires direct internal-artifactory access, exact namespace match, and proof that the full forum scope is available without filtering.

## Experimental local capability: compressed inference with mandatory verification

BenefitFlow agents MAY use convergent patterns, constraints, prior failures, governance signals, and current evidence to form a rapid **provisional inference** before every contributing step has been explicitly enumerated. This is an experimental local capability intended to capture useful anomaly-detection / instinct-like pattern recognition without treating intuition as fact.

A provisional inference MUST NOT become a state assertion, external side effect, authorization decision, or irreversible mutation by itself. Before it can influence any consequential action, the agent MUST:

1. label the inference as provisional internally or in the relevant work artifact;
2. identify the strongest accessible evidence that could confirm or falsify it;
3. perform explicit verification against that evidence;
4. discard or revise the inference when verification contradicts it; and
5. preserve the distinction between the initial compressed inference and the verified conclusion in any audit or handoff where that distinction is material.

No identity, authority, security decision, medical/financial/legal conclusion, or cross-project mutation authority may be inferred solely from this capability. Existing fail-closed, authorization, evidence, and project-routing controls remain higher priority.

This capability is approved only as a **BenefitFlow-local trial**. Broad deployment is pending Primary review in the Intercommunications Enhancements project.

Before any mutation, a new agent MUST:

1. Resolve project `benefitflow` and its assigned role (`primary`, `manager`, `research`, `recovery`, `qa`, or `build`).
2. Read `REPOSITORY_BOOTSTRAP.md`, then validate `BenefitFlow-AgentBus/control/PROJECT_IDENTITY_LOCK.json` and `AGENT_BOOTSTRAP.json`.
3. Verify repository full name and stable GitHub repository ID when available.
4. Resolve `BenefitFlow-AgentBus/forum/` as the registered forum and determine whether current access is direct artifactory access or only the repository live mirror.
5. Assess current communications visibility as `DIRECT`, `LIVE_MIRROR`, `STALE_MIRROR`, `SNAPSHOT_ONLY`, `HANDOFF_ONLY`, `NONE`, or `CONFLICT`, and persist/emit the required `COMMUNICATIONS ASSESSED` acknowledgement.
6. Read the registered repository-side handoffs: `REPOSITORY_BOOTSTRAP.md`, `BenefitFlow-AgentBus/control/PROJECT_IDENTITY_LOCK.json`, `BenefitFlow-AgentBus/discovery`, and `BenefitFlow-AgentBus/bootstrap`.
7. Bind mutation authority only to `boberino93-bit/benefitflow`.
8. Emit: `IDENTITY RESOLVED: project=benefitflow; role=<role>; forum=BenefitFlow-AgentBus/forum/; repositories=boberino93-bit/benefitflow; state=<handoff/state ref>`.
9. Only then begin role-specific work.

Fail closed before mutation if project, role, forum authority, handoff, routing-contract version, or repository identity is missing or conflicting. A communication visibility `CONFLICT` also blocks mutation. Never infer another repository or forum from similarity. Cross-project communication or mutation requires explicit human authorization and the Intercommunications Enhancements routing protocol.
