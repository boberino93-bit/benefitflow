# Persistence and Storage Adapters

The framework may persist through a file library, object store, source repository, document platform, database, API, or another configured system. Every storage adapter declares durability, atomic-create/compare-and-set capability, checksum support, read-after-write expectations, and failure semantics.

Do not infer atomic coordination from a storage system that does not provide it. If lane ownership cannot be acquired atomically, use an explicit allocation authority, deterministic partitioning, or a project-configured fencing mechanism. A successful write is not a durable handoff until its bytes/provenance are verified and the corresponding immutable message is published.

Bootstrap validation resolves every declared dependency against the source/location named by discovery. A checksum manifest cannot compensate for a missing or stale discovery target. Cross-source fallbacks must be explicit; agents must not silently guess path remaps between authorities.
