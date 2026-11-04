# CHMRG01 registry and settings

The registry is a Chimera-owned, versioned typed configuration store. Its hierarchical organization is inspired by the Windows registry, but it is not compatible with or derived from Microsoft's proprietary SAM database.

## Hives
- machine: host identity and machine-wide policy.
- environment: desktop/session defaults and user environment policy.
- kernel: boot-time and kernel policy. Values are descriptive until an explicitly implemented kernel consumer validates and adopts them.

Immutable image defaults live in system/registry/*.defaults.json. Runtime source copies live under /var/lib/chimera/registry/source and compiled hives under /var/lib/chimera/registry/hives.

## GUI and CLI
Aurora Registry & System Settings lists, searches, adds, edits and deletes typed entries. CLI examples:

    chimera-registry-editor list environment
    chimera-registry-editor get environment environment.locale
    chimera-registry-editor set environment environment.locale string en_US.UTF-8

Machine and kernel changes require administrator privileges. The editor does not make unsupported kernel settings live; only implemented consumers may read them.

## Transactions
The transaction journal contains the complete next source and binary hive images. It is fsync'd before either destination is replaced. Recovery replays prepared transactions idempotently, and an advisory lock serializes local writers. This is a single-host transaction protocol, not distributed consensus.

Never store passwords, Kerberos tickets, private keys, tokens or other secrets in registry values or repository defaults. Use the OS credential store.
