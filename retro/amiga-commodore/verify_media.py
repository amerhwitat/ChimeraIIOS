#!/usr/bin/env python3
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "build/retro-media")
manifest = json.loads((root / "media-manifest.json").read_text(encoding="utf-8"))
adf = root / "AROS-Amiga-500-2000-m68k-boot.adf"
d64 = root / "CHIMERA-Commodore-64.d64"
prg = root / "CHIMERA64.PRG"
assert adf.stat().st_size == 880 * 1024
assert adf.read_bytes()[:3] == b"DOS"
assert d64.stat().st_size == 174848
assert prg.read_bytes()[:2] == b"\\x01\\x08"
assert manifest["amiga"]["format"] == "ADF"
assert manifest["commodore"]["format"].startswith("D64")
assert manifest["amiga"]["sha256"] and manifest["commodore"]["sha256"]
print("Amiga ADF and Commodore 64 D64 structural checks: PASS")
