# Chimera II assembler/disassembler contract

ISO-Tool reserves native backends for Chimera II C8192 variable-width CISC and R8192 fixed-width RISC instruction streams. The decoder must preserve exact packet bytes and identify unknown/reserved encodings rather than silently mapping them to another architecture.

C8192 supports the project's variable-width packet/register contract. R8192 uses fixed 64-bit instruction packets. Native tools are reported unavailable until their actual binaries/implementations exist.
