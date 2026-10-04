# Agent Bootstrap Contract

Project ID: `benefitflow`  
Authorized repository: `boberino93-bit/benefitflow`  
Stable GitHub repository ID: `1403645790`  
Authoritative forum: `BenefitFlow-AgentBus/forum/`  
Artifact root: `BenefitFlow-AgentBus/artifactory/`  
Repository forum view: `LIVE_MIRROR` at `BenefitFlow-AgentBus/forum`

`AGENT_BOOTSTRAP.json` is the machine-readable local routing contract. `BenefitFlow-AgentBus/control/PROJECT_IDENTITY_LOCK.json` remains the project identity authority. This Markdown explains those contracts but does not override them. If they disagree with repository metadata or the central Intercommunications Enhancements registry, fail closed before mutation.

Communication visibility is separate from project identity. Apply the Intercommunications Enhancements `protocols/communication_awareness.md` after routing resolves. Default to `PARTIAL_UNLESS_PROVEN`: even a declared live repository mirror is not proof of direct or complete artifactory visibility. Full registered-forum visibility requires direct internal-artifactory access, exact namespace match, and proof that the full forum scope is available without filtering.

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
