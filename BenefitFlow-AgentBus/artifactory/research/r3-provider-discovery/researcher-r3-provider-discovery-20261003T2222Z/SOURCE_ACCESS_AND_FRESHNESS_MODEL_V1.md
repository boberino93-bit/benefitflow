# R3 Provider Discovery — Source Access, Automation Boundaries & Freshness Model V1

**Project:** BenefitFlow (`project_id=benefitflow`)  
**Agent:** `researcher-r3-provider-discovery-20261003T2222Z`  
**Slot:** R3 — Provider Discovery and Identity Resolution  
**Manager:** `manager-01`  
**Status:** EVIDENCE/PROPOSAL — not accepted project truth  
**Evidence date:** 2026-10-03

## Purpose

This packet follows the initial R3 finding that BenefitFlow must separate provider identity, licensure, payer participation, clinic metadata, and availability. This pass focuses on a narrower production question:

> Which provider-discovery sources can BenefitFlow rely on, at what freshness, and with what automation boundary?

The central conclusion is that **source authority and source automability are independent properties**. A source can be highly authoritative for a fact while being unsuitable for bulk ingestion, scraping, or autonomous transaction execution.

## Verified evidence

### E1 — CHCPBC registry is authoritative for licensure verification, but expressly restricted from commercial use

The College of Health and Care Professionals of BC (CHCPBC) states that its Public Registry exists to verify whether a health professional is currently licensed. The registry covers audiology, dietetics, hearing instrument dispensing, occupational therapy, opticianry, optometry, physical therapy, psychology, and speech-language pathology.

CHCPBC also states that the registry information is **not for commercial, marketing, or fundraising purposes**. The live registry is designed for searching individual professionals and returns a maximum of 25 records at one time.

Source:
- https://chcpbc.org/public/
- https://chcpbc.alinityapp.com/client/publicdirectory

**Interpretation:** high authority does not imply permission for automated commercial ingestion. BenefitFlow should not design a scraper-first architecture around this registry. Production use needs an explicit legal/terms/licensing decision, and a safer near-term design is bounded, user-directed verification of an already-selected professional.

### E2 — CCHPBC registry has the same commercial-use restriction and is the established verification process during licence-number migration

The College of Complementary Health Professionals of BC (CCHPBC) regulates chiropractors, massage therapists, naturopathic physicians, and traditional Chinese medicine practitioners/acupuncturists. Its public-facing materials state that registry information is not to be used for commercial, marketing, or fundraising purposes.

CCHPBC further tells insurers to continue using its Registry and established verification processes during its 2026–2027 licence-number transition. Chiropractors changed licence numbers June 17, naturopathic physicians September 1, TCM/acupuncture September 2, and massage therapists transition October 5, 2026. All licensees must transition by March 31, 2027.

Source:
- https://cchpbc.ca/public/
- https://cchpbc.ca/public/practitioner-search/
- https://cchpbc.ca/login/

**Interpretation:** BenefitFlow needs versioned regulator identifiers and cannot use licence number as its durable entity key. It also needs a transition-aware verification rule that tolerates an old insurer-side identifier and a newer regulator-side identifier referring to the same professional.

### E3 — CCHPBC explicitly warns that registration numbers are fraud-sensitive

CCHPBC advises practitioners to safeguard registration numbers because fraudulent billing can occur when those identifiers are misused, and says registration numbers should not be published on public websites or marketing materials.

Source:
- https://cchpbc.ca/prevent-billing-fraud-safeguard-your-registration-number/

**Security implication:** provider identifiers are not harmless enrichment data. BenefitFlow should retain only identifiers necessary for verification/claims compatibility, scope access to them, and avoid exposing full identifiers in public UI or analytics.

### E4 — Jane Practitioner Search is useful for fresh availability, but it is an opt-in BC beta and requires Jane ID

Jane states that Practitioner Search is currently available in B.C. and supports chiropractic care, massage therapy, physiotherapy, and acupuncture. Patients must sign in with a Jane ID. Results expose current availability and redirect the patient to the clinic's online booking page to complete the appointment.

Clinics/practitioners must opt in. Changes to profile/settings/availability may take **up to 3 hours** to appear in Practitioner Search.

Source:
- https://jane.app/guide/practitioner-search-for-patients
- https://jane.app/guide/practitioner-search-for-clinics
- https://jane.app/guide/how-to-enable-practitioner-search-for-your-clinic

