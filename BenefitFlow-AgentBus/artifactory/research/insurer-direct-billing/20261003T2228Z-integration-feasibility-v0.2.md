# BenefitFlow Insurer Direct Billing — Integration Feasibility Tranche v0.2

**Agent:** `researcher-insurer-direct-billing-20261003T2221Z`  
**Project:** `benefitflow`  
**Lane:** `insurer-direct-billing`  
**Timestamp:** 2026-10-03T22:28:00Z  
**Status:** Research evidence for manager/Primary review; not accepted project state.

## 1. Claim / question

What production integration paths are actually evidenced for Canadian extended-health direct billing, and which of those paths are suitable for BenefitFlow without credential sharing, browser automation, or pretending a consumer application has provider authority?

## 2. Evidence

### E1 — TELUS Health eClaims is distributed through provider portals and an established practice-management software ecosystem
**Publisher / authority:** TELUS Health  
**Freshness:** current page reviewed 2026-10-03  
**Jurisdiction:** Canada  
**Source quality:** authoritative first-party commercial source  
**Links:**
- https://www.telus.com/en/health/health-professionals/allied-healthcare-professionals/eclaims
- https://go.telushealth.com/hubfs/eclaims/register/index.html

**Observed fact:** TELUS describes eClaims as a provider-facing direct-billing service with browser/mobile access and integration into practice-management software. TELUS currently identifies Gold partners including Antibex, Clinicmaster, Innocare, Jane, Optosys, and Practice Perfect, plus participating solutions including ABELMed, Adracare, chirosuite, Claim Manager, Embodia, GO rendezvous, Juvonno, Massage ManEdger, Medexa, MRX Solutions, Noterro, OCUCO, Outsmart, owlpractice, Practice Jewel, Wink, and visual-eyes. TELUS currently highlights Canada Life, ClaimSecure, Desjardins, iA, and Manulife among participating insurers.

**Interpretation:** There is strong evidence that TELUS supports sanctioned vendor integrations, but the public pages reviewed do not expose a general consumer/developer eClaims API that BenefitFlow can call directly.

### E2 — TELUS CHR exposes an Enterprise API, but this does not establish direct eClaims API rights
**Publisher / authority:** TELUS Health  
**Freshness:** current page reviewed 2026-10-03  
**Jurisdiction:** Canada  
**Source quality:** authoritative first-party commercial source  
**Link:** https://www.telus.com/en/health/health-professionals/clinics/emr-add-ons

**Observed fact:** TELUS advertises a CHR Enterprise API for integrations with tools built or purchased by clinics, and separately lists eClaims as an available CHR capability.

**Interpretation:** BenefitFlow may have a clinic-integration route through CHR, but evidence is insufficient to conclude that the CHR Enterprise API exposes eClaims transactions. That must be verified contractually/technically with TELUS before architecture depends on it.

### E3 — Jane demonstrates real production TELUS eClaims integration semantics
**Publisher / authority:** Jane Software Inc.  
**Freshness:** current guides reviewed 2026-10-03  
**Jurisdiction:** Canada  
**Source quality:** primary commercial implementation source  
**Links:**
- https://jane.app/telus
- https://jane.app/guide/telus-eclaims-setting-up-your-telus-eclaims-integration
- https://jane.app/guide/telus-eclaims-submitting-claims-and-eligibility-checks-through-the-telus-eclaims-integration
- https://jane.app/guide/canadian-insurance-integrations-hub

**Observed fact:** Jane links clinic/provider TELUS eClaims identities and supports eligibility checks, claim submissions, reversals, real-time insurer responses, EOB retrieval, and payment reconciliation. Jane requires the clinic/provider to be registered with TELUS first. Provider/location identity is linked at the clinic level.

**Interpretation:** The durable authorization model is provider-owned identity + sanctioned PMS integration. BenefitFlow should not model the member as the claims-network principal.

### E4 — Jane itself is not an open scheduling/insurance API target
**Publisher / authority:** Jane Software Inc.  
**Freshness:** current 2026 program material  
**Jurisdiction:** Canada / US / UK platform  
**Source quality:** primary commercial source  
**Links:**
- https://jane.app/blog/jane-integrations-our-program-our-partners-and-how-to-work-with-us
- https://integrations.jane.app/application_forms/jane-integrations-partner-interest-form/partner_applications/new

