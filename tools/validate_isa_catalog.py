#!/usr/bin/env python3
"""Validate the canonical Chimera ISA catalog without third-party dependencies."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "isa" / "catalog.json"


def main() -> int:
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    assert data["schema"] == "CHM-ISA-CATALOG-1"
    families = {f["id"] for f in data["families"]}
    ids = set()
    for insn in data["instructions"]:
        assert insn["id"] not in ids, insn["id"]
        ids.add(insn["id"])
        assert insn["family"] in families
        e = insn["encoding"]
        assert e["length_bits"] % 8 == 0
        b = e["sample"]["binary"]
        h = e["sample"]["hex"]
        assert len(b) == e["length_bits"]
        assert re.fullmatch(r"[01]+", b)
        assert h.lower() == format(int(b, 2), "#x"), (insn["id"], h)
        assert e["fields"]
    assert any(any(o.get("optional") for o in i["operands"]) for i in data["instructions"])
    assert len(data["sources"]) >= 5
    print(f"ISA catalog valid: {len(families)} families, {len(ids)} instructions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
