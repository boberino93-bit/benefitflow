# Organization Agent Mesh — Start Here

This package is a generic, domain-neutral operating framework for multi-agent projects. It can begin from a short problem statement, make uncertainty explicit, establish authority and evidence rules, decompose work, coordinate parallel specialists, review contradictions, change accepted state under controlled authority, validate deliverables, and hand the project to successor agents.

## Five-minute start

1. Verify package integrity: `python tools/verify_package.py`.
2. Initialize: `python initializer/init_project.py --idea "We need to improve X" --output ./projects --name "X Improvement"`.
3. Open the generated `PROJECT_MANIFEST.json` and `OPEN_QUESTIONS.json`; fill only facts you actually know.
4. Configure authoritative sources, data rules, capabilities, human approval gates, validation methods, and the adapter that fits the project.
5. Each agent begins with `ORG_AGENT_MESH/discovery/AGENT_DISCOVERY.json`, follows the declared bootstrap order, claims a bounded lane, and publishes evidence/artifacts rather than asking the human to relay internal messages.
6. Specialists route candidate work to Reviewers. Reviewers may mark it `READY_FOR_INTEGRATION`, but only configured accepted-state authority may integrate it.
7. Before a phase/release, reconcile every lane, blocker, contradiction, dependency change, continuity impact, and deferred finding.
8. Generate a successor package with `python tools/generate_successor.py <project> <output>`.

## Core safety properties

Evidence outranks agent confidence. Accepted state has explicit authority. Records are append-only. Corrections supersede rather than erase. Messages point to canonical evidence. Parallelism does not erase accountability. Disagreement triggers evidence reconciliation, never voting. Liveness describes actual executing sessions, not imaginary background work. Learning may improve process but never privilege. Unknown facts stay unknown until supported.

## Package map

- `ARCHITECTURE.md` — control plane and lifecycle.
- `PROJECT_TEMPLATE.*` — domain-neutral project manifest.
- `AGENT_DISCOVERY_TEMPLATE.json` — entrypoint for newly instantiated agents.
- `protocols/` — governance, evidence, messaging, review, continuity, succession.
- `roles/` and `bootstrap/` — authority-tier behavior and startup sequence.
- `adapters/` — project-type defaults; adapters do not alter core authority.
- `schemas/` — machine-readable record contracts.
- `org_agent_mesh/` — executable reference implementation.
- `synthetic_examples/` — fictional immutable message examples.
- `reference_project/` — compact end-to-end fictional demonstration.
- `tests/` — deterministic acceptance tests.
