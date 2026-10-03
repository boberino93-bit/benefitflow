# Presence and Liveness

Executing agents publish immutable presence/service frames with a configurable lease. Derived state may be ACTIVE, IDLE, BLOCKED, LATE, RELEASED, FAILED, or UNKNOWN. A stale lease ages a worker to LATE; history remains. Liveness indicates execution state only. A dormant or ended session must never be represented as independently continuing work.