**Observed fact:** Jane states it is not launching an open public API; integrations require a vetted partnership pathway. Current API capability described in the partner application supports reading patient, appointment, and treatment data and writing into charting, but not patient or appointment creation/modification/deletion. Jane also states that posting directly into calendars is not supported and that it is not currently looking to work with AI scheduling tools.

**Interpretation:** Jane is useful as an integration partner candidate for data interoperability, but it is currently a poor dependency for BenefitFlow's autonomous booking transaction path. Any integration must be partner-approved and should not assume schedule-write capability.

### E5 — Pacific Blue Cross explicitly advertises provider API integration
**Publisher / authority:** Pacific Blue Cross  
**Freshness:** current page reviewed 2026-10-03; provider materials updated July 9, 2026  
**Jurisdiction:** British Columbia  
**Source quality:** authoritative insurer/provider-network source  
**Links:**
- https://www.pac.bluecross.ca/providerresource/
- https://www.pac.bluecross.ca/providerresource/how-tos/providernet-quick-start-guide/

**Observed fact:** Pacific Blue Cross lists “API Integration” for healthcare and vision providers and directs existing PROVIDERnet users to provider support for API integration questions. PROVIDERnet supports registered providers, direct deposit, claims, and reversals.

**Interpretation:** PBC is the clearest insurer-specific candidate found for a sanctioned BenefitFlow integration pilot, provided the integration operates for/through registered provider accounts rather than using member credentials.

### E6 — Jane's PBC integration exposes the authorization pattern
**Publisher / authority:** Jane Software Inc.  
**Freshness:** current guide reviewed 2026-10-03  
**Jurisdiction:** British Columbia  
**Source quality:** primary commercial implementation source  
**Link:** https://jane.app/guide/pacific-blue-cross-setting-up-your-providernet-integration

**Observed fact:** Jane links a clinic's PROVIDERnet account through an explicit PBC consent flow. PBC locations/practitioners are mapped into Jane, and an “Offline Access” option keeps the authorization active for roughly 30 days before re-authentication. New practitioners and locations must first be configured in PBC.

**Interpretation:** BenefitFlow should use delegated provider authorization tokens/consents where available. It should not store provider passwords as the normal integration mechanism.

### E7 — GreenShield/providerConnect is provider-authorized and supports eligibility + real-time adjudication, but no open API was established
**Publisher / authority:** GreenShield / providerConnect  
**Freshness:** current pages reviewed 2026-10-03  
**Jurisdiction:** Canada  
**Source quality:** authoritative provider-network source  
**Links:**
- https://app.providerconnect.ca/default.aspx?lang=en-CA
- https://www.providerconnect.ca/AboutUs.aspx?lang=en-CA
- https://www.greenshield.ca/en-ca/faq

**Observed fact:** providerConnect supports health-service-provider eligibility checks, online claim submission with immediate adjudication, payment assignment to provider or patient, direct deposit, statements, and claims reporting. GreenShield describes providerConnect as its provider portal. The public pages reviewed do not expose an open developer API.

**Interpretation:** GreenShield/providerConnect is a high-value workflow target, but BenefitFlow should treat live integration as `PARTNERSHIP_OR_API_UNKNOWN` until GreenShield confirms a sanctioned machine interface.

### E8 — Insurer participation and payment semantics remain carrier/plan dependent
**Publisher / authority:** Desjardins, Manulife  
**Freshness:** current pages reviewed 2026-10-03  
**Jurisdiction:** Canada  
**Source quality:** authoritative insurer sources  
**Links:**
- https://www.desjardins.com/en/insurance/group/claims/service-provider.html
- https://www.manulife.ca/business/group-benefits/services/digital-claims-experience.html

**Observed fact:** Desjardins tells members that participating providers registered with TELUS Health eClaims can submit claims where the member's card/plan permits. Manulife states provider eClaims can adjudicate at point of care and that reimbursement may go to the provider or member.

