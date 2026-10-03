# BenefitFlow R9 — Initial Identity, Authentication, Account Security, and Auditability Findings

**Agent:** `researcher-r9-identity-security-20261003T2222Z`  
**Assignment:** R9  
**Project:** BenefitFlow (`project_id=benefitflow`)  
**Repository:** `boberino93-bit/benefitflow`  
**Status:** Initial evidence package for Manager/Primary review; not accepted project state.

## Scope

Identity, authentication, account security, hosted-data architecture, auditability, and least-privilege access boundaries. Privacy-law interpretation, consent/retention law, and data-subject rights are intentionally left to R5 except where they directly constrain security architecture.

## Executive finding

The current beta is appropriately described as a local/synthetic prototype, but its runtime security model must not be carried forward into a hosted or production service. The present API has no visible user authentication/session layer, no account/tenant ownership fields on booking proposals, no object-level authorization check on proposal approval, plaintext persistence of full plan/member identifiers in SQLite, and no application security/audit event model.

The highest-priority production hardening requirement is therefore **not merely “add login.”** BenefitFlow needs a coherent identity boundary that binds every sensitive object and action to an authenticated principal, enforces authorization on every access, separates sensitive identifiers from ordinary application state, and creates an attributable approval/audit trail before any transaction adapter is allowed to act.

## Current-beta observations

### BF-R9-01 — Runtime API has no visible authentication/authorization dependency

`benefitflow_beta/app.py` exposes parsing, planning, provider verification, proposal creation, and proposal approval endpoints directly. The route definitions do not show an authentication middleware/dependency, authenticated subject, account context, or authorization policy check.

**Implementation consequence:** In a hosted deployment, every endpoint that handles user plans, provider workflow state, proposals, or approvals must run under an authenticated account/session context unless explicitly classified as public. Public health/static endpoints should be isolated from authenticated application APIs.

**Disposition:** `SUPPORTED` by repository inspection.

### BF-R9-02 — Proposal approval is vulnerable by design to object-reference authorization failure if deployed as-is

`BookingApprovalRequest` contains only `proposal_id` and `approved`. `approve_proposal()` fetches `proposal:{proposal_id}` and proceeds if the record exists. There is no owner/account/tenant identity on `BookingProposal` or the stored record and no check that the caller owns or is entitled to approve that proposal.

The proposal ID is generated with `secrets.token_urlsafe(8)`, which improves unpredictability but does **not** constitute authorization. OWASP API1:2023 states that object-level authorization checks are required when APIs use object identifiers; manipulating an object ID is a common path to unauthorized access.

**Implementation consequence:** Add immutable `account_id`/subject ownership to user-owned objects and enforce ownership/entitlement server-side on **every** read/change/action. Deny by default. Do not rely on UUID/random-ID secrecy.

**Disposition:** `SUPPORTED`; **production blocker**.

### BF-R9-03 — Full member and plan identifiers are persisted in plaintext application state

`create_proposal()` stores the masked values in the outward proposal but also persists the full `plan_number` and `member_id` inside a JSON `sensitive` object. `storage.py` serializes this JSON directly into a local SQLite database without application-layer encryption.

OWASP Cryptographic Storage guidance recommends minimizing storage of sensitive information first; where sensitive data must be retained, encryption and separate key management should follow the threat model.

**Implementation consequence:** Prefer not to persist these identifiers until the minimum point at which an approved transaction requires them. If persistence is necessary, separate them from normal proposal state into a dedicated sensitive-data vault/store, encrypt at the application layer or with an equivalent managed data-protection control, use a dedicated KMS/key vault, and return only opaque references plus masked display values to ordinary workflow code.

**Disposition:** `SUPPORTED`; **production blocker for hosted member data**.

### BF-R9-04 — Approval is not yet an attributable, single-use security event

The approval function accepts a boolean against a proposal ID and returns `READY_FOR_TRANSACTION_ADAPTER`. There is no authenticated approver identity, authentication age, step-up/re-authentication evidence, approval timestamp, expiry, single-use nonce, state transition lock, or immutable record of the exact terms approved.

**Implementation consequence:** A production approval record should bind at minimum: authenticated subject, proposal ID, exact material-terms digest/version, approval decision, timestamp, authentication/session context, expiry, and one-time transaction authorization state. Material change to provider/practitioner/service/price/window/cancellation terms must invalidate the prior approval and require a fresh approval.

**Disposition:** `SUPPORTED`; high priority.

### BF-R9-05 — No application security/audit event model is visible

The beta storage layer contains only a generic key/value table. The reviewed runtime modules do not define an attributable audit stream for authentication, authorization decisions, sensitive-record access, provider verification, proposal creation, approval, adapter handoff, or privileged actions.