**Interpretation:** Jane is valuable as a fresh discovery/availability signal, but not a complete provider universe. “Not found” is not negative evidence. A practical freshness ceiling for search-derived availability is approximately the source's documented propagation window; BenefitFlow should still re-check before presenting a final booking choice.

### E5 — Jane does not offer an open API and currently rejects the architecture BenefitFlow would otherwise want for autonomous scheduling

Jane says its integration program is approval-based and it is **not launching an open public API**. Current guidance says Jane is not looking to work with AI scheduling or AI scribe tools, clinics cannot build their own integrations, posting directly into Jane calendars is not supported, and integrations must not depend on credential sharing or disabling two-factor authentication.

Source:
- https://jane.app/blog/jane-integrations-our-program-our-partners-and-how-to-work-with-us
- https://jane.app/guide/integrations-hub-faq

**Implementation consequence:** BenefitFlow must not assume it can graduate from Jane search to autonomous calendar posting. The production-safe baseline is:
1. discover/compare,
2. deep-link or user-directed handoff into Jane/clinic booking,
3. observe a user-approved confirmation result,
unless Jane later approves a partner integration that explicitly permits BenefitFlow's use case.

This is an important boundary between **discovery automation** and **transaction automation**.

### E6 — TELUS eClaims exposes an API, but it is a claims/provider workflow API, not evidence of a public provider-discovery API

TELUS Health's provider agreement describes eClaims service access through a web portal, mobile app, or API for providers/practice-management systems. TELUS documentation shows that integrated PMS access uses provider credentials/account data, TELUS provider IDs, location IDs, roles, licence issuer and licence numbers. Provider additions and role/licence additions are reviewed by TELUS.

TELUS also lists supported practice-management software products that integrate with eClaims, including Jane.

Source:
- https://plus.telushealth.co/page/eclaims/resources/asset/pdf/PROVIDER_AGREEMENT_eClaims_and_WSIB_EN.pdf
- https://plus.telushealth.co/page/eclaims/help/learningcorner/APIInstructions.htm
- https://plus.telushealth.co/page/eclaims/help/FAQ/FAQ.htm
- https://plus.telushealth.co/page/eclaims/help/Provider/Adding_providers.htm
- https://plus.telushealth.co/page/eclaims/help/Provider/Roles_and_licenses.htm

**Interpretation:** the existence of a TELUS eClaims API must not be normalized into “BenefitFlow can query TELUS for provider discovery.” The documented API is scoped to registered provider/PMS claims workflows and uses authenticated provider-side account information. Any BenefitFlow integration would require a separate commercial/technical authorization path and should be handled by R2/R10 as a claims/transaction integration, not treated as an open R3 directory source.

### E7 — Canada Life directory is useful candidate evidence, but explicitly stale and non-guaranteeing

Canada Life's provider list says listed providers **may** be eligible under a group benefits plan, claims are not guaranteed, the list is not updated in real time, and provider names/addresses are shown as submitted by providers.

Source:
- https://www.canadalife.com/insurance/workplace-benefits/eclaims-provider-listing.html

**Interpretation:** this should be modeled as a payer-specific candidate/compatibility observation, not a live licensure source, live location source, or member-specific eligibility decision.

### E8 — Sun Life Provider Search contains broad discovery and some booking/availability signals, but fields have different provenance

Sun Life Provider Search says it exposes a Canada-wide provider database, ratings, cost indicators, services, hours, and—on select provider profiles—available slots and booking.

Its disclaimer says:
- cost indicators are based on submitted claims and may not reflect current pricing;
- next-available appointments are informational and may not apply to every service/client type;
- results may omit suitable providers;
- Sun Life does not validate information supplied by providers for extended profiles.

Sun Life also states that a basic provider profile can be automatically created when a Sun Life client submits a claim for that provider.

Source:
- https://providersearch.sunlife.ca/en/
- https://www.sunlife.ca/sl/provider/en/support/faqs/provider-search-and-profiles/
- https://www.sunlife.ca/sl/provider/en/provider-search/

**Interpretation:** Sun Life is not one trust domain. Ratings derive from claims-related member feedback; basic profiles can originate from claim history; extended profile fields are provider-entered; availability can be informational or linked to booking. BenefitFlow should retain **field-level provenance**, not label the entire profile “verified.”

## Source quality and automation matrix

