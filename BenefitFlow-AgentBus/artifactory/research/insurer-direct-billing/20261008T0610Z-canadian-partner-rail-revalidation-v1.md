# BenefitFlow Follow-on Research — Canadian Partner-Rail Revalidation v1

**Role:** RESEARCH  
**Project:** `benefitflow`  
**Repository:** `boberino93-bit/benefitflow`  
**Repository revision reviewed before publication:** `8b49490eb12a60434ad3ce6407fa0fb45dd2ff7d`  
**Timestamp:** 2026-10-08T06:10:00Z  
**Status:** RESEARCH EVIDENCE / PROPOSAL ONLY — NOT ACCEPTED PROJECT TRUTH  
**Scope:** Read-only public-source revalidation of Canadian sanctioned direct-billing and provider-rail integration paths. No live credentials, member data, claims, bookings, provider actions, or financial actions were used.

## 1. Research question

Which currently evidenced Canadian provider/direct-billing rails are credible targets for a BenefitFlow pilot, and what does the evidence imply about the correct integration boundary?

## 2. Current evidence

### E1 — TELUS Health eClaims remains the strongest multi-insurer aggregation rail
**Source:** TELUS Health eClaims  
**URL:** https://go.telushealth.com/hubfs/eclaims/register/index.html  
**Reviewed:** 2026-10-08 UTC  
**Source quality:** First-party commercial/operational source

Observed facts:
- TELUS states that eClaims is used by more than 100,000 healthcare professionals.
- TELUS states that the service covers major Canadian insurers and lists participating carriers including Canada Life, ClaimSecure, Desjardins, Manulife, iA, GroupHEALTH, GroupSource, Simply Benefits, TELUS AdjudiCare and others.
- TELUS explicitly supports eClaims inside practice-management software and lists integrated vendors including Jane, Clinicmaster, Innocare, Practice Perfect, Noterro, Juvonno, Owl Practice, Embodia and others.
- The public material describes a provider-facing browser/PMS workflow; it does not establish a general public consumer API available to BenefitFlow.

Interpretation:
TELUS is the highest-leverage partnership target because one sanctioned integration could reach multiple insurers. The evidence still supports a **provider/PMS-authorized integration model**, not BenefitFlow acting as the member-side claims principal.

### E2 — Pacific Blue Cross is the clearest bounded insurer-specific API pilot candidate
**Source:** Pacific Blue Cross Provider Resources / PROVIDERnet  
**URLs:**  
- https://www.pac.bluecross.ca/providerresource/  
- https://www.pac.bluecross.ca/providerresource/how-tos/how-to-sign-up-for-providernet/  
- https://www.pac.bluecross.ca/providerresource/how-tos/providernet-quick-start-guide/  
**Reviewed:** 2026-10-08 UTC  
**Source quality:** First-party insurer/provider-network source

Observed facts:
- Pacific Blue Cross publicly lists **API Integration** under healthcare and vision provider resources.
- Existing PROVIDERnet users are instructed to contact `provider@pac.bluecross.ca` for API integration questions.
- PROVIDERnet requires provider/practice registration and direct-deposit setup before normal direct-billing operation.
- Current provider materials identify eligible practitioner classes and require relevant BC regulatory/licensing information.
- The Quick Start Guide describes an eligibility workflow in which a provider may submit a claim and then reverse it.

Interpretation:
PBC remains the best **bounded first technical discovery target** because a real API integration path is publicly acknowledged. However, public evidence still does not disclose the API specification, authentication model, sandbox availability, vendor eligibility, certification requirements, transaction scopes, or commercial terms.

Critical architectural consequence:
BenefitFlow must not normalize `eligibility_check` as a universal harmless read. On some rails, the evidenced workflow may involve claim submission + reversal, which is a materially different transaction and should not be automated as a background coverage probe without explicit rail-specific authorization.

### E3 — Sun Life Connect confirms provider-owned direct billing but not an open machine interface
**Source:** Sun Life Provider Hub / Sun Life Connect eClaims  
**URLs:**  
- https://www.sunlife.ca/sl/provider/en/paramedical/eclaims/  
- https://www.sunlife.ca/sl/provider/en/support/faqs/eclaims/  
- https://www.sunlife.ca/sl/provider/en/  
**Reviewed:** 2026-10-08 UTC  
**Source quality:** First-party insurer source

Observed facts:
- Sun Life eClaims lets eligible providers direct bill on behalf of patients.
- Sun Life requires provider/practice registration and validation; setup includes business/ownership and banking information.
- Sun Life currently lists a broad set of eligible paramedical specialties.
- Sun Life states that eClaims can pay providers quickly and supports provider claims-history access.
- No public developer/API interface for BenefitFlow was established by the reviewed material.

Interpretation:
Sun Life is a meaningful rail for manual/provider-mediated handoff and a potential partnership target, but current public evidence is insufficient to classify it as a machine-integrable BenefitFlow adapter.

### E4 — Canada Life continues to route substantial provider workflows through TELUS and standards-based dental rails
**Source:** Canada Life provider resources  
**URLs:**  
- https://www.canadalife.com/resources/provider.html  
- https://www.welcome.canadalife.com/psdcp-pdsp-provider/how-tos.html  
**Reviewed:** 2026-10-08 UTC  
**Source quality:** First-party insurer source

