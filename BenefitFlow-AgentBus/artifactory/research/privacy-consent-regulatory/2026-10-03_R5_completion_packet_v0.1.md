# R5 Completion Packet — Privacy, Consent, Data Minimization, Regulatory Applicability

**Project:** BenefitFlow (`project_id=benefitflow`)  
**Assignment:** R5  
**Researcher:** researcher-5e9c  
**Date retrieved:** 2026-10-03  
**Status:** READY_FOR_MANAGER_REVIEW  
**Companion baseline:** `2026-10-03_baseline_v0.1.md`

## 1. Material finding index

### R5-F01 — PIPEDA is the current federal production baseline; Bill C-36 is a horizon item
- **Observed evidence:** OPC continues to describe PIPEDA as the current federal private-sector privacy law. Parliament lists Bill C-36, Protecting Privacy and Consumer Data Act, introduced June 15, 2026, at second reading.
- **Source owner/type:** Office of the Privacy Commissioner of Canada (regulator); Parliament of Canada (official legislative status).
- **Sources:**
  - https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/pipeda_brief/
  - https://www.parl.ca/legisinfo/en/bill/45-1/c-36
- **Publication/update:** PIPEDA page current as retrieved; Bill C-36 introduced 2026-06-15.
- **Jurisdiction:** Canada/federal.
- **Applicability:** Covered private-sector commercial activity, subject to federal/provincial allocation.
- **Confidence:** High.
- **Known contradiction/limit:** Federal/provincial applicability is fact-specific; this does not determine which statute governs every BenefitFlow data flow.
- **Implementation consequence:** Version the compliance policy layer. Build against current PIPEDA obligations now; do not code Bill C-36 proposals as enacted law.
- **Classification:** Observed evidence + product recommendation.

### R5-F02 — Sensitive data needs meaningful, purpose-specific consent and minimized collection
- **Observed evidence:** OPC guidance requires meaningful consent and states that express consent should generally be used for sensitive information. PIPEDA also limits collection to what is needed for identified purposes.
- **Source owner/type:** OPC regulator guidance.
- **Source:** https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/p_principle/principles/p_consent/
- **Publication/update:** Current as retrieved 2026-10-03.
- **Jurisdiction:** Canada/federal.
- **Applicability:** Directly relevant to benefit, insurance, financial, appointment, and health-adjacent data.
- **Confidence:** High.
- **Known contradiction/limit:** Exact form of consent depends on context and governing statute.
- **Implementation consequence:** Separate `BookingApproval` from `ConsentGrant`/`DisclosureAuthorization`; bind authorization to exact purpose, recipient, fields, transaction, versioned notice, timestamp, expiry, and withdrawal.
- **Classification:** Observed evidence + implementation recommendation.

### R5-F03 — Third-party processors do not transfer accountability away from BenefitFlow
- **Observed evidence:** OPC states organizations remain accountable for personal information handled by third-party processors and should use contractual or other means to provide comparable protection. September 2026 OPC guidance calls for due diligence covering data flows, jurisdictions, subprocessors, controls, and contracts.
- **Source owner/type:** OPC regulator guidance.
- **Sources:**
  - https://www.priv.gc.ca/en/privacy-topics/privacy-for-businesses/appropriate-handling-of-personal-information/gd_third-party_202609/
  - https://www.priv.gc.ca/en/privacy-topics/airports-and-borders/gl_dab_090127/
- **Publication/update:** Third-party guidance published 2026-09-10 and open for comments until 2026-12-04.
- **Jurisdiction:** Canada/federal.
- **Applicability:** Cloud hosting, model providers, telephony, transcription, analytics, booking vendors, insurer/provider integrations.
- **Confidence:** High, with freshness caveat.
- **Known contradiction/limit:** The September 2026 guidance may be amended after consultation.
- **Implementation consequence:** Create processor/subprocessor registry, jurisdiction field, contract status, breach-notice terms, and periodic reassessment.
- **Classification:** Observed evidence + product recommendation.