OWASP recommends logging authentication successes/failures, authorization failures, access to sensitive data, higher-risk functionality, imports/uploads, and suspicious workflow bypass attempts, while avoiding unnecessary sensitive information in logs and protecting logs from tampering.

**Implementation consequence:** Build a separate append-oriented audit/security event stream with actor, action, resource, result, reason, timestamp, correlation/transaction ID, and policy/authorization decision metadata. Never log raw plan/member IDs, authentication secrets, tokens, or unnecessary uploaded-plan content. Protect log access and integrity separately from ordinary application state.

**Disposition:** `SUPPORTED`.

### BF-R9-06 — Project/repository guard is not a runtime user-access control

`project_guard.py` correctly protects project/repository write intent for the multi-agent development environment. It does not authenticate BenefitFlow end users or authorize runtime access to benefit data and booking objects.

**Implementation consequence:** Preserve the project guard, but do not treat it as part of the production IAM boundary. Development-agent authorization and product-user authorization are separate trust domains.

**Disposition:** `SUPPORTED`.

## External evidence and current standards

### E1 — NIST SP 800-63-4 / SP 800-63B-4 (final July 2025)

NIST Revision 4 is the current Digital Identity Guidelines suite. SP 800-63B-4 defines AAL2 as multi-factor authentication with approved cryptography, requires replay resistance, and requires verifiers to offer at least one phishing-resistant option. It identifies WebAuthn/FIDO2 as an example of phishing-resistant verifier-name binding.

Sources:
- NIST SP 800-63-4: https://csrc.nist.gov/pubs/sp/800/63/4/final
- NIST SP 800-63B-4: https://pages.nist.gov/800-63-4/sp800-63b.html

**BenefitFlow implication:** Do not invent a bespoke credential system. Prefer a mature identity provider and make passkeys/WebAuthn a first-class authentication/step-up option. A formal assurance-level determination should be risk-driven; this report does not claim BenefitFlow is required to meet a federal AAL.

### E2 — RFC 9700, OAuth 2.0 Security Best Current Practice (January 2025)

RFC 9700 is the current OAuth 2.0 security BCP. It requires modern defenses for redirect-based authorization flows and requires PKCE for public clients, while recommending additional replay defenses and protected channels.

Source: https://www.rfc-editor.org/rfc/rfc9700.html

**BenefitFlow implication:** If BenefitFlow uses OIDC/OAuth for sign-in or delegated API access, use Authorization Code flow with the applicable RFC 9700 protections, including PKCE where required. Avoid legacy OAuth anti-patterns and avoid exposing bearer credentials to browser storage when a server-side/BFF session design can keep them out of JavaScript.

### E3 — OWASP API Security Top 10 2023, API1 Broken Object Level Authorization

OWASP identifies object-level authorization as a leading API risk and requires authorization checks for functions that access data by user-supplied object IDs.

Source: https://api-security.owasp.org/editions/2023/en/0xa1-broken-object-level-authorization/

**BenefitFlow implication:** `proposal_id`, plan IDs, verification IDs, booking IDs, document IDs, and any future claim/transaction IDs must be treated as references, not capabilities. Every access must be authorized against the authenticated principal and current policy.

### E4 — OWASP Authorization Cheat Sheet

OWASP recommends deny-by-default authorization, server-side enforcement, permission validation on every request, and explicit testing of authorization logic.

Source: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html

**BenefitFlow implication:** Centralize policy logic, keep enforcement close to protected resources, and add negative authorization tests covering cross-account object access and workflow-state bypass.

### E5 — OWASP Cryptographic Storage and Key Management guidance

OWASP recommends minimizing storage of sensitive data, selecting encryption placement based on a threat model, and using dedicated key-management services where available. Keys should be separated from encrypted data and not committed to source/build artifacts.

Sources:
- https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html

**BenefitFlow implication:** Split identifiers/credentials/secrets from general workflow state, encrypt sensitive values when retained, and keep encryption keys in a managed vault/KMS rather than alongside application data.

### E6 — NIST SP 800-207 / 800-207A Zero Trust

NIST zero-trust guidance removes implicit trust based on network location and emphasizes authentication/authorization around identities and protected resources; SP 800-207A extends this to application/service identities in cloud-native environments.

Sources:
- https://www.nist.gov/publications/zero-trust-architecture
- https://csrc.nist.gov/pubs/sp/800/207/a/final

**BenefitFlow implication:** Human user identity is only one boundary. Background workers, provider-verification services, transaction adapters, and research/automation components should also have distinct service identities and least-privilege permissions. A booking adapter should not inherit broad read access to unrelated user records merely because it runs inside the same environment.