| Source | Strongest fact | Authority | Freshness | Completeness | Automation/terms posture | BenefitFlow role |
|---|---|---:|---|---|---|---|
| CHCPBC Registry | current licensure/status | High | High when queried live | Scoped to regulated professions | Explicit commercial-use restriction | Bounded verification only unless permission obtained |
| CCHPBC Registry | current licensure/status | High | High when queried live | Scoped to 4 profession families | Explicit commercial-use restriction | Bounded verification; transition-aware aliasing |
| Jane Practitioner Search | opted-in bookable availability | High for surfaced slots | Near-live but changes can take up to 3h | Incomplete/opt-in/BC beta | No open API; approval program; AI scheduling not currently supported | Discovery + deep-link handoff |
| TELUS eClaims | claims-network/provider workflow | High inside authenticated provider workflow | Operational | Not a public directory | Licensed provider/PMS API, authenticated and purpose-limited | R2/R10 integration candidate, not R3 public discovery |
| Canada Life provider list | payer-specific candidate signal | Medium | Explicitly not real-time | Incomplete | Public list; no evidence here of supported public API | Candidate evidence only |
| Sun Life Provider Search | broad discovery; ratings; some availability | Field-dependent | Field-dependent | Broad but explicitly incomplete | Public search; no supported public API established in this pass | Candidate discovery with field-level provenance |

## Proposed freshness model

BenefitFlow should not assign one TTL to a provider record. TTL belongs to the **assertion type + source**.

### Suggested initial TTL policy

These are engineering proposals, not claims about source guarantees.

| Assertion | Proposed usable age | Hard behavior after age | Rationale |
|---|---:|---|---|
| live appointment slot | 5–15 minutes | re-query before proposal/transaction | slots are highly perishable |
| Jane search availability snapshot | <= 3 hours for discovery display; re-check before action | mark stale and refresh | Jane documents up to 3h propagation |
| accepting new patients | 24 hours | re-verify before booking proposal | clinic operational state changes quickly |
| clinic hours/contact | 7 days | soft warning then refresh | moderate volatility |
| current cash price | 7 days | re-verify before approval if material | price can affect user out-of-pocket |
| payer participation/direct billing | 30 days, but re-check at booking if relied upon | stale -> unknown until refreshed | payer/provider participation changes |
| regulator licence status | 24 hours when used to recommend/book | re-query live | high consequence despite low average volatility |
| regulator identifier alias/history | durable, append-only | never overwrite; supersede | needed for identity continuity |
| ratings/cost statistics | source-defined snapshot date | show observation date; never imply live | aggregated historical signal |

### Freshness status enum

Recommended common vocabulary:

- `FRESH`
- `AGING`
- `STALE_RECHECK_REQUIRED`
- `EXPIRED_DO_NOT_USE`
- `SOURCE_UNAVAILABLE`
- `SOURCE_NOT_AUTHORIZED`

`SOURCE_NOT_AUTHORIZED` is important: it prevents the product from treating a technically reachable page as an approved ingestion source.

## Proposed provider evidence schema

```text
ProviderEntity
  provider_entity_id              # internal immutable ID
  canonical_name
  profession
  jurisdiction

ProviderIdentifierAlias
  provider_entity_id
  authority                       # CHCPBC, CCHPBC, TELUS, payer, clinic
  identifier_type
  identifier_value_encrypted_or_masked
  valid_from
  valid_to
  observed_at
  supersedes_alias_id
  source_observation_id

EvidenceObservation
  observation_id
  provider_entity_id
  assertion_type                  # LICENSURE, DIRECT_BILLING, LOCATION, PRICE, AVAILABILITY...
  assertion_value
  source_name
  source_url_or_reference
  source_authority_class
  source_terms_class              # PUBLIC_OK, BOUNDED_VERIFICATION_ONLY, PARTNER_ONLY, UNKNOWN
  observed_at
  expires_at
  freshness_status
  jurisdiction
  confidence
  negative_reason                 # NOT_LISTED, PRIVACY_SUPPRESSED, OPT_OUT, OUT_OF_SCOPE...
  raw_evidence_hash
```

## Contradiction rules

### C1 — Regulator vs directory
If a directory lists a provider but the regulator says licence is suspended/former/not authorized:
- regulator wins for practise-authority purposes;
- directory record remains as historical evidence;
- BenefitFlow must block recommendation/booking until resolved.

### C2 — Directory missing, regulator active
Do not infer ineligibility. Classify the directory result as `NOT_LISTED` or source-specific exclusion.

### C3 — Payer directory says direct billing; clinic says no
Use the clinic's fresh operational response for current booking expectations, while retaining the payer directory observation as contradictory/stale until rechecked.

