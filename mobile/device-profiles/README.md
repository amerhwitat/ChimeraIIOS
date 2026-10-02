# Chimera II Mobile Device Profiles

Profiles are exact hardware contracts. The builder only generates a ROM when the
connected phone matches stable vendor identifiers and architecture.

Each profile must define exact boot mode, signed-image requirements, rollback
metadata, and explicit partition mappings. Generic or guessed mappings are rejected.

No FRP, Activation Lock, MDM, carrier-lock, OEM authorization, Secure Boot, or
Verified Boot bypasses are implemented. Destructive writes require confirmation
and verified hashes.