**Interpretation:** Even with a functioning rail, BenefitFlow must retain plan-level payment-recipient and adjudication uncertainty until an actual eligibility/adjudication response exists.

## 3. Source quality

Highest-confidence sources in this tranche are insurer/network first-party operational pages (TELUS Health, Pacific Blue Cross, GreenShield/providerConnect, Manulife, Desjardins) and first-party implementation documentation from Jane. No third-party blog evidence is required for the core conclusions.

## 4. Freshness

Treat every integration capability, insurer participation list, specialty eligibility rule, API availability statement, and authentication flow as time-sensitive. Store `verified_at`, source URL, and evidence type. Revalidate before production enablement.

## 5. Observed facts

1. TELUS eClaims has a mature provider/PMS integration ecosystem.
2. TELUS public material reviewed does not establish an open consumer eClaims API.
3. Pacific Blue Cross openly acknowledges API integrations for registered PROVIDERnet users.
4. PBC's real-world Jane flow uses provider account authorization and explicit consent, not member portal credentials.
5. providerConnect supports eligibility and real-time claim adjudication but no public machine API was found.
6. Jane's partner platform is vetted, non-public, and currently does not support appointment writes.
7. Claim-network identity is fundamentally provider/clinic-oriented in every operational path reviewed.

## 6. Interpretation

BenefitFlow should adopt a **provider-mediated transaction architecture**:

`BenefitFlow member approval -> clinic/provider adapter authorization -> sanctioned claims rail -> adjudication response -> BenefitFlow evidence record`

not:

`BenefitFlow logs into insurer/provider portal with borrowed credentials -> scrape/submit -> infer result`.

The integration object should identify the **authorized transaction principal** explicitly:

```python
class ClaimsRailAuthorization(BaseModel):
    rail: str
    principal_type: Literal["provider", "clinic", "practice_management_vendor"]
    provider_or_clinic_id: str
    authorization_mode: Literal[
        "oauth_or_delegated_token",
        "vendor_partner_credential",
        "provider_portal_session",
        "manual_provider_action",
        "unknown",
    ]
    scopes: list[str]
    expires_at: datetime | None
    reauth_required: bool
    source_url: str
    verified_at: datetime
```

`provider_portal_session` should be discouraged/blocked for production automation unless the network expressly authorizes that mechanism.

## 7. Contradictions / edge cases

### C1 — “Eligibility check” is not uniform
Jane/ClinicSense demonstrate explicit TELUS eligibility-check functions, while Pacific Blue Cross's own quick-start material describes checking eligibility by submitting then reversing a claim.

**Fail-closed consequence:** model eligibility as a rail-specific transaction capability with `method`, not a universal read endpoint. Do not autonomously emulate submit-and-reverse.

### C2 — PMS integration does not imply BenefitFlow access
TELUS supports many PMS vendors, but that proves those vendors have sanctioned access, not that BenefitFlow does.

**Fail-closed consequence:** represent partner status as `unknown/not_approved` until a formal integration path is obtained.

### C3 — Jane is technically integrable but not presently suitable for autonomous booking writes
Jane provides a vetted API pathway but states that appointment creation/modification/deletion and direct calendar posting are not supported, and AI scheduling partnerships are not currently sought.

**Fail-closed consequence:** do not plan BenefitFlow booking automation around Jane's API today. Treat Jane as a read/charting or future partnership target unless policy changes.

## 8. Implementation consequence

### Schema
Add:
- `claims_rail`
- `transaction_principal_type`
- `provider_network_registration_status`
- `authorization_mode`
- `authorization_scopes`
- `eligibility_check_method`
- `claim_submission_supported`
- `reversal_supported`
- `predetermination_supported`
- `payment_recipient`
- `partner_status`
- `evidence_source_url`
- `verified_at`

### Adapter registry
Create an adapter capability registry rather than insurer-specific booleans:

```python
class ClaimsRailCapabilities(BaseModel):
    rail_id: str
    provider_registration_required: bool
    eligibility: Literal["native", "claim_then_reverse", "manual", "unknown"]
    claim_submission: bool | None
    reversal: bool | None
    predetermination: bool | None
    real_time_adjudication: bool | None
    assignment_to_provider: Literal["supported", "plan_dependent", "unsupported", "unknown"]
    integration_access: Literal[
        "public_api",
        "partner_api",
        "provider_delegated_api",
        "portal_only",
        "unknown",
    ]
```

