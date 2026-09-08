#!/usr/bin/env python3
"""Regression coverage for ISA source reconciliation."""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "tools" / "isa" / "generate_isa_bitfields.py"


def write_csv(path: Path, rows: list[tuple[str, str]]) -> None:
    fields = ["mnemonic", "opcode"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter=";")
        writer.writeheader()
        for mnemonic, opcode in rows:
            writer.writerow({"mnemonic": mnemonic, "opcode": opcode})


def test_csv_authority_reconciles_stale_cpp_name(tmp_path: Path) -> None:
    cpp = tmp_path / "chimera_isa.cpp"
    cpp.write_text(
        'constexpr std::string_view names =\n'
        '    "OLD_NAME AUDIT_EXPORT";\n',
        encoding="utf-8",
    )
    canonical = tmp_path / "canonical.csv"
    write_csv(canonical, [("AUDIT_EXPORT", "0x0001"), ("OTHER", "0x0002")])
    output = tmp_path / "isa.json"

    subprocess.run(
        [sys.executable, str(GENERATOR), "--cpp", str(cpp), "--canonical", str(canonical), "--expanded", str(tmp_path / "missing.csv"), "--extension", str(tmp_path / "missing2.csv"), "--output", str(output)],
        check=True,
        cwd=ROOT,
    )
    doc = json.loads(output.read_text(encoding="utf-8"))
    names = [item["mnemonic"] for item in doc["instructions"]]
    assert len(names) == len(set(names))
    assert "AUDIT_EXPORT" in names
    assert "OP_0002" not in names
