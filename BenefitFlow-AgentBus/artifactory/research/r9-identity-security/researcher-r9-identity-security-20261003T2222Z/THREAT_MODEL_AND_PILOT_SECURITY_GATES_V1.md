# BenefitFlow R9 — Threat Model and Pilot Security Gates v1

**Agent:** `researcher-r9-identity-security-20261003T2222Z`  
**Project:** BenefitFlow (`project_id=benefitflow`)  
**Assignment:** R9 — Identity, Authentication, Security, and Hosted Data  
**Status:** Specialist evidence/recommendation package; not accepted project state.

## Purpose

Extend the initial R9 findings into the manager-requested deliverables: high-risk trust boundaries, authentication/account-recovery abuse cases, hosted-data risks, and concrete security acceptance criteria for a pilot. This package evaluates the current beta as evidence and defines what must change before BenefitFlow is exposed as a hosted multi-user service or allowed to drive a live transaction adapter.

## Current beta safety context

Two existing design choices materially reduce present risk:

1. `run_beta.py` binds Uvicorn to `127.0.0.1`, so the documented beta launch is local-only rather than network-exposed by default.
2. `.gitignore` excludes `*.db`, `*.sqlite`, and `*.sqlite3`, reducing accidental source-control publication of the current local state database.

These are useful local-beta controls. They are not substitutes for production authentication, authorization, encryption, tenancy, rate limiting, or auditability.

## New repository findings

### BF-R9-07 — Approval state is replayable and reversible

`approve_proposal()` reads the proposal record but does not persist a transition from `AWAITING_USER_APPROVAL` to a terminal/consumed state. It does not store an approval record, `used_at`, `revoked_at`, expiry, or transaction nonce.

The existing test `test_approval_gate_releases_only_transaction_handoff` first calls `approve_proposal(..., False)` and receives `DECLINED`, then calls `approve_proposal(..., True)` against the same proposal and receives `READY_FOR_TRANSACTION_ADAPTER`. The test therefore demonstrates that a declined proposal can later be approved without creating a new proposal, and an approved proposal can be re-approved repeatedly.

**Security consequence:** once a real adapter exists, replay can result in repeated disclosure or repeated external action. A stale or previously declined authorization cannot safely be treated as current authority.

**Required control:** approval must be an atomic, attributable state transition. Persist an immutable approval event and one-time transaction authorization. Enforce allowed transitions server-side, reject replay, expire approvals, and invalidate approval when material proposal terms change.

**Recommended disposition:** `SUPPORTED` — production blocker for live adapters.

### BF-R9-08 — Unbounded upload and request consumption is unsafe for hosted deployment

`POST /api/parse-file` executes `await file.read()` with no application-level file-size limit, then passes the entire byte string to `pypdf.PdfReader` when the filename ends in `.pdf`. No page-count, decompressed-content, parse-time, or request-rate limit is visible. `POST /api/parse-text` similarly accepts text without an explicit application-level length bound.

OWASP API4:2023 identifies missing maximum upload size, memory/CPU bounds, execution limits, and operation throttles as unrestricted resource-consumption risks.

**Security consequence:** a hosted service could be exposed to memory exhaustion, expensive PDF parsing, worker starvation, or cost-amplification attacks even before authentication bypass is considered.

**Required control:** enforce request body and upload limits at both edge/proxy and application layers; set maximum document size/page count; bound parse time and concurrency; rate-limit upload/parse endpoints; reject unsupported content; isolate document parsing from transaction/identity services.

**Recommended disposition:** `SUPPORTED` — pilot blocker for public/hosted upload endpoints.

### BF-R9-09 — User-controlled string fields have no explicit bounded-length security contract

The reviewed Pydantic request models constrain several numeric fields but do not set explicit maximum lengths for `insurer_name`, `preferred_window`, `plan_number`, or `member_id`. Provider-verification storage keys also incorporate the lower-cased insurer name.

**Security consequence:** this is not an exploit by itself, but hosted input contracts should not permit arbitrarily large identity/workflow strings. Unbounded values increase storage, logging, error-path, resource-consumption, and downstream-integration risk.

**Required control:** define schema-level maximum lengths and canonicalization rules for every external string; reject control characters where inappropriate; ensure downstream log/event encoding prevents log injection.

**Recommended disposition:** `SUPPORTED_WITH_LIMITS` — hardening requirement.

