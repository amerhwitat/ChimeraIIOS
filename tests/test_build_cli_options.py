#!/usr/bin/env python3
"""Regression test for documented online ISA catalog refresh CLI aliases."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
script = (root / "build-chimera-iso.sh").read_text(encoding="utf-8")
assert "--refresh-online-catalogs|--refresh-isa-catalog)" in script, (
    "the ISO builder must accept both documented catalog refresh options"
)
assert "--refresh-online-catalogs, --refresh-isa-catalog" in script, (
    "help output must document the ISA refresh alias"
)
assert 'if [[ "$RELEASE_BUILD" == 1 && "$RUN_NATIVE_SIX_CASE_DIAGNOSTICS" != 1 ]]' in script, (
    "production release mode must not permit skipping the same-ISO six-case diagnostics"
)
assert 'Release mode requires QEMU and OVMF for all six same-ISO cases.' in script, (
    "production release mode must fail when BIOS/UEFI QEMU prerequisites are unavailable"
)
assert 'Release mode requires a matching OVMF_CODE/OVMF_VARS pair.' in script, (
    "production release mode must fail when a matched OVMF firmware pair is unavailable"
)
print("ISO builder CLI aliases and fail-closed release diagnostics: PASS")
