# BenefitFlow Research Lane: Insurer Direct Billing

**Agent:** `researcher-insurer-direct-billing-20261003T2221Z`  
**Project:** `benefitflow`  
**Date:** 2026-10-03  
**Status:** Research handoff for Primary/reviewer consideration; not accepted state.

## Executive conclusion

BenefitFlow should model Canadian extended-health direct billing as a **multi-gate provider/insurer/plan transaction capability**, not as a single Boolean or tri-state provider attribute.

The current beta model uses:

```python
direct_billing: Literal["confirmed", "not_available", "unknown"]
```

and the synthetic verifier marks direct billing as `confirmed` whenever an insurer name is present. That behavior is not safe for production semantics.

A provider may:

1. be registered with a claims network generally;
2. be eligible for a particular insurer;
3. support a particular profession/service through that insurer;
4. be allowed to assign payment to the provider for one plan but not another;
5. be able to submit a claim but not a predetermination through the same client/channel;
6. receive payment directly while the member still owes a deductible/co-pay/non-covered balance;
7. support coordination of benefits only under specific transaction/order rules;
8. require member consent/signature at point of care;
9. change availability without insurer directory data updating in real time.

Therefore BenefitFlow needs to separate **provider capability evidence** from **member-plan adjudication certainty**.

---

## Evidence findings

### 1. TELUS Health eClaims is a major provider-side hub, not a consumer booking API

TELUS Health describes eClaims as a web-based point-of-sale system used by eligible healthcare providers to submit claims on behalf of patients. It supports browser, mobile, and integrations with participating practice-management software. Depending on the insurer, submissions may adjudicate automatically and return coverage, expense and provider-eligibility results in real time.

TELUS currently lists many participating insurers including Canada Life, Canada Life PSHCP, Manulife Financial, Desjardins, Equitable, ClaimSecure, People Corporation and others.

TELUS also states that the mobile workflow can capture patient consent for emailed responses, while predeterminations are not available from the mobile app. Registration can take one to three weeks and provider eligibility varies by profession and insurer.

**Product implication:** BenefitFlow should treat TELUS eClaims as a provider/clinic transaction rail. The public evidence reviewed does **not** establish a public consumer API that BenefitFlow can call directly. Production integration should therefore be assumed to require a formal TELUS/provider-software relationship until proven otherwise.

Sources:
- https://www.telus.com/en/health/health-professionals/allied-healthcare-professionals/eclaims
- https://www.telus.com/en/health/health-professionals/allied-healthcare-professionals/eclaims/faq
- https://www.telus.com/en/health/organizations/group-health-benefits/insurers/extended-healthcare-claims

### 2. Sun Life uses a provider-specific access layer and assignment/payment can vary

Sun Life's provider hub exposes Sun Life Connect for paramedical providers and facilities, with eClaims and Provider Search. Sun Life's eClaims documentation requires provider registration and banking details for direct deposit.

Sun Life plan-member material also distinguishes electronic submission from assignment of benefits: in many cases a provider can submit a claim and, with member consent, receive insurer payment directly, but some employer plans or provider configurations may instead direct reimbursement to the member.

**Product implication:** `claim_submission_supported` and `provider_payment_assignment_supported` are separate facts. A clinic saying "we submit electronically" must not automatically be represented as "you only pay the uncovered balance."

Sources:
- https://www.sunlife.ca/sl/provider/en/
- https://www.sunlife.ca/sl/provider/en/support/faqs/eclaims/

### 3. Manulife confirms point-of-care eClaims but payment destination is variable

Manulife states that many healthcare providers can submit claims at point of care, that adjudication is typically performed while the plan member is still in the provider's office, and that reimbursement may go either to the provider or to the plan member.

**Product implication:** direct billing needs a payment-recipient field. `provider_paid`, `member_paid`, and `unknown/plan_dependent` should not be collapsed into one status.

Source:
- https://www.manulife.ca/business/group-benefits/services/digital-claims-experience.html

### 4. Canada Life uses provider eClaims and separate dental transaction rails

Canada Life directs eligible providers to Provider eClaims and TELUS Health registration/direct-deposit workflows. Provider payments may be bundled and paid on a schedule rather than claim-by-claim.

Canada Life dental documentation shows a richer transaction vocabulary through CDAnet, including Claim, Coordination of Benefits Claim, Claim Reversal, Predetermination, EOB/acknowledgment transactions, and attachments. Canada Life specifies carrier ID and transaction configuration requirements for provider software.

Canada Life also documents COB-specific sequencing and explicitly warns providers to disclose only the claim details needed when coordinating with another carrier.

**Product implication:** BenefitFlow should model claim submission, predetermination, reversal and coordination-of-benefits as different capabilities. It should not infer real-time eligibility merely because a carrier participates in eClaims.

Sources:
- https://www.canadalife.com/resources/provider.html
- https://www.welcome.canadalife.com/psdcp-pdsp-provider/how-tos.html
- https://www.welcome.canadalife.com/psdcp-pdsp-provider/frequently-asked-questions.html

