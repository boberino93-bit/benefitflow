# R6 Research Report — Voice and Phone Transaction Workflow

Project: BenefitFlow  
Assignment: R6 — Voice and Phone Transaction Workflow  
Prepared lane: `voice-transaction-workflow`  
Researcher: `researcher-r6-voice-phone-8a7f`  
Status: SPECIALIST EVIDENCE — NOT ACCEPTED PROJECT STATE  
Retrieval date: 2026-10-03

## 1. Scope and boundary

This report addresses phone/voice booking workflows, identity-disclosure sequencing, recording/consent considerations at a product-design level, verification prompts, bounded transaction authorization, confirmation capture, and failure/escalation conditions.

It does **not** establish legal compliance for every jurisdiction, select a production telephony vendor, authorize recording, decide authentication architecture, or implement an external transaction adapter. Privacy/legal applicability belongs to R5/qualified review; identity/security controls overlap R9; adapter implementation overlaps R10.

Research uses only public documentation and the synthetic/public BenefitFlow beta repository. No member identifiers, plan identifiers, credentials, claim data, or private health information were used.

## 2. Observed evidence

### E1 — BenefitFlow already enforces a useful transaction boundary

**Source:** `benefitflow_beta/workflow.py` in `boberino93-bit/benefitflow`  
**Source type:** first-party project implementation  
**Applicability:** BenefitFlow beta  
**Observed evidence:** After user approval, the beta generates a transaction script that:
- identifies itself as an automated scheduling assistant acting with member approval;
- instructs the adapter to reconfirm clinic need before disclosing identifiers;
- limits identifier exposure to the approved stored values;
- requires fresh user approval if provider, practitioner, service, price, cancellation condition, or appointment window materially changes;
- forbids deposit payment or claim submission without separate authorization.

**Confidence:** high for current beta behavior.  
**Implementation consequence:** preserve these boundaries when a live voice adapter is introduced; make them machine-enforced state transitions rather than script text alone.

### E2 — The current beta does not yet represent voice-call or booking-outcome state

**Source:** `benefitflow_beta/models.py` and `benefitflow_beta/workflow.py`  
**Source type:** first-party project implementation  
**Applicability:** BenefitFlow beta  
**Observed evidence:** `BookingResult` currently ends at `READY_FOR_TRANSACTION_ADAPTER` or `DECLINED`. There are no first-class states for dialing, ringing, human/IVR answer, counterparty verification, disclosure authorization, pending request, confirmed appointment, ambiguous outcome, retry, or manual reconciliation.

**Confidence:** high.  
**Implementation consequence:** production voice work needs a transaction/call state model separate from the current proposal-approval state.

### E3 — A telephony provider's “completed” call status is not evidence of a successful booking

**Source:** Twilio, “Call resource”  
**URL:** https://www.twilio.com/docs/voice/api/call-resource  
**Source type:** first-party vendor technical documentation  
**Freshness:** live technical documentation retrieved 2026-10-03  
**Applicability:** Twilio specifically; concept generalizes to telephony transports  
**Observed evidence:** Twilio exposes transport states such as queued, ringing, in-progress, completed, busy, failed, no-answer, and canceled. Twilio explicitly warns that a “completed” call only means a connection was established and audio transferred; the answer could have been a person, IVR, or voicemail.

**Confidence:** high for Twilio.  
**Known limitation:** vendor-specific state names are not a universal standard.  
**Implementation consequence:** BenefitFlow must keep **telephony transport state** separate from **business transaction outcome**. Never map `call.completed` to `booking.confirmed`.

### E4 — Event callbacks can provide durable transport evidence

**Source:** Twilio, “Call resource” / Voice status callback documentation  
**URL:** https://www.twilio.com/docs/voice/api/call-resource  
**Source type:** first-party vendor technical documentation  
**Freshness:** retrieved 2026-10-03  
**Observed evidence:** outbound calls can emit initiated/ringing/answered/completed progress callbacks with a unique call identifier and terminal status information.

**Confidence:** high for Twilio.  
**Implementation consequence:** a production adapter should persist provider event IDs/timestamps and normalize them to BenefitFlow transport events, but business success still requires independent structured confirmation evidence.