### BF-R9-10 — Current tests validate workflow behavior but not security invariants

Current workflow tests prove provider verification is required and that the beta stops at a transaction-handoff boundary. They do not test authentication, ownership, cross-account access, approval replay, approval expiry, material-term invalidation, session revocation, recovery abuse, adapter scope, rate limits, or sensitive-data log exclusion.

**Security consequence:** a future authentication layer could be added while the core authorization/state flaws remain undetected.

**Required control:** introduce explicit negative-security tests as release gates, not merely implementation tests.

**Recommended disposition:** `SUPPORTED`.

## High-risk trust boundaries

### TB1 — Browser/client ↔ BenefitFlow application

Threats: unauthenticated access, stolen sessions, CSRF after cookie-based authentication is introduced, token exposure, credential stuffing, object-ID substitution, automated resource abuse.

Required boundary controls: managed authentication, server-side authorization on every protected operation, secure sessions, CSRF protection for state-changing cookie-authenticated requests, rate limiting, request-size limits, secure headers, HTTPS in hosted deployments.

### TB2 — Application ↔ user-owned workflow objects

Threats: cross-account proposal access, tenant confusion, object-level authorization failure, mass assignment/property exposure, stale access after account disablement.

Required boundary controls: immutable `account_id`/tenant binding on every user-owned object, deny-by-default authorization, policy checks at each object read/write/action, negative cross-account tests.

### TB3 — Ordinary workflow state ↔ sensitive identifier store

Threats: member/plan identifier exfiltration, accidental logging, support/admin overreach, backups containing plaintext identifiers, broad service access.

Required boundary controls: minimize retention; keep only masks/opaque references in normal records; separately encrypt sensitive identifiers; KMS/vault-backed keys; narrowly scoped read permission; access audit; no research-service access.

### TB4 — User approval ↔ transaction authorization

Threats: replay, stale approval, changed terms after approval, approval spoofing, session theft immediately before external action.

Required boundary controls: approval record tied to authenticated subject and exact terms digest; recent-auth/step-up policy for sensitive disclosure/action; expiry; one-time consumption; idempotency key; terminal state; fresh approval on material change.

### TB5 — BenefitFlow ↔ external booking/insurer/provider adapter

Threats: confused deputy, adapter over-permission, secret leakage, retry duplication, external endpoint spoofing, compromised integration credential.

Required boundary controls: separate service identity; narrow scopes; short-lived credentials where possible; allowlisted destinations; exact approved payload only; idempotency; response verification; adapter cannot enumerate unrelated user data.

### TB6 — Application ↔ IdP / account recovery channels

Threats: OAuth/OIDC redirect abuse, code injection, weak recovery becoming an authentication bypass, SIM-swap/SMS takeover, changed-email takeover, user enumeration.

Required boundary controls: mature OIDC provider; RFC 9700 protections; PKCE where applicable; exact redirect allowlists; recovery at assurance comparable to account risk; generic recovery responses; single-use expiring tokens; recovery notifications; invalidate compromised sessions/authenticators.

### TB7 — Application ↔ audit/monitoring system

Threats: raw identifiers or tokens copied to logs, log tampering, malicious newline/control-character injection, overly broad analyst access.

Required boundary controls: structured logging, sensitive-field denylist/allowlist, sanitization, separate security event stream, append/tamper protection, restricted access, correlation identifiers rather than raw session secrets.

### TB8 — File parsing service ↔ uploaded benefit document

Threats: oversized files, parser resource exhaustion, malformed PDFs, decompression/pathological object graphs, data leakage into temporary/debug output.

Required boundary controls: size/page/time/concurrency limits; content validation; parser isolation; temporary-data cleanup; no document bodies in ordinary logs; dependency scanning and rapid patch path for parser libraries.

## Authentication and account-recovery abuse cases

### AC-01 Credential stuffing
Attacker reuses breached credentials. Controls: mature IdP, breached-password blocking where passwords are used, rate limiting, MFA/passkeys, anomaly detection, session revocation.

### AC-02 Account enumeration
Attacker distinguishes existing accounts through login/recovery response text or timing. Controls: generic/timing-consistent responses and throttling.

### AC-03 Recovery channel takeover / SIM swap
Attacker controls a phone number or newly changed recovery address. Controls: do not make SMS the sole strong recovery mechanism for sensitive accounts; require independent recovery evidence; notify established channels; treat recent recovery changes as high risk.

