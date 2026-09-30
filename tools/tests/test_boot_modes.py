#!/usr/bin/env python3
import json
from pathlib import Path

p = Path(__file__).resolve().parents[2] / "boot/chimera-boot-modes.json"
d = json.loads(p.read_text())
assert d["schema"] == "chimera-boot-modes-v1"
ids = [m["id"] for m in d["modes"]]
expected = {"normal","recovery","safe-mode","last-known-good","live-aurora","installer","diagnostics","chainloader"}
assert set(ids) == expected
assert len(ids) == len(set(ids))
assert d["default"] == "normal"
assert d["last_known_good"]["write_after"] == "aurora-healthcheck"
print("PASS: all required boot modes are defined")
