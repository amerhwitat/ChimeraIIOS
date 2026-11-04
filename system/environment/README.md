# Environment defaults

Environment hive values are defaults copied through a process-manager allowlist at process creation, never a shared mutable process environment. PATH and shell paths must be checked against mounted filesystems. Locale/timezone remain hints until corresponding services exist. Do not store credentials, tokens, private keys or other secrets here. User overrides require a user-owned hive and VFS-enforced permissions.