### C4 — Clinic says direct billing; payer/member check says not covered
Member/plan-specific eligibility wins for expected reimbursement. Direct billing capability can remain true while coverage is false.

### C5 — Licence identifier mismatch during 2026 migrations
Attempt alias resolution using name + profession + jurisdiction + known transition dates. Do not create a new provider entity solely because the regulator number changed.

### C6 — Jane shows slot; clinic page no longer shows slot
Availability is expired. Never preserve the Jane observation as bookable once the destination source contradicts it.

## Privacy and security implications

1. **Do not cache full licence/registration identifiers more broadly than necessary.** CCHPBC's fraud warning shows that provider identifiers can have billing-abuse value.
2. **No credential replay for provider or patient systems.** Jane rejects credential-sharing integrations; TELUS eClaims uses authenticated provider/PMS workflows.
3. **Separate public discovery from member-specific eligibility.** R3 data should not require member IDs, plan IDs, or insurer credentials.
4. **Retain evidence hashes and timestamps, not unnecessary page snapshots containing personal information.**
5. **Terms authorization is a first-class control.** Technical reachability is not sufficient authority to ingest or automate.

## Architecture recommendation

Adopt a source-adapter registry with explicit policy metadata:

```text
SourceAdapterPolicy
  source_name
  supported_assertions[]
  authorization_mode             # PUBLIC, USER_DIRECTED, PARTNER, PROVIDER_AUTH, MEMBER_AUTH
  commercial_use_status          # ALLOWED, RESTRICTED, UNKNOWN
  automation_level               # READ_ONLY, DEEP_LINK, PARTNER_API, TRANSACTIONAL
  default_ttl_by_assertion
  negative_evidence_semantics
  sensitive_identifier_policy
```

The provider pipeline should then enforce:

`discover -> resolve identity -> check source authorization -> verify licensure -> observe payer participation -> observe fresh availability -> verify member-specific eligibility -> user approval -> booking adapter`

The **source authorization check belongs before data acquisition**, not after.

## Cross-lane handoffs

### To R2 — Insurer direct billing
- TELUS eClaims API is provider/PMS claims infrastructure, not evidence of an open discovery API.
- Direct billing participation should remain separate from member-specific coverage.
- Provider IDs/licence aliases can drift during 2026 regulator migrations.

### To R4 — Booking channels
- Jane currently supports a discovery-to-clinic-booking redirect flow and requires Jane ID for Practitioner Search.
- Jane's official integration posture currently does not support AI scheduling or direct calendar posting.
- Booking automation should therefore distinguish `DEEP_LINK_HANDOFF` from `TRANSACTIONAL_API`.

### To R5/R9 — Privacy/security
- CHCPBC/CCHPBC registries have explicit non-commercial-use language.
- CCHPBC warns registration-number misuse can enable fraudulent billing.
- R3 recommends masking/encrypting externally useful provider identifiers and treating terms authorization as a control.

### To R10 — Integration architecture
- Every adapter needs an authorization mode and terms status.
- TELUS API access is authenticated/provider-side and purpose-limited.
- Jane requires partnership approval and currently excludes AI scheduling.

## Unknowns / follow-up

1. Whether CHCPBC or CCHPBC will license or otherwise authorize machine-assisted verification for a member-directed commercial benefits product.
2. Whether Sun Life or Canada Life offer partner/provider-search APIs not publicly documented.
3. Whether Jane's stated exclusion of AI scheduling will change when its integration program launches more broadly.
4. Exact source-specific rate limits and machine-readable identifiers for public discovery products.
5. Province-by-province regulator terms and identifier stability outside BC.
6. Whether insurers expose a supported verification endpoint that can confirm provider eligibility without using member credentials.

## Recommendation to Manager-01

Classify the following as **SUPPORTED**:
- split provider truth into source-scoped observations;
- use an immutable internal provider ID plus versioned regulator aliases;
- treat Jane as discovery/deep-link rather than autonomous scheduling under current published integration posture;
- treat TELUS eClaims API as an authenticated claims/PMS integration, not a public provider-discovery API;
- add source authorization/terms posture and assertion-specific TTLs to the provider evidence model.

Classify the following as **ESCALATE_TO_PRIMARY / LEGAL-TERMS REVIEW**:
- any automated commercial ingestion of CHCPBC or CCHPBC registry data;
- any plan to scrape or reverse-engineer Jane, Sun Life, Canada Life, or TELUS interfaces in place of a supported integration;
- any design that stores or exposes full provider billing identifiers beyond the minimum required scope.
