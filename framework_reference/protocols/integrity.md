# Integrity Protocol

Important package components are content-hashed. A package cannot claim complete when mandatory files, declared dependencies, sanitization, or hash verification fail. Discovery metadata is not self-validating: bootstrap must verify that every declared dependency actually exists. Fail closed.
