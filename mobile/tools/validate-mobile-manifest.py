#!/usr/bin/env python3
"""Validate the versioned mobile synchronization contract."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
data = json.loads((root / "mobile" / "mobile-sync.json").read_text(encoding="utf-8"))
assert data.get("schema") in {"CHM-MOBILE-SYNC-2", "CHM-MOBILE-SYNC-3"}, "unsupported mobile manifest schema"
assert data["source_of_truth"] == "ChimeraIIOS/main"
assert isinstance(data.get("android"), dict) and isinstance(data.get("apple"), dict)
assert data["shared_security"]["signature_verification"] == "required"
assert data["shared_security"]["flash_confirmation"] == "required"
assert data["shared_security"]["generic_partition_flash"] == "forbidden"
if data["schema"] == "CHM-MOBILE-SYNC-3":
    assert data["microkernel"]["syscall_abi"] is True
    assert data["microkernel"]["mixed_width_ipc"] is True
    assert data["endianness"]["contract"] == "system/architecture/endianness.json"
print(f"Chimera mobile manifest: valid ({data['schema']})")