### AC-04 Recovery weakens MFA
Attacker bypasses stronger authentication through a weaker recovery path. Controls: risk-based documented recovery, saved recovery codes/independent channels/repeated proofing as appropriate, no silent assurance downgrade.

### AC-05 Session theft
Attacker steals a valid session and attempts proposal approval/member-ID disclosure. Controls: secure cookies, rotation, expiry, revocation, CSRF defense, recent-auth/step-up for sensitive actions.

### AC-06 Approval replay
Attacker or buggy client repeatedly invokes an authorization. Controls: atomic one-time consume, idempotency, durable terminal state, replay detection.

### AC-07 Material terms changed after approval
Provider, price, service, appointment window, practitioner, cancellation terms, or disclosure requirements change. Controls: canonical `terms_digest`; material mutation invalidates approval and requires fresh approval.

### AC-08 Cross-tenant object substitution
User A submits User B's object ID. Controls: ownership/entitlement enforcement on every object operation; negative BOLA tests.

### AC-09 Support/admin abuse
Privileged staff inspect or act on member data outside legitimate support need. Controls: separate staff identity plane, least privilege, no shared accounts, audited elevation/impersonation/break-glass.

### AC-10 Service credential compromise
Booking/calendar/provider integration credential is stolen. Controls: per-service principals, narrow scopes, secret vault, rotation, short-lived tokens where possible, destination restrictions.

## Pilot-readiness security acceptance criteria

A hosted pilot that stores real member/plan information or performs real booking-related actions should be **NO-GO** unless all P0 controls below are demonstrably satisfied.

### P0 — mandatory before hosted real-user / live-adapter pilot

- **P0.1 Authentication:** all non-public user-data endpoints require an authenticated principal.
- **P0.2 Object ownership:** every user-owned object is durably bound to an account/tenant; server-side authorization is enforced on every object operation.
- **P0.3 Cross-account tests:** automated tests prove User A cannot read, mutate, approve, export, or act on User B's records even with valid object IDs.
- **P0.4 Approval atomicity:** approval/decline is durably stored; invalid transitions are rejected; a declined proposal cannot later become approved without a new authorized workflow.
- **P0.5 One-time adapter authorization:** transaction authorization expires, is single-use/idempotent, and is tied to exact material terms.
- **P0.6 Sensitive identifier separation:** raw member/plan identifiers are absent from ordinary workflow records wherever technically avoidable; retained values are encrypted and access-controlled separately.
- **P0.7 No sensitive logging:** raw member/plan IDs, passwords, tokens, session secrets, recovery codes, uploaded plan bodies, and integration secrets are excluded from ordinary logs.
- **P0.8 Auditability:** authentication, recovery, authorization failures, sensitive-data access, approval, privileged access, and transaction-adapter handoff generate attributable audit/security events.
- **P0.9 Secure recovery:** recovery uses single-use/expiring evidence, anti-enumeration controls, notifications, throttling, and does not trivially bypass stronger authentication.
- **P0.10 Session security:** secure cookie/token handling, rotation, logout/revocation, timeout policy, and CSRF defense for state-changing cookie-authenticated requests.
- **P0.11 Upload/resource controls:** hosted parse endpoints enforce request/file limits, parse time/concurrency bounds, and rate limits.
- **P0.12 Service least privilege:** transaction/research/provider-verification/calendar components have distinct service identities/scopes; research components cannot retrieve member identifiers.
- **P0.13 Secrets:** production secrets/keys are not stored in source/build artifacts/ordinary config; managed secret/KMS storage and rotation procedures exist.
- **P0.14 Transport:** hosted user, IdP, and adapter traffic uses authenticated TLS.
- **P0.15 Incident control:** operators can revoke sessions/authenticators, disable accounts/service credentials, and stop transaction adapters without editing application code.

### P1 — required before expansion beyond tightly controlled pilot

- phishing-resistant sign-in/step-up option such as WebAuthn/passkeys;
- security notifications for new authenticator, recovery, sensitive profile changes, suspicious sign-in;
- dependency/SCA and secret scanning in CI with a documented patch SLA;
- security headers/CSP appropriate to deployed frontend architecture;
- encrypted backup policy with restore tests and least-privilege backup access;
- centralized alerting for auth abuse, cross-account denials, recovery abuse, adapter replay, anomalous privileged access;
- formal data-retention/deletion rules informed by R5;
- tested support/admin break-glass process;
- external security review or penetration test before broad public launch.

