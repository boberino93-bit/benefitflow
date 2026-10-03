# Message Bus Protocol

Messages are immutable, append-only routing/event records. Corrections create a new SUPERSESSION record that references the old record. Messages should summarize and point to artifacts/evidence instead of duplicating full reports. Required kinds include claims, findings, blockers, requests, review traffic, contradictions, handoffs, decisions, supersessions, service checkpoints, and release/close records.