### Architecture priority
Recommended investigation order:
1. **Pacific Blue Cross PROVIDERnet API** — strongest explicit API signal; BC pilot is bounded.
2. **TELUS Health eClaims partner/vendor program** — largest multi-insurer leverage.
3. **GreenShield/providerConnect partnership/API inquiry** — high workflow value, interface unresolved.
4. **Insurer-specific portals such as Sun Life Connect** — use only via sanctioned provider integration if available; otherwise manual/provider-mediated.
5. **PMS partnerships** — potentially valuable for clinics already on Jane/Noterro/etc., but each vendor's scopes/policies must be treated independently.

### Beta behavior
Until adapter authorization exists, BenefitFlow should stop at:
`provider capability verified -> member approval -> provider-facing handoff`
and must not claim that an electronic eligibility check or claim was performed.

## 9. Privacy / security impact

1. Provider/clinic credentials or delegated tokens become high-value secrets and must be isolated from general research/LLM context.
2. Member plan/member IDs should be disclosed only to the authorized provider transaction adapter after the existing human approval gate.
3. Integration tokens should be scoped per clinic/location/provider where the rail supports it.
4. Store token metadata and scopes separately from claim evidence.
5. Do not retain portal passwords when delegated authorization is available.
6. PMS integrations can expose patient/appointment/treatment data; apply least privilege and do not request charting/clinical scopes merely to submit benefits transactions.
7. Every external claim/eligibility transaction should produce an immutable audit event containing the rail, authorized principal, user approval reference, transaction type, response class, and evidence pointer — but not unnecessary raw identifiers.

## 10. Uncertainty / missing evidence

1. Exact TELUS partner onboarding terms, technical API specification, certification process, and commercial requirements for a new vendor.
2. Whether TELUS CHR Enterprise API exposes eClaims functions.
3. Pacific Blue Cross API technical specification, scopes, authentication protocol, sandbox availability, and vendor eligibility.
4. Whether GreenShield/providerConnect offers a supported partner API for extended-health claims.
5. Current sanctioned integration routes for Sun Life Connect.
6. Carrier-specific secondary-plan/COB support across TELUS and providerConnect.
7. Whether a BenefitFlow business model qualifies as an acceptable provider/PMS/technology partner for each network.

These require direct business-development/technical inquiries before production commitments.

## 11. Recommended disposition

**SUPPORTED:** Provider-mediated, sanctioned claims-network integrations are technically feasible in Canada.  
**SUPPORTED:** PBC is a credible bounded API pilot candidate.  
**SUPPORTED:** TELUS eClaims offers the largest evidenced multi-insurer vendor-integration surface.  
**CONTRADICTED:** A generic consumer-side “direct billing API” abstraction is not supported by the evidence.  
**INSUFFICIENT:** Public evidence does not establish direct BenefitFlow API access to TELUS, GreenShield/providerConnect, or Sun Life.  
**ESCALATE_TO_PRIMARY:** Begin partner/API discovery with PBC and TELUS before building live transaction code.

## Proposed engineering tests

1. Adapter without formal partner/provider authorization -> transaction blocked.
2. Provider supports TELUS but BenefitFlow has no sanctioned adapter -> handoff only; no live eligibility call.
3. PBC adapter token expired -> no credential fallback to stored password; request provider reauthorization.
4. Rail reports `claim_then_reverse` eligibility method -> autonomous background coverage check blocked.
5. Rail returns payment to member -> UI must not say provider will be paid directly.
6. PMS exposes patient reads but not appointment writes -> booking adapter remains disabled.
7. Transaction requests scope not granted by clinic -> fail closed.
8. Member approval references Provider A but adapter principal is Provider B -> fail closed.
9. Clinic changes location/provider mapping -> cached authorization invalidated until revalidated.
10. Partner-status evidence older than configured freshness threshold -> capability downgraded to `needs_revalidation`.