### E5 — Recording creates additional privacy obligations; notice, purpose, consent, safeguards, and retention matter

**Source:** Office of the Privacy Commissioner of Canada, “Recording of Customer Telephone Calls”  
**URL:** https://www.priv.gc.ca/en/privacy-topics/surveillance/02_05_d_14/  
**Source type:** official regulator guidance  
**Date modified:** 2018-03-06  
**Retrieval date:** 2026-10-03  
**Jurisdiction:** Canada / PIPEDA organizations; page also describes the guidelines as best practices for others not subject to PIPEDA  
**Observed evidence:** the OPC says recordings collect personal information; organizations subject to PIPEDA should inform the customer that the call is recorded, state the purpose, ask for consent, use information only for stated purposes, apply safeguards, and limit retention. The page notes customers may object and seek an alternative channel.

**Confidence:** high for the stated federal guidance.  
**Known limitation:** this does not resolve all provincial, sector-specific, cross-border, or counterparty-specific rules, and the page was modified in 2018.  
**Implementation consequence:** BenefitFlow should default to **no call recording unless a defined purpose requires it**. If recording/transcription is introduced, it should be behind a jurisdiction-aware policy gate and qualified privacy/legal review, with explicit notice/purpose/consent and retention controls.

### E6 — Benefit/health-related identifiers should be treated conservatively as sensitive data

**Source:** Office of the Privacy Commissioner of Canada, “PIPEDA Fair Information Principle 3 — Consent”  
**URL:** https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/p_principle/principles/p_consent/  
**Source type:** official regulator guidance  
**Retrieval date:** 2026-10-03  
**Jurisdiction:** Canada / PIPEDA  
**Observed evidence:** the OPC states meaningful consent is generally required for collection, use, and disclosure of personal information and says express consent is generally appropriate for sensitive information. It also emphasizes necessity, stated purpose, reasonable expectations, and consequences.

**Confidence:** high for the stated federal guidance.  
**Implementation consequence:** the approval object should explicitly enumerate what fields may be disclosed, to whom, for what purpose, and under what conditions. Full values should not appear in ordinary research logs or general call audit logs.

### E7 — Data minimization is a design requirement, not just a privacy notice issue

**Source:** Office of the Privacy Commissioner of Canada, PIPEDA limiting-collection guidance / self-assessment material  
**URL:** https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/pipeda-compliance-help/pipeda-compliance-and-training-tools/pipeda_sa_tool_200807  
**Source type:** official regulator guidance  
**Retrieval date:** 2026-10-03  
**Jurisdiction:** Canada / PIPEDA  
**Observed evidence:** collection should be limited to what is necessary for identified purposes.

**Confidence:** high for the stated principle.  
**Implementation consequence:** a voice adapter should ask the clinic which fields are actually required before disclosing approved identifiers and should log field *categories/purposes*, not duplicate the raw values into transcripts or telemetry.

## 3. Interpretation

The beta's current script contains the right safety intent but leaves too much enforcement to a future voice agent's prompt-following behavior. Production safety should move critical boundaries into deterministic orchestration:

1. **Approval is a capability grant, not a blanket permission.**
2. **Connection is not identity verification.**
3. **Identity verification is not permission to disclose everything.**
4. **Transport completion is not booking confirmation.**
5. **A materially changed offer invalidates the current booking authority.**
6. **An ambiguous end state is not permission to retry blindly.**
7. **Recording/transcription is optional processing with its own consent/purpose/retention policy, not a prerequisite for auditability.**

## 4. Recommended call/transaction state model

Use two orthogonal state dimensions:

### A. Telephony transport state

`NOT_STARTED`
→ `QUEUED`
→ `DIALING`
→ `RINGING`
→ `ANSWERED`
→ `ENDED`

Terminal transport reasons:
- `COMPLETED_CONNECTION`
- `BUSY`
- `NO_ANSWER`
- `FAILED`
- `CANCELED`

Transport events must never directly set booking outcome.

### B. BenefitFlow transaction state

1. `APPROVAL_SNAPSHOT_READY`
   - Immutable snapshot of approved provider/practitioner constraints, service, window, price/cost bounds, cancellation constraints, allowed disclosures, and prohibited actions.