### R5-F04 — Quebec requires additional cross-border controls
- **Observed evidence:** Quebec CAI states that before communicating or entrusting personal information outside Quebec, an enterprise must conduct a privacy impact assessment; the communication must be covered by a written agreement; the enterprise remains responsible for the information. CAI also emphasizes necessity and valid consent.
- **Source owner/type:** Commission d’accès à l’information du Québec (regulator).
- **Sources:**
  - https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-entreprises-privees/utilisation-communication-renseignements-personnels
  - https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-entreprises-privees/consentement-personnes-entreprises
- **Publication/update:** Current as retrieved 2026-10-03.
- **Jurisdiction:** Quebec.
- **Applicability:** Quebec users/data and any out-of-Quebec processor or hosting flow.
- **Confidence:** High for cited requirements; qualified for exact BenefitFlow application.
- **Known contradiction/limit:** Exact statutory allocation should be verified against BenefitFlow’s corporate presence and data flows.
- **Implementation consequence:** Add a Quebec cross-border PIA gate and written-agreement evidence requirement before activating an external processor.
- **Classification:** Observed evidence + implementation recommendation.

### R5-F05 — Ontario integration mode changes the PHIPA role analysis
- **Observed evidence:** Ontario PHIPA includes health information custodians, agents/service providers, and a consumer electronic service provider concept for electronic services requested by individuals to access/use/manage personal health information. Ontario IPC decisions emphasize that custodians remain responsible when third-party providers handle PHI.
- **Source owner/type:** Ontario statute/government; Ontario IPC regulator.
- **Sources:**
  - https://www.ontario.ca/laws/statute/04p03
  - https://www.ipc.on.ca/en/cases-of-note/custodians-must-ensure-phi-protected-even-when-using-third-party-providers
  - https://www.ipc.on.ca/en/health-individuals/consent-and-your-personal-health-information
- **Publication/update:** Statute current as retrieved; third-party case note 2025-07-21.
- **Jurisdiction:** Ontario.
- **Applicability:** Provider/custodian integrations or consumer PHI-management features.
- **Confidence:** High for role categories and safeguards; **requires qualified review** for BenefitFlow classification.
- **Known contradiction/limit:** Consumer-only and custodian-contracted deployments may fall into different legal roles.
- **Implementation consequence:** Treat `consumer_only`, `custodian_agent`, and `provider_integrated` as separate compliance modes until counsel resolves classification.
- **Classification:** Observed evidence + interpretation + qualified-review requirement.

### R5-F06 — Alberta provider contracts can change the HIA role
- **Observed evidence:** Alberta describes HIA “affiliates” as including people who perform services for a custodian under contract or agency relationships.
- **Source owner/type:** Government of Alberta official guidance.
- **Source:** https://www.alberta.ca/health-information-act
- **Publication/update:** Current as retrieved 2026-10-03.
- **Jurisdiction:** Alberta.
- **Applicability:** Direct integrations/services performed for Alberta health custodians.
- **Confidence:** High for definition/guidance; qualified for BenefitFlow classification.
- **Known contradiction/limit:** Not every consumer benefits-navigation use case makes BenefitFlow an HIA affiliate.
- **Implementation consequence:** Require legal/contract role classification before enabling provider-integrated Alberta workflows.
- **Classification:** Observed evidence + interpretation.

### R5-F07 — Current beta storage is not suitable for production secrets
- **Observed evidence:** `workflow.py` persists full `plan_number` and `member_id` inside a `sensitive` object; `storage.py` serializes values into a generic SQLite key/value table. The storage abstraction exposes no TTL, delete, access log, purpose binding, encryption adapter, or per-field authorization.
- **Source owner/type:** BenefitFlow repository (first-party code).
- **Sources:**
  - `benefitflow_beta/workflow.py`
  - `benefitflow_beta/storage.py`
  - `benefitflow_beta/models.py`
- **Publication/update:** Repository state reviewed 2026-10-03.
- **Jurisdiction:** Product architecture, not jurisdiction-specific.
- **Applicability:** Production use of real member/plan identifiers.
- **Confidence:** High.
- **Known contradiction/limit:** This is a synthetic beta; absence of production controls in beta does not imply the team intended them to be production-ready.
- **Implementation consequence:** Put raw identifiers behind a secure secret-store interface and retain only masked values/opaque references in workflow state.
- **Classification:** Observed code evidence + security/privacy recommendation.

