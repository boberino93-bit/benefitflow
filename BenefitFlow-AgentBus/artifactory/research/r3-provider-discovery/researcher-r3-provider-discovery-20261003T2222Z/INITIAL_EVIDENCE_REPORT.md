# R3 Provider Discovery — Initial Evidence Report

**Project:** BenefitFlow (`project_id=benefitflow`)  
**Agent:** `researcher-r3-provider-discovery-20261003T2222Z`  
**Assignment:** R3 — provider discovery sources, data quality/freshness, identity resolution, location/service matching, and availability signals  
**Status:** INITIAL EVIDENCE PASS — proposal only, not accepted project truth  
**Evidence date:** 2026-10-03

## Executive finding

BenefitFlow should not model “provider verified” as one fact. The evidence ecosystem splits into at least four independently sourced assertions:

1. **Professional licensure / right to practise**
2. **Payer or direct-billing participation**
3. **Clinic/provider discovery metadata**
4. **Bookable availability**

Those assertions have different authorities, different update speeds, and different failure modes. A production design should preserve their provenance and timestamps separately and only combine them at decision time.

## F1 — Regulatory registries are the strongest source for professional identity and licence status

British Columbia now has two major consolidated regulatory sources relevant to common extended-health categories:

- **CHCPBC** regulates audiologists, dietitians, hearing instrument practitioners, occupational therapists, opticians, optometrists, physical therapists, psychologists, and speech-language pathologists, and exposes a Public Registry for licence verification.
- **CCHPBC** regulates chiropractors, massage therapists, naturopathic physicians, and traditional Chinese medicine practitioners/acupuncturists, and exposes a practitioner registry for current licence verification.

These registries should be treated as authoritative for licence/status questions, not for insurer eligibility, clinic availability, or plan coverage.

### Important source-use constraint

Both CHCPBC and CCHPBC state that public-registry information is not for commercial, marketing, or fundraising purposes. That does not by itself resolve whether BenefitFlow may automate verification for a member-directed benefits workflow. Automated ingestion, caching, or scraping therefore needs an explicit terms/licensing/legal review before production use.

## F2 — Provider identifiers are actively changing in BC during 2026

Identity resolution cannot assume a licence number is a permanent provider primary key.

- CHCPBC moved its regulated professions into a single database in June 2026 and assigned new seven-digit licence numbers. It states it is working with third-party payers to update numbers, and that licensees may need to update identifiers with some organizations.
- CCHPBC is also transitioning licence numbers by profession during 2026. Its registry notice states chiropractors changed June 17, naturopathic physicians September 1, TCM/acupuncture September 2, and massage therapists transition October 5, 2026, with transition completion expected by March 31, 2027.

### Implementation consequence

Use an internal immutable `provider_entity_id` and store regulator identifiers as versioned aliases:

- regulator
- profession
- licence_number
- valid_from
- valid_to
- source_observed_at
- replacement_identifier / supersedes

Identity matching should also include normalized name, profession, jurisdiction, and service-location evidence. Licence-number changes must not create duplicate provider entities.

## F3 — Direct-billing participation is not the same as member-specific coverage

### TELUS Health eClaims

TELUS Health exposes a public eClaims provider search and an insurer/profession eligibility matrix. It describes eClaims as direct billing and states:

- participation varies by insurer, profession, and province;
- individual plan details and professional licence issuer still matter;
- not every eClaims feature is supported by every participating insurer;
- the public provider finder can be used to find professionals who use eClaims.

This is strong evidence that a provider participates in the eClaims network, but not proof that a specific member’s plan will pay a specific service.

### Canada Life

Canada Life’s provider list explicitly says:

- listed providers **may** be eligible under a group benefits plan;
- claims are not guaranteed and remain subject to the plan’s rules;
- the list is not updated in real time;
- provider names and addresses are submitted by providers.

This source is useful for candidate discovery and payer-specific compatibility, but should not be used as a final eligibility guarantee.

### Pacific Blue Cross

Pacific Blue Cross states that members can use its Insta-Claim provider search to find participating direct-billing providers; for example, it added registered Clinical Counsellors in BC to direct billing in July 2025. This is payer-specific participation evidence, not universal coverage evidence.

### Implementation consequence

Do not use a single field such as `direct_billing = confirmed` without scope. Use a record keyed by:

- payer / network
- profession
- jurisdiction
- provider entity
- observed_at
- evidence URL/source
- participation status
- plan-specific verification status (separate)

## F4 — Availability is highly perishable and source-specific

### Jane

Jane’s Practitioner Search is currently described by Jane as a beta available in **B.C., Canada**, exposing real-time bookable openings for participating clinics. Patient search supports location and availability filters and currently covers chiropractic care, massage therapy, physiotherapy, and acupuncture. Jane’s normal online booking pages also expose clinic-controlled live appointment slots.

For clinics that opt in, Jane is a strong availability signal. It is not a complete provider directory because clinics can be absent if they have not opted in or do not use online booking.

### Sun Life Provider Search

Sun Life Provider Search can expose location, ratings, cost indicators, treatment filters, next-available appointment information, and direct booking for some providers. Its disclaimer is important:

- availability is informational and may not apply to every service/client type;
- provider-supplied extended-profile data is not fully validated;
- search results may not include every suitable provider;
- cost indicators are based on Sun Life claims and may not reflect current price.

### Implementation consequence

Availability should be represented as an observation, not a durable provider attribute:

- source
- service/treatment
- practitioner
- location
- earliest_slot / slot set
- observed_at
- expires_at / freshness policy
- booking_url
- source confidence

BenefitFlow should re-check live availability immediately before presenting or executing a booking action.

## F5 — Absence from a directory is not reliable negative evidence