2. `COUNTERPARTY_UNVERIFIED`
   - Call may be connected, but no sensitive member/plan fields are disclosed.
3. `COUNTERPARTY_VERIFIED`
   - Clinic/practice identity and intended service/practitioner context match the approval snapshot.
4. `DISCLOSURE_NEED_CONFIRMED`
   - Clinic states which approved fields are needed and for what purpose.
5. `DISCLOSURE_AUTHORIZED`
   - Orchestrator confirms requested fields are within the user's approval and minimization policy.
6. `NEGOTIATING_WITHIN_SCOPE`
   - Agent can discuss approved window/price/service without widening authority.
7. `REAPPROVAL_REQUIRED`
   - Triggered by any material variation: different provider/practitioner/service; price beyond approved bound; materially different cancellation/no-show term; different appointment window outside approved tolerance; deposit/payment; claim submission; new sensitive-data category.
8. `BOOKING_REQUESTED_PENDING`
   - Clinic has accepted a request but has not provided durable confirmation.
9. `BOOKING_CONFIRMED`
   - Only after required confirmation fields are captured and internally validated.
10. `ENDED_UNCONFIRMED`
   - Call ended normally but no booking confirmation exists.
11. `AMBIGUOUS_OUTCOME`
   - Disconnect/failure occurred after a point where the clinic might have created a booking but confirmation is incomplete.
12. `MANUAL_RECONCILIATION_REQUIRED`
   - Used before any retry that could create a duplicate appointment.
13. `FAILED_RETRYABLE`
   - e.g., busy/no-answer before any business-side booking action.
14. `FAILED_TERMINAL`
   - e.g., wrong business, provider unavailable with no approved alternative, clinic refuses interaction.
15. `CANCELED_BY_USER`.

## 5. Sensitive-data disclosure gates

### Gate 0 — User authorization before dialing
Required:
- exact purpose;
- target clinic/provider;
- service/category;
- appointment constraints;
- approved price/cost tolerance;
- explicit list of disclosure categories allowed;
- explicit prohibited actions (payment, claim submission, materially different service, etc.);
- authorization expiry/version.

Recommendation: replace the current implicit ability to access stored `plan_number` and `member_id` with an `allowed_disclosures[]` capability list.

### Gate 1 — Counterparty verification before sensitive disclosure
The agent should first identify itself and purpose at a non-sensitive level, then verify the organization/clinic and relevant practitioner/service context.

Do not treat caller ID, an answered phone, IVR traversal, or a human saying “hello” as sufficient identity proof.

### Gate 2 — Necessity/purpose check
Ask what information is required for:
- appointment creation;
- direct-billing profile setup;
- insurer verification;
- another specific task.

Only fields both **requested for a legitimate task** and **already approved by the user** may proceed.

### Gate 3 — Recording/transcription policy
If BenefitFlow records or retains a transcript:
- determine jurisdiction/policy applicability before starting;
- provide required notice and purpose;
- capture consent state;
- offer/follow a no-recording alternative where required/appropriate;
- apply retention and access controls.

Product-safe default pending R5/qualified review: **do not retain raw audio**. Prefer structured event/audit data and minimal derived notes.

### Gate 4 — Material-change guard
Any out-of-scope change moves to `REAPPROVAL_REQUIRED`. The voice agent must be unable to “talk its way around” this state through prompt interpretation.

### Gate 5 — Confirmation capture
A booking is not confirmed until BenefitFlow has, where applicable:
- provider/clinic;
- practitioner or service identity;
- date;
- start time and timezone/locality;
- location or modality;
- expected price/amount due if supplied;
- cancellation/no-show terms if material;
- clinic confirmation/reference number if available;
- whether the clinic described the appointment as confirmed vs requested/waitlisted/pending;
- confirmation channel promised (SMS/email/portal) when applicable.

## 6. Failure and escalation conditions

### Stop before disclosure
- wrong number or clinic identity mismatch;
- target practitioner/service cannot be reconfirmed;
- call routes to voicemail/unknown third party;
- clinic asks for data beyond user-approved categories;
- agent cannot determine why a sensitive field is needed.

