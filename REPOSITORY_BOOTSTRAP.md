# BenefitFlow Dedicated Repository Binding

Canonical repository: `boberino93-bit/benefitflow`

Status: **VERIFIED / BOUND**

BenefitFlow must never be committed into `boberino93-bit/duo-open` or another project as a substitute.

Binding invariants:
1. repository identity is exactly `boberino93-bit/benefitflow`;
2. `BenefitFlow-AgentBus/control/PROJECT_SCOPE_BINDING.json` must agree;
3. project isolation tests must pass;
4. every material binding/HEAD change is recorded as an immutable forum message;
5. successor packages must revalidate current HEAD before claiming alignment.