## Minimum negative-security test suite

1. anonymous call to each protected API → denied;
2. User A uses User B proposal ID → denied;
3. User A uses User B sensitive-data reference → denied;
4. approve twice → no second external action;
5. decline then approve same immutable proposal → rejected unless a new approval workflow is created;
6. approve then change material terms → prior approval invalid;
7. expired approval → adapter denied;
8. revoked session → protected API denied;
9. completed recovery → old sessions/recovery tokens cannot restore attacker access;
10. oversized PDF/text payload → bounded rejection before excessive resource use;
11. flood recovery/upload/verification endpoint → throttled;
12. sensitive identifiers/tokens in requests → absent from logs;
13. research/service identity requests member identifier → denied;
14. transaction adapter requests unrelated record → denied;
15. malicious control characters in event text → safely encoded/sanitized;
16. privileged support action → attributable audit event emitted.

## Evidence index

### E-R9-01 — NIST SP 800-63B-4
Owner/type: NIST / government standard. URL: https://pages.nist.gov/800-63-4/sp800-63b.html . Retrieved 2026-10-03. Relevant evidence: account recovery is security-sensitive; recovery codes/contacts/repeated proofing are recognized; recovery notifications are required; recovery and session threats are explicitly discussed.

### E-R9-02 — RFC 9700
Owner/type: IETF / Internet Best Current Practice. Published January 2025. URL: https://www.rfc-editor.org/rfc/rfc9700.html . Applicability: OAuth/OIDC flows. Relevant evidence: modern authorization-code defenses, PKCE requirements/recommendations, redirect/CSRF/mix-up protections.

### E-R9-03 — OWASP API1:2023 Broken Object Level Authorization
URL: https://api-security.owasp.org/editions/2023/en/0xa1-broken-object-level-authorization/ . Retrieved 2026-10-03. Relevant evidence: user-supplied object IDs require server-side object authorization regardless of ID format/randomness.

### E-R9-04 — OWASP API4:2023 Unrestricted Resource Consumption
URL: https://api-security.owasp.org/editions/2023/en/0xa4-unrestricted-resource-consumption/ . Retrieved 2026-10-03. Relevant evidence: APIs should bound upload size, CPU/memory/time, request frequency, and external-service cost exposure.

### E-R9-05 — OWASP Forgot Password Cheat Sheet
URL: https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html . Retrieved 2026-10-03. Relevant evidence: anti-enumeration responses, secure single-use expiring recovery evidence, throttling, and post-compromise session/recovery cleanup.

### E-R9-06 — OWASP Session Management Cheat Sheet
URL: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html . Retrieved 2026-10-03. Relevant evidence: session rotation/protection and reauthentication after high-risk events.

### E-R9-07 — OWASP Logging Cheat Sheet
URL: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html . Retrieved 2026-10-03. Relevant evidence: log security-relevant actions while excluding raw tokens/passwords/sensitive personal data and protecting log integrity/access.

## What this evidence does not establish

- It does not determine which Canadian privacy statute/regulator applies to a particular BenefitFlow deployment; R5 owns legal/applicability analysis.
- It does not establish that BenefitFlow must meet NIST AAL2 or another federal assurance level.
- It does not select a specific identity vendor, KMS, database, SIEM, or cloud provider.
- It does not establish that the local-only beta is presently internet-exploitable; the documented launch binds to localhost.
- It does not replace penetration testing or production architecture review once deployment topology is known.

## Recommended manager disposition

- BF-R9-07 replayable/reversible approval: `SUPPORTED` — production blocker for live adapters.
- BF-R9-08 unbounded hosted upload/resource consumption: `SUPPORTED` — hosted-pilot blocker.
- BF-R9-09 unbounded string contracts: `SUPPORTED_WITH_LIMITS` — hardening requirement.
- BF-R9-10 missing negative-security release gates: `SUPPORTED`.
- P0 pilot gates: recommend `ESCALATE_TO_PRIMARY` for adoption as release criteria after Manager reconciliation and R5/R8/R10 cross-lane review.

No accepted project state was modified by this specialist.