### Fresh user approval required
- different provider or practitioner where practitioner identity was material;
- different service/category;
- price exceeds approved bound;
- materially different cancellation/no-show condition;
- appointment time outside approved tolerance;
- deposit, card details, or other payment request;
- claim submission or insurer action not separately authorized;
- additional sensitive-data category.

### Manual reconciliation before retry
- line drops after clinic says it created/held/booked an appointment;
- confirmation ID/details are incomplete after apparent booking;
- duplicate possibility exists;
- clinic will call back from another number and identity cannot be safely bound to the existing transaction.

### Retryable without manual reconciliation
Only when no business-side action could reasonably have occurred, e.g.:
- busy;
- no answer;
- failed to connect;
- canceled before answer.

Retry policy should be bounded by attempt count, cooldown, user preferences, and clinic hours. It should not produce repeated nuisance calls.

## 7. Idempotency and duplicate-booking protection

Use:
- a stable `transaction_id` for the user-approved booking intent;
- a unique `attempt_id` for each call;
- telephony provider call ID as transport evidence, not the primary business key;
- monotonic state transitions;
- an `ambiguous_outcome` lock that blocks automatic redial until reconciliation;
- a confirmation fingerprint composed from provider/service/date/time/location (plus provider confirmation reference when available);
- deduplication checks before any retry following a partially completed interaction.

Critical rule: **retry the transport, not the business transaction**. After any evidence the clinic may have acted, reconcile first.

## 8. Required audit evidence for a completed transaction

Minimum structured audit record:

### Authorization evidence
- proposal ID;
- approval snapshot ID/version/hash;
- approval timestamp;
- authorization expiry if used;
- approved fields/categories, without duplicating raw sensitive values;
- prohibited-action set.

### Provider/verification evidence
- provider/clinic ID;
- provider verification record version and timestamp;
- phone-number source/provenance;
- service/practitioner constraints.

### Call evidence
- transaction ID;
- attempt ID;
- telephony provider call/event ID;
- transport-state timestamps;
- whether automated-assistant disclosure occurred;
- counterparty-verification result;
- recording/transcription mode and consent-policy result, if applicable.

### Disclosure evidence
- field categories disclosed (for example `member_id`, `plan_number`) rather than raw values in general logs;
- purpose for each disclosure;
- recipient organization/context;
- disclosure timestamp.

### Outcome evidence
- booking state;
- appointment details;
- confirmation/reference ID if provided;
- any pending/waitlist status;
- material cancellation/no-show terms;
- any deviations and whether fresh user approval was obtained;
- terminal reason;
- manual-reconciliation flag.

### Data that should not be copied into ordinary audit logs
- full member/certificate identifiers;
- full plan numbers;
- payment credentials;
- unnecessary medical details;
- raw audio/transcripts by default.

## 9. Product/model changes recommended for manager review

### M1 — Introduce first-class transaction models
Suggested conceptual models:
- `BookingAuthorizationSnapshot`
- `VoiceTransaction`
- `CallAttempt`
- `DisclosureDecision`
- `BookingConfirmation`

### M2 — Separate provider/transport/business outcomes
Do not overload `BookingResult.status`. Keep:
- proposal/authorization status;
- transport/call status;
- transaction/business status;
- confirmation status.

### M3 — Make allowed disclosures explicit
Current workflow stores plan/member IDs and relies on script instructions. Add explicit:
- `allowed_disclosure_fields`
- `allowed_disclosure_purposes`
- `disclosure_expiry`
- `requires_reapproval_if_changed`

### M4 — Add a deterministic reapproval barrier
The transaction adapter should emit a structured `REAPPROVAL_REQUIRED` event with the proposed deviation and stop. The conversational model should not be able to override this barrier.

### M5 — Default to structured audit evidence, not raw call recording
A robust audit trail can be built from signed/validated state events and confirmation facts. Recording should be optional, justified, jurisdiction-aware, access-controlled, and retention-limited.

### M6 — Add ambiguity-safe retry logic
No automatic redial after an outcome becomes ambiguous. Require status reconciliation or human review first.

## 10. Recommended tests