Observed facts:
- Canada Life directs eligible health providers toward TELUS Health eClaims/direct-deposit registration.
- Canada Life dental-provider material supports CDAnet transactions through practice-management software and identifies TELUS Group B configuration for relevant flows.
- Claims, reversals, predeterminations, acknowledgements/EOBs and selected attachments are represented as explicit transaction types in the dental rail.

Interpretation:
This reinforces the architecture that BenefitFlow should integrate with **sanctioned provider rails or PMS/standards channels**, rather than attempt member-portal automation.

## 3. Revalidated conclusions

1. **Provider/clinic identity remains the dominant transaction principal.** Every strong production path reviewed is provider-, clinic-, PMS-, or network-oriented.
2. **TELUS eClaims is the strongest aggregation target.** It has the broadest evidenced insurer and PMS reach.
3. **Pacific Blue Cross is the clearest first bounded API-discovery target.** It publicly acknowledges API integrations for registered providers.
4. **Sun Life is provider-mediated, but machine access remains unproven from public evidence.**
5. **Canada Life strengthens the case for rail-specific adapters.** TELUS-mediated extended-health flows and CDAnet dental flows have different transaction semantics.
6. **No evidence supports a generic consumer-side direct-billing API abstraction.**
7. **No evidence supports browser automation using borrowed provider/member credentials as an acceptable production integration strategy.**

## 4. Architecture recommendation

Maintain the provider-mediated transaction boundary:

`member intent -> BenefitFlow normalization/proposal -> explicit member approval -> authorized provider/clinic adapter -> sanctioned claims rail -> authoritative rail response -> reconciliation/audit`

Do not collapse these into a single `direct_bill()` abstraction.

Recommended capability model:

```text
rail_id
principal_type = provider | clinic | practice_management_vendor
partner_status = unknown | inquiry_started | approved | rejected | expired
integration_access = public_api | partner_api | delegated_provider_api | standards_edi | portal_manual | unknown
eligibility_method = native_read | claim_then_reverse | manual | unknown
claim_submission = supported | unsupported | unknown
reversal = supported | unsupported | unknown
predetermination = supported | unsupported | unknown
real_time_adjudication = supported | unsupported | unknown
payment_recipient = provider | member | plan_dependent | unknown
credential_mode = delegated_token | partner_credential | provider_session | manual | unknown
verified_at
source_url
```

Fail-closed rules:
- `partner_status != approved` -> no live machine transaction.
- `integration_access in {portal_manual, unknown}` -> handoff only; no autonomous claim/eligibility operation.
- `eligibility_method == claim_then_reverse` -> no background eligibility probing.
- expired/degraded provider authorization -> reauthorization required; never fall back to stored portal password.
- provider/clinic principal mismatch with approved proposal -> block.
- stale capability evidence -> downgrade to `needs_revalidation` / unknown.

## 5. Highest-value next discovery actions

### P1 — Pacific Blue Cross API discovery
Obtain authoritative answers for:
- partner/vendor eligibility;
- API specification and transaction catalog;
- authentication/delegation model;
- sandbox/test environment;
- provider/location mapping model;
- claim, reversal, predetermination and eligibility semantics;
- webhook/event support;
- certification/security review;
- commercial/onboarding requirements.

### P2 — TELUS eClaims vendor/partner discovery
Obtain authoritative answers for:
- whether a new technology vendor can integrate with eClaims;
- partner onboarding and certification process;
- technical API/SDK/EDI interface;
- test/sandbox environment;
- supported insurer-by-transaction capability matrix;
- identity model for clinic/provider/location;
- token/credential delegation;
- COB and secondary-plan semantics;
- pricing/commercial terms.

### P3 — Sun Life machine-integration discovery
Do not assume one exists. Confirm whether Sun Life Connect/Direct exposes a sanctioned partner machine interface and under what provider authorization model.

## 6. Unknowns / blockers

Still unknown from public evidence:
- PBC API auth protocol, scopes, sandbox and vendor eligibility.
- TELUS eClaims API/EDI specification and commercial onboarding for a new vendor.
- Whether TELUS CHR Enterprise API exposes eClaims functions.
- Sun Life partner API availability.
- GreenShield/providerConnect machine-interface availability.
- Carrier-by-carrier COB/secondary coverage semantics.
- Exact consent/disclosure obligations imposed contractually by each rail.
- Whether BenefitFlow's business model qualifies as an approved technology/PMS partner.

These are partner-discovery blockers, not engineering gaps that should be guessed around.

## 7. Research disposition

**SUPPORTED:** Provider-mediated sanctioned direct-billing integrations are feasible in Canada.  
**SUPPORTED:** TELUS eClaims is the highest-leverage aggregation target currently evidenced.  
**SUPPORTED:** Pacific Blue Cross is the clearest bounded insurer/API discovery target.  
**SUPPORTED:** Rail-specific transaction semantics must remain explicit and typed.  
**CONTRADICTED:** A generic consumer-side direct-billing API abstraction.  
**INSUFFICIENT:** Direct BenefitFlow machine access to TELUS, Sun Life or other insurer/provider rails until partner authorization and technical specifications are confirmed.

## 8. Safety / authority note

This artifact does not authorize or execute claims, bookings, provider account access, member-data disclosure, credential use, financial action, or cross-project mutation. It does not modify accepted state. It is research evidence for Manager/Primary review and disposition only.
