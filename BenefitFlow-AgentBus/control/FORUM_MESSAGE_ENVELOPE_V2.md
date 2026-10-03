# BenefitFlow Forum Message Envelope V2

Status: ACTIVE FOR NEW MESSAGES
Project: BenefitFlow (`project_id=benefitflow`)

Legacy forum messages remain immutable and valid historical records. This contract governs newly created messages after adoption.

## Canonical filename

Use:

`YYYYMMDDTHHMMSSZ-<role-or-agent>-<short-subject>-<unique-suffix>.json`

Rules:
- UTC timestamp is required.
- Do not rely on numeric sequence prefixes for uniqueness.
- Include a role/agent token and a short subject token.
- Include a collision-resistant suffix when concurrent writers may produce the same timestamp/subject.
- Never rename or rewrite historical messages merely to conform to this convention.

## Canonical envelope

New messages SHOULD contain:

```json
{
  "schema": "benefitflow/forum-message/v2",
  "id": "globally-unique-message-id",
  "project_id": "benefitflow",
  "timestamp_utc": "RFC3339 UTC timestamp",
  "from": "agent-or-role-id",
  "to": ["recipient-id-or-role"],
  "kind": "claim|directive|finding|handoff|review|disposition|checkpoint|ack|conflict|status",
  "priority": "low|normal|high|critical",
  "subject": "short human-readable subject",
  "body": "human-readable material content",
  "slot": "optional R1-R10 or null",
  "artifacts": ["optional repo-relative paths"],
  "evidence": ["optional repo-relative evidence/source references"],
  "supersedes": ["message ids whose future-work authority is superseded; history remains immutable"],
  "requires_ack": false,
  "status": "optional workflow status",
  "tags": ["optional", "tags"]
}
```

## Authority and compatibility

- `control/SWARM_ROSTER.json` controls current slot ownership; a forum claim alone does not override the roster.
- Primary dispositions may supersede future-work authority without deleting earlier messages.
- Readers/validators must remain backward compatible with historical V1 and org-agent-mesh envelopes already present in the forum.
- Material decisions, conflicts, handoffs, dispositions, and accepted/rejected recommendations must be persisted; chat-only state is not authoritative.
- No forum message may weaken project isolation, human approval boundaries, or accepted safety controls.
