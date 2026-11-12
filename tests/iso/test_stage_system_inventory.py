#!/usr/bin/env python3
"""Regression test: ISO output nested below boot/ must never be rescanned as source."""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
script = repo / "tools/iso/stage-system-inventory.py"
with tempfile.TemporaryDirectory(prefix="chimera-iso-inventory-") as temp:
    root = Path(temp) / "repo"
    iso = root / "boot/iso/dist/iso"
    (root / "boot/units").mkdir(parents=True)
    (root / "system/units").mkdir(parents=True)
    iso.mkdir(parents=True)
    (root / "boot/units/chimera-boot.service").write_text("[Unit]\nDescription=boot\n")
    (root / "system/units/chimera-system.service").write_text("[Unit]\nDescription=system\n")
    subprocess.run(
        [sys.executable, str(script), "--root", str(root), "--iso", str(iso)],
        check=True, capture_output=True, text=True,
    )
    inventory_path = iso / "boot/chimera/manifests/ISO-COMPONENT-INVENTORY.json"
    inventory = json.loads(inventory_path.read_text())
    entries = [x for x in inventory["entries"] if x["kind"] == "service-unit-definition"]
    assert len(entries) == 2, f"expected exactly two source units, got {len(entries)}"
    assert (iso / "usr/share/chimera/service-unit-definitions/boot/units/chimera-boot.service").is_file()
    assert (iso / "usr/share/chimera/service-unit-definitions/system/units/chimera-system.service").is_file()
    assert not any("/service-unit-definitions/boot/iso/" in x["iso_path"] for x in entries)
print("ISO inventory nested-output recursion regression passed")