## Recommended production identity/security architecture

1. **Identity provider, not home-grown credentials.** Use OIDC with a mature IdP. Prefer phishing-resistant passkeys/WebAuthn; support appropriately strong recovery and MFA. Treat staff/admin identities separately from end-user accounts.
2. **Server-side authenticated session/BFF for the web app.** Keep browser-visible session material minimal. If cookies are used, use HTTPS plus `Secure`, `HttpOnly`, appropriate `SameSite`, CSRF protections, session rotation, idle/absolute timeouts, and explicit logout/revocation.
3. **Per-object ownership and authorization.** Every user-owned record gets an immutable account/subject boundary. Enforce authorization on every object operation; deny by default; test cross-user access as a first-class security suite.
4. **Sensitive identifier vault.** Ordinary proposal/plan tables hold masked values and opaque vault references. Full member/plan identifiers are retained only when justified, encrypted, and released only to narrowly authorized transaction components.
5. **Bounded transaction authorization.** Convert user approval into a signed/immutable authorization record tied to subject + exact proposal terms + expiry + one-time adapter scope. Never let a boolean alone become the durable authority to disclose identifiers or transact.
6. **Step-up for sensitive external action.** If the authentication is stale or the action will disclose member identifiers / create a booking, require a recent stronger authentication/reauthentication according to a risk policy. Prefer phishing-resistant methods.
7. **Service identity and least privilege.** Provider research, verification, booking adapters, calendar integrations, and support/admin tooling receive separate service principals/scopes. Research services do not receive member identifiers. Transaction adapters receive only the minimum approved payload and duration.
8. **Append-oriented audit trail.** Record security and high-value business events separately from ordinary logs, with tamper detection/centralization. Do not put raw plan/member identifiers or tokens in logs.
9. **Secrets and key management.** Use managed secrets/KMS, rotation, environment separation, and no credentials in source or repository artifacts.
10. **Authorization and abuse tests before live adapters.** Add tests for unauthenticated access, cross-account proposal access, replayed approvals, expired approval, changed terms after approval, privilege changes, stolen/old sessions, and adapter overreach.

## Proposed minimal object model additions

The following is architectural guidance, not an accepted schema change:

- `Account`: `account_id`, external IdP subject, status, assurance/auth policy metadata.
- User-owned records: immutable `account_id` / tenant boundary.
- `ApprovalRecord`: `approval_id`, `account_id`, `proposal_id`, `terms_digest`, `decision`, `approved_at`, `expires_at`, `auth_time`, `auth_context`, `used_at`, `revoked_at`.
- `SensitiveIdentifierRef`: opaque reference to separately encrypted/vaulted plan/member data; ordinary records keep only masks.
- `AuditEvent`: actor, service/subject, action, resource type/id, decision, result, policy reason, correlation ID, timestamp; no raw secret/member identifier fields.

## Immediate test requirements

Before any hosted/live-booking milestone, automated tests should prove at least:

- anonymous callers cannot access user-owned APIs;
- User A cannot read/approve/modify User B's objects even with a valid object ID;
- a stale, expired, revoked, already-used, or materially changed approval cannot drive an adapter;
- sensitive identifiers are absent from ordinary proposal responses and ordinary logs;
- transaction adapters can access only the explicitly approved record/fields and cannot enumerate other user records;
- service/research identities cannot query the sensitive-identifier store;
- security/audit events are emitted for authentication, authorization failures, proposal approval, privileged access, and adapter handoff.

## Open questions for Manager / Primary

1. Is BenefitFlow intended initially as single-user local software, a multi-tenant hosted consumer service, an employer-sponsored service, or multiple deployment modes? The IAM boundary changes materially by deployment model.
2. Which external IdP strategy is preferred: consumer CIAM, platform-native authentication, or an abstraction supporting multiple IdPs?
3. What exact actions should trigger step-up authentication: approval creation, member-ID disclosure, booking execution, claims activity, profile/recovery changes, or all of the above?
4. Will transaction adapters run in-process or as separately deployed services? Separate deployment materially strengthens least privilege and secret isolation.
5. What retention/consent requirements R5 establishes for plan/member identifiers should determine whether BenefitFlow stores identifiers at all between transactions.

## Initial manager disposition recommendation

- **BF-R9-01:** SUPPORTED
- **BF-R9-02:** SUPPORTED — production blocker
- **BF-R9-03:** SUPPORTED — production blocker for hosted member data
- **BF-R9-04:** SUPPORTED — high priority
- **BF-R9-05:** SUPPORTED
- **BF-R9-06:** SUPPORTED

No accepted project state was modified by this researcher.