## 2. Data classification and minimization recommendation

| Class | Examples | Default handling |
|---|---|---|
| Public/provider directory | clinic name, public phone, public booking URL | Cache with provenance/freshness metadata |
| User preference | desired service, budget, preferred time window | Store only as needed for active planning; user-editable |
| Benefit entitlement | coverage %, limits, deductible remaining, referral flags | Sensitive; purpose-bound; avoid unrelated reuse |
| Insurance identifiers | member/certificate ID, plan/group number | Restricted secret class; never research-agent context; disclose only transaction-scoped |
| Health-adjacent/PHI | referral/prescription details, treatment/diagnosis data if ever added | Highest sensitivity; collect only if product purpose genuinely requires it |
| Transaction evidence | consent grant, disclosure event, booking confirmation | Retain under explicit schedule; immutable audit linkage |
| Voice/transcript | call audio/transcript if later enabled | Separate consent + retention policy; redact secrets; no training by default |

## 3. Required consent/disclosure checkpoints

1. **Initial collection:** show identified purpose before collecting sensitive fields.
2. **Plan upload/normalization:** disclose what is extracted and retained.
3. **Provider research:** use sanitized need-to-know inputs; do not disclose member identifiers.
4. **Proposal approval:** user approves provider/service/price/window; this is workflow authorization.
5. **Disclosure authorization:** separately enumerate recipient, purpose, exact fields, and expiry before an adapter can retrieve full identifiers.
6. **Material change:** new recipient/service/price/field set requires reapproval and, where scope changes, a fresh disclosure grant.
7. **Secondary use:** analytics/model training requires an independently justified governance path; default is no.
8. **Withdrawal:** future use/disclosure stops subject to legal/contractual limits; retained evidence of prior authorized actions remains governed by retention policy.

## 4. Contradictions / unresolved unknowns

- No direct contradiction was found among the cited regulator/government sources.
- The principal uncertainty is **applicability**, not rule conflict: BenefitFlow’s legal role changes with province, corporate presence, whether it acts only for a consumer, and whether it contracts with insurers/providers/custodians.
- Bill C-36 creates a **future-law uncertainty**. It is not enacted and must not be treated as current law.
- Quebec and health-sector provincial regimes can impose additional requirements beyond a federal-only design.

**Product-safe fallback:** when role/jurisdiction cannot be resolved, block the sensitive integration path and route to legal/privacy review rather than infer permissive authority.

## 5. Recommended implementation/test consequences

### P0
- Consent/disclosure ledger independent of booking approval.
- Secure secret-store abstraction.
- Structured transaction policy enforcing recipient/fields/purpose/expiry.
- Data inventory/purpose registry and processor registry.
- Retention/delete/export/correction service.
- Privacy/security audit + breach event model.

### Tests
- Adapter cannot retrieve a full member ID without an active matching disclosure grant.
- Grant for Provider A cannot be replayed for Provider B.
- Grant expires and cannot be reused.
- Material price/service/recipient/field changes invalidate prior approval.
- Research-agent payload generation strips identifiers.
- Retention expiry removes secrets while preserving permitted audit metadata.
- Jurisdiction policy blocks Quebec cross-border processor activation when PIA/contract evidence is missing.
- Unknown compliance mode fails closed.

## 6. What this research does NOT establish

- It is not legal advice and does not determine the definitive statute governing BenefitFlow.
- It does not decide BenefitFlow’s corporate launch jurisdiction, controller/processor status, custodian/agent status, or insurer contractual role.
- It does not prescribe a particular encryption algorithm, cloud provider, or retention duration.
- It does not analyze U.S. HIPAA/state law, minors in depth, employment-benefit sponsor obligations, or call-recording law; those require separate scope.
- It does not authorize processing real member data in the research swarm.

## 7. Researcher recommendation

Manager should treat the architectural findings as `SUPPORTED_WITH_LIMITS` and route jurisdiction/role classifications to `REQUIRES_HUMAN_OR_QUALIFIED_REVIEW`.

The safest near-term product rule is: **BenefitFlow may continue synthetic R&D, but real member/plan identifiers should not enter the production workflow until the P0 privacy control plane exists and the launch jurisdiction/integration role has been qualified.**