TELUS Health’s public eClaims finder states that identifying information for mental-health professionals is removed because of the nature of their practice. Jane results can omit clinics that have not opted in to Practitioner Search or have not enabled online booking. Sun Life also states its search may not contain all suitable providers.

Therefore:

> `not_found_in_source` must not be normalized to `provider_not_eligible` or `provider_does_not_exist`.

A negative source observation needs a reason category such as `not_listed`, `privacy_suppressed`, `source_scope_excluded`, `not_opted_in`, or `unknown`.

## F6 — Current Beta model is too coarse for production provider verification

Current code inspection:

- `Provider` stores only `provider_id`, `name`, `category`, `city`, `phone`, `booking_channel`, and `synthetic`.
- `ProviderVerification` stores `insurer_name`, accepting-new-patients, current price, a three-state direct-billing value, required profile fields, referral/prescription flags, cancellation policy, `verified_at`, and a free-text evidence note.
- `simulate_verification()` marks direct billing as confirmed whenever an insurer name is supplied, which is explicitly synthetic and should not shape the production trust model.

### Recommended model split

Introduce separate concepts instead of expanding one verification object indefinitely:

**ProviderEntity**
- immutable internal ID
- canonical name
- profession/category
- regulator identities / aliases

**ServiceLocation**
- normalized address
- phone/site
- clinic affiliation
- geo coordinates
- source observations

**LicensureObservation**
- regulator
- licence number/status
- profession/jurisdiction
- observed_at
- source

**PayerParticipationObservation**
- payer/network
- profession
- jurisdiction
- direct-billing/eClaims participation
- observed_at
- source

**AvailabilityObservation**
- treatment/service
- practitioner/location
- slot(s) or earliest availability
- observed_at / expiry
- booking channel/source

**MemberEligibilityVerification**
- plan-scoped result
- service/provider restrictions
- prior authorization/referral rules
- verification timestamp
- evidence
- must remain separate from public discovery data

## Initial source confidence matrix

| Source | Strongest use | Main limitation | Suggested trust |
|---|---|---|---|
| CHCPBC Public Registry | licence/status for 9 regulated BC professions | terms/use restrictions; no booking/payer data | High for licensure |
| CCHPBC Registry | licence/status for complementary professions | identifier transition; terms/use restrictions | High for licensure |
| TELUS Health eClaims | eClaims participation and payer/profession matrix | not member-plan guarantee; public privacy suppression for some providers | High for network participation, lower for plan coverage |
| Canada Life provider list | Canada Life candidate/provider eligibility signal | not real time; claims not guaranteed; provider-submitted name/address | Medium |
| Pacific Blue Cross Insta-Claim | PBC direct-billing participation | payer-specific, not universal plan guarantee | High for PBC participation |
| Sun Life Provider Search | discovery, cost/ratings, some availability/booking | extended profiles not fully validated; availability informational | Medium, field-specific |
| Jane Practitioner Search | real-time bookable openings at opted-in BC clinics | beta, limited disciplines, incomplete universe | High for current Jane availability, low for completeness |

## Architecture recommendation

BenefitFlow’s provider pipeline should be evidence-fusion, not directory-import:

`candidate discovery -> identity resolution -> regulatory verification -> payer/network participation check -> clinic/service match -> fresh availability observation -> plan-specific verification -> user approval -> transaction adapter`

Every step should retain source, timestamp, jurisdiction, and confidence. A later source should not overwrite an earlier observation; it should supersede or contradict it explicitly.

## Immediate follow-up research

1. Review source terms/API or licensed-access options before any automated registry/directory ingestion.
2. Build a province-by-profession regulator crosswalk beyond BC.
3. Build a test fixture for the 2026 CHCPBC/CCHPBC licence-number migrations to prove identity aliases prevent duplicates.
4. Determine source-specific freshness/TTL policies; Canada Life explicitly says its list is not real-time, while Jane exposes live booking availability.
5. Investigate structured access/integration options for Jane, TELUS eClaims, Sun Life, and insurer directories without using member credentials.
6. Define contradiction rules when regulator status, payer directory status, provider self-report, and booking data disagree.

## Sources consulted

- CHCPBC — https://chcpbc.org/
- CHCPBC public information — https://chcpbc.org/public/
- CHCPBC licence-number migration notice — https://chcpbc.org/2026/07/06/new-seven-digit-licensee-numbers-for-all-health-professionals-regulated-by-chcpbc/
- CCHPBC practitioner registry — https://cchpbc.ca/public/practitioner-search/
- CCHPBC public information — https://cchpbc.ca/public/
- TELUS Health eClaims provider finder — https://plus.telushealth.co/page/eclaims/discover/
- TELUS Health insurer eligibility by profession — https://plus.telushealth.co/page/eclaims/help/insurer_coverage_html/
- Canada Life eligible provider search — https://www.canadalife.com/insurance/workplace-benefits/eclaims-provider-listing.html
- Pacific Blue Cross provider news / Insta-Claim — https://pac.bluecross.ca/providerresource/provider-news/direct-billing-for-mental-health-providers-in-bc-starting-july-11/
- Sun Life Provider Search — https://providersearch.sunlife.ca/en/
- Jane Practitioner Search guide — https://jane.app/guide/practitioner-search-for-patients
- Jane Practitioner Search clinic hub — https://jane.app/guide/practitioner-search-for-clinics
- Jane online booking guide — https://jane.app/guide/booking-an-appointment-online-for-patients

## Research disposition

`SUPPORTED_INITIAL`: The source separation, identity-alias requirement, and freshness model are supported by current authoritative/provider documentation. Exact automation rights, API access, caching permissions, and cross-Canada coverage remain unresolved and should not be inferred.