1. **IVR answered:** transport becomes answered/completed, business state remains unverified/unconfirmed.
2. **Voicemail answered:** no sensitive disclosure; no booking success.
3. **Wrong clinic:** stop before disclosure.
4. **Correct clinic, identifiers not required:** do not disclose them.
5. **Correct clinic requests member ID for a stated direct-billing profile purpose:** disclose only if user approval permits.
6. **Clinic asks for DOB/diagnosis not in allowed fields:** refuse/escalate.
7. **Price rises above approved bound:** enter `REAPPROVAL_REQUIRED`.
8. **Different practitioner offered:** reapproval according to approval-card semantics.
9. **Different time outside approved window:** reapproval.
10. **Deposit requested:** stop and require separate authorization/payment pathway.
11. **Call drops before any booking action:** retry may be allowed.
12. **Call drops immediately after “I booked that for you”:** set ambiguous outcome; no automatic retry.
13. **Clinic says request submitted but pending confirmation:** `BOOKING_REQUESTED_PENDING`, not confirmed.
14. **Telephony status is completed but only IVR was reached:** no booking confirmation.
15. **Recording enabled without policy/consent result:** fail closed before recording.
16. **Recording declined:** follow configured non-recording path rather than coercing consent.
17. **Transfer to another department:** maintain organization context but re-check purpose/need before additional sensitive disclosure.
18. **Incoming callback:** do not trust caller ID alone; bind through the future R9/R10 security/transaction protocol before disclosure.
19. **Duplicate retry after ambiguous outcome:** blocked.
20. **Audit-log inspection:** full sensitive identifiers absent from general logs.

## 11. Contradictions, limitations, and unknowns

- **Jurisdiction is unresolved.** Canadian PIPEDA guidance is useful because BenefitFlow is being researched in a Canadian context, but production applicability may vary by province, country, user location, clinic location, and corporate structure. R5/qualified legal review must resolve this.
- **Recording rules are not fully established here.** This report intentionally avoids claiming that one consent mechanism is universally sufficient.
- **Telephony vendor is not selected.** Twilio is used as a concrete current technical example, not a vendor recommendation.
- **Clinic identity-proofing standard is unresolved.** R9 should define a stronger trust model, especially for callbacks, forwarded calls, or number changes.
- **Booking confirmation semantics depend on R4.** R6 recommends separation of transport and business outcome but does not override R4's booking taxonomy.
- **Adapter/event security depends on R10/R9.** Webhook signature verification, secret isolation, event ordering, and replay defense belong primarily there.
- **Direct billing remains non-final.** A clinic saying it direct-bills does not establish final benefit eligibility or insurer payment; R2 owns that evidence.

## 12. What the evidence does NOT establish

This report does not establish:
- that BenefitFlow may lawfully record every call;
- that an AI/automated assistant may place every type of call in every jurisdiction;
- that a telephony provider's `completed` status proves a human answered;
- that a successful conversation proves an appointment exists;
- that clinic direct billing guarantees insurer reimbursement;
- that caller ID alone proves clinic identity;
- that current beta storage of sensitive identifiers is production-ready;
- that the recommendations have been accepted into BenefitFlow architecture.

## 13. Manager review recommendations

Recommended manager dispositions:
- **SUPPORTED:** separate telephony transport state from booking outcome.
- **SUPPORTED:** preserve and harden the current fresh-approval boundary for material changes.
- **SUPPORTED:** require counterparty verification and purpose/necessity check before sensitive disclosure.
- **SUPPORTED_WITH_LIMITS:** explicit recording notice/consent/retention controls; jurisdiction-specific applicability requires R5/qualified review.
- **SUPPORTED:** ambiguous post-action disconnect must block blind retry and route to reconciliation.
- **SUPPORTED:** structured audit evidence should be sufficient for routine transaction accountability without default raw-audio retention.
- **ESCALATE_TO_PRIMARY:** exact approval-card fields/tolerances and production retention policy.
- **REQUIRES_HUMAN_OR_QUALIFIED_REVIEW:** jurisdiction-specific privacy/recording legality.

Primary acceptance is still required before any recommendation changes accepted project state.
