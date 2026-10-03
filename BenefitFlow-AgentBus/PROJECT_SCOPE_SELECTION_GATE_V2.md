# BenefitFlow Project Scope Selection Gate V2

This gate is mandatory for every new Primary, Manager, Research, Reviewer, Specialist, worker, test, or temporary agent.

1. Resolve project identity from `PROJECT_MANIFEST.json` and `control/PROJECT_SCOPE_BINDING.json` before normal capabilities are enabled.
2. If the user's instruction explicitly names BenefitFlow, bind to `project_id=benefitflow` and repository `boberino93-bit/benefitflow` without asking redundantly.
3. If multiple projects could satisfy the instruction and no active project is explicit, ask the user which project is intended **before any mutation**.
4. UNBOUND agents may inspect only enough metadata to resolve project identity. They may not publish messages, write artifacts, modify tasks/state, acquire leases, create branches/commits, mutate repositories, deploy, replace packages, or cause external side effects.
5. Once bound, project identity is immutable for that execution instance. A child agent inherits its parent's `project_id`, repository binding, protocol version, package version, root agent, and task lineage.
6. Any conflicting project identity, foreign repository target, foreign AgentBus path, or foreign artifact/task reference fails closed.
7. Ordinary AgentBus traffic is BenefitFlow-internal only. Cross-project exchange must use the explicit bounded exchange protocol; it may never be smuggled through internal channels.
8. Semantic relevance is not authorization. Never infer that another repository or artifact is writable because it appears related.

Canonical identity: `benefitflow`
Canonical repository: `boberino93-bit/benefitflow`
Canonical AgentBus root: `BenefitFlow-AgentBus/`