### 5. Pacific Blue Cross uses PROVIDERnet and demonstrates why “eligibility check” is not a simple read-only API

Pacific Blue Cross states that registered providers can directly bill through PROVIDERnet and must configure direct deposit before submitting the first claim. Its quick-start material tells providers that one way to check patient eligibility is to submit a claim and then reverse it.

**Product implication:** BenefitFlow must distinguish read-only coverage lookup from a transaction-based eligibility technique. It should **never** emulate submit-and-reverse as a background eligibility check without an authorized provider transaction context and explicit product/legal review.

Sources:
- https://www.pac.bluecross.ca/providerresource/how-tos/how-to-sign-up-for-providernet/
- https://www.pac.bluecross.ca/providerresource/how-tos/providernet-quick-start-guide/

### 6. Provider-directory evidence is useful discovery evidence, not transaction proof

Canada Life explicitly notes that its provider list is not updated in real time and that inclusion does not guarantee a claim; coverage remains subject to the member's plan.

**Product implication:** directory discovery can raise confidence that a provider may participate, but it cannot become the production value `direct_billing = confirmed` without a more current confirmation path.

Source:
- https://www.canadalife.com/insurance/workplace-benefits/eclaims-provider-listing.html

---

## Required semantic split for BenefitFlow

Replace the current single direct-billing field with a structured capability record. Suggested shape:

```python
class DirectBillingCapability(BaseModel):
    insurer_name: str
    service_category: str

    # Provider/network capability
    provider_enrollment: Literal["confirmed", "not_enrolled", "unknown"]
    transaction_rail: Literal[
        "telus_eclaims",
        "sun_life_connect",
        "pacific_blue_cross_providernet",
        "cdanet",
        "other_provider_portal",
        "practice_management_integration",
        "unknown",
    ]

    # Transaction capabilities
    electronic_claim_submission: Literal["supported", "not_supported", "unknown"]
    predetermination: Literal["supported", "not_supported", "unknown"]
    claim_reversal: Literal["supported", "not_supported", "unknown"]
    coordination_of_benefits: Literal["supported", "not_supported", "unknown"]

    # Payment semantics
    payment_recipient: Literal["provider", "member", "plan_dependent", "unknown"]
    assignment_of_benefits: Literal["supported", "not_supported", "plan_dependent", "unknown"]

    # Point-of-care/member requirements
    member_consent_required: bool | None = None
    signature_or_attestation_mode: str = ""
    required_member_fields: list[str] = []

    # Evidence
    evidence_source_type: Literal[
        "provider_confirmation",
        "insurer_directory",
        "insurer_documentation",
        "claims_network_documentation",
        "member_plan_document",
        "unknown",
    ]
    evidence_url: str = ""
    evidence_note: str = ""
    verified_at: datetime | None = None
    confidence: Literal["high", "medium", "low"] = "low"
```

The exact enum names can change; the semantic separation should remain.

---

## Recommended verification state machine

### Stage A — discovery

BenefitFlow discovers a provider and may record network/directory evidence.

State: `POSSIBLE_DIRECT_BILLING`

Allowed UI wording:
- "May support electronic claims for this insurer."
- "Needs clinic confirmation."

Never say:
- "Direct billing confirmed."
- "You will only pay $X."

### Stage B — provider confirmation

The clinic confirms current participation for the insurer and service category.

Capture:
- insurer/network accepted;
- practitioner/service category accepted;
- whether the clinic submits on behalf of the member;
- whether insurer payment can be assigned to the clinic;
- what identifiers are needed;
- whether predetermination is available;
- whether they can provide estimated member responsibility before treatment.

State: `PROVIDER_CAPABILITY_CONFIRMED`

This is still **not** proof of member-plan coverage.

### Stage C — member-plan confirmation / adjudication

Where a legitimate provider workflow can do so, the provider obtains a predetermination or point-of-care adjudication for the actual member plan.

State: `PLAN_TRANSACTION_RESULT_AVAILABLE`

Only here should BenefitFlow display a transaction-specific covered/uncovered amount as insurer-derived rather than estimated.

### Stage D — post-service claim result

Record the actual EOB/adjudication result and payment recipient. This should update utilization only from verified claim evidence, not solely from an appointment booking.

---

## Changes recommended against the current beta

### `benefitflow_beta/models.py`

Current `ProviderVerification.direct_billing` is too coarse. Add the structured direct-billing capability or at minimum these interim fields:

- `claim_submission_supported`
- `assignment_of_benefits`
- `payment_recipient`
- `predetermination_supported`
- `transaction_rail`
- `plan_specific_confirmation_required`
- `direct_billing_evidence_type`
- `direct_billing_verified_at`

### `benefitflow_beta/providers.py`

Current synthetic logic:

```python
direct_billing="confirmed" if insurer_name else "unknown"
```

