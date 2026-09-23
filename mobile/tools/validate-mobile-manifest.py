#!/usr/bin/env python3
import json
from pathlib import Path
root=Path(__file__).resolve().parents[2]
data=json.loads((root/"mobile"/"mobile-sync.json").read_text(encoding="utf-8"))
assert data["schema"]=="CHM-MOBILE-SYNC-1"
assert data["source_of_truth"]=="ChimeraIIOS/main"
assert "android" in data and "apple" in data
assert data["shared_security"]["signature_verification"]=="required"
print("Chimera mobile manifest: valid")
