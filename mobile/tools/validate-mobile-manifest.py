#!/usr/bin/env python3
"""Validate the shared mobile, microkernel, and PnP contract."""
import json
from pathlib import Path
root = Path(__file__).resolve().parents[2]
data = json.loads((root / "mobile" / "mobile-sync.json").read_text(encoding="utf-8"))
assert data["schema"] in {"CHM-MOBILE-SYNC-2", "CHM-MOBILE-SYNC-3", "CHM-MOBILE-SYNC-4"}
assert data["source_of_truth"] == "ChimeraIIOS/main"
assert "android" in data and "apple" in data
assert data["shared_security"]["signature_verification"] == "required"
if data["schema"] == "CHM-MOBILE-SYNC-4":
    assert data["driver_discovery"]["catalog"] == "system/drivers/catalog.json"
    assert data["microkernel"]["pnp"]["remote_driver_auto_load"] is False
print("Chimera mobile manifest: valid")
