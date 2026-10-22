#!/usr/bin/env python3
"""Regression guard for binding a native init ELF to its production payload.

This is a source-contract test only. It does not replace the six-case ISO
acceptance matrix or prove that the selected target is operational.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
source = (ROOT / "kernel/core/target_launch.cpp").read_text(encoding="utf-8")
required = (
    "uint32_t payload_count=0;",
    "Target payload_target=TARGET_NONE;",
    "case CHIMERA_MODULE_LIVE_INITRAMFS:",
    "case CHIMERA_MODULE_INSTALL_IMAGE:",
    "case CHIMERA_MODULE_RECOVERY_INITRAMFS:",
    "if (payload_count>1u)",
    "if (payload_count==1u && payload_target!=target)",
    "native init target does not match the selected production payload",
)
missing = [part for part in required if part not in source]
if missing:
    raise SystemExit("native init payload-binding contract missing: " + "; ".join(missing))
print("native init payload-binding contract: PASS (source-level only)")
