# Source-of-Truth Protocol

Every authoritative source declares `source_id`, `type`, `location_reference`, `authority_scope`, `freshness_expectation`, `verification_method`, `write_authority`, and `read_authority`. A project may have several authorities for different scopes. Material claims name the source that supports them. When authorities conflict, resolve scope and freshness explicitly rather than assuming a universal winner.
