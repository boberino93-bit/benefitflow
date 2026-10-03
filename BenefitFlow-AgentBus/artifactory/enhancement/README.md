# BenefitFlow Enhancement Artifactory

This namespace stores BenefitFlow-local evidence and dispositions produced by the recursive cross-project enhancement process.

Foreign repositories are reference-only. Nothing in this namespace authorizes mutation of a source repository.

Each enhancement candidate should preserve:
- candidate ID/fingerprint;
- source repository/path/ref/digest;
- observed pattern;
- compatibility classification;
- expected BenefitFlow value;
- affected local surfaces;
- safety/privacy/security impact;
- regression and rollback plan;
- Manager disposition;
- Primary disposition;
- local graft/package/recovery references if accepted.

Historical foreign material should normally be referenced by provenance rather than copied wholesale. Sensitive or project-private foreign material must not be imported.