should be explicitly marked as synthetic-only and must not survive into any production adapter. Presence of an insurer name provides no evidence of clinic enrollment, service eligibility, assignment of benefits, or member-plan coverage.

### `benefitflow_beta/workflow.py`

The transaction script currently tells the clinic that verification indicates a `direct_billing` status. Production should instead ask bounded confirmation questions if any direct-billing component remains plan-dependent.

Recommended pre-disclosure script logic:

1. reconfirm practitioner/service and current price;
2. ask whether the clinic currently submits electronic claims to the named insurer for this service;
3. ask whether insurer payment can be assigned directly to the clinic for this member's plan, or whether reimbursement goes to the member;
4. ask whether a predetermination/coverage check is available through the clinic's authorized provider workflow;
5. only after the clinic confirms a legitimate need, disclose the minimum member identifiers within the user's approved scope;
6. never submit a claim, eligibility transaction or reversal merely to discover coverage unless that transaction is separately authorized and valid for the provider workflow.

---

## Data-confidence policy

Suggested evidence priority for direct billing:

1. **Actual insurer/provider adjudication or predetermination for the member** — highest transaction confidence.
2. **Current clinic confirmation + insurer/network compatibility evidence** — high provider-capability confidence, not coverage certainty.
3. **Current insurer/provider portal documentation** — medium-to-high rail capability confidence.
4. **Insurer provider directory listing** — medium discovery confidence; not real-time proof.
5. **Clinic marketing page / third-party directory** — low-to-medium until reconfirmed.
6. **Inference from insurer name alone** — no acceptable production confidence.

Each record should retain timestamp and provenance because provider enrollment and insurer participation can change.

---

## Product UX implications

BenefitFlow should present three separate user-facing concepts:

1. **Provider supports electronic claims**
2. **Provider can be paid directly by this insurer/plan**
3. **Expected amount the member will owe**

These are not synonyms.

Recommended wording examples:

- `Electronic claims: confirmed with clinic`
- `Direct insurer payment to clinic: plan-dependent`
- `Estimated member cost: $35–$60 until adjudication`
- `Predetermination: clinic can request after your approval`

This reduces a major trust risk: telling users a clinic "direct bills" and then having them unexpectedly pay the full visit cost.

---

## Coordination-of-benefits implications

COB requires an explicit ordered-plan model. At minimum BenefitFlow should preserve:

- primary insurer;
- secondary insurer;
- whether the provider can submit COB electronically;
- whether an EOB from the primary is required before secondary submission;
- whether the second carrier is automatically processed by the first carrier's workflow in the specific scenario;
- member-approved disclosure scope for the minimum EOB/claim details needed.

The system should not assume a universal COB sequence across carriers.

---

## Engineering acceptance tests suggested from this research

1. Insurer name present but clinic enrollment unknown -> direct billing must remain unconfirmed.
2. Clinic supports TELUS eClaims but member's plan directs payment to member -> UI must not claim direct provider payment.
3. Clinic submits claims but does not support predeterminations -> planner must keep member cost estimated before service.
4. Directory lists provider but evidence is stale -> booking proposal should require fresh provider confirmation.
5. Provider says "we direct bill most plans" -> system records `plan_dependent`, not `confirmed`.
6. Member has two plans -> workflow requires ordered COB metadata before predicting secondary reimbursement.
7. A coverage-check method would require submit-and-reverse -> system blocks autonomous use absent an explicitly approved provider transaction adapter.
8. Clinic requests plan/member ID before confirming it needs those fields -> transaction script must withhold identifiers until purpose is reconfirmed.
9. Actual adjudication returns less than optimizer estimate -> actual EOB becomes authoritative and utilization state reconciles from evidence.
10. Provider switches payment recipient from clinic to member -> direct-billing UI changes without incorrectly changing electronic-claim capability.

---

## Research gaps / next actions

The following need primary/manager follow-up or a dedicated integration lane:

1. Determine whether TELUS Health exposes a partner/developer API or certification program suitable for BenefitFlow's intended production model. Public pages reviewed establish provider software integration but not a public consumer API.
2. Identify practice-management platforms with supported eClaims integrations and partnership/API programs; this may be a more practical integration route than insurer-by-insurer automation.
3. Obtain and review formal terms for provider-network automated access before implementing any browser or credential automation.
4. Research insurer-specific provider directories/APIs and freshness guarantees.
5. Define member-consent and privacy requirements with the privacy/regulatory lane before transmitting plan/member identifiers to a provider.
6. Extend the optimizer so pre-service cost remains an estimate until a plan-specific adjudication/predetermination result exists.

---

## Recommended Primary disposition

**Accept the semantic correction immediately:** direct billing is a structured, evidence-backed capability and transaction state, not a single provider flag.

**Do not implement live claim submission yet.** First harden the data model and verification/approval boundary, then investigate sanctioned integration paths with TELUS Health, insurer provider platforms, or certified practice-management software.
