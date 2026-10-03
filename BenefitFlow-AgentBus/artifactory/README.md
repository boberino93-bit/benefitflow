# BenefitFlow Artifactory

Dedicated artifact namespace for BenefitFlow only.

- `primary/` — Primary integration artifacts
- `reviewer/` — review dispositions and reconciliations
- `research/` — specialist evidence outputs
- `releases/` — validated release packages and manifests

No Duo Open artifacts or mutable state belong here. Cross-project reusable material must arrive through an explicit sanitized import.
