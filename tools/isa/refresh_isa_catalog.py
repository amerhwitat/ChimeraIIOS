#!/usr/bin/env python3
"""Refresh source-backed ISA indexes and regenerate the universal instruction catalog.

Network discovery is opt-in. This tool records provenance and explicit semantic
properties; it never infers missing register effects or marks catalog rows as
executable/conformant. Native/compatibility execution is enabled only by a
separately implemented and tested backend.
"""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEMANTIC_FIELDS = (
    "operands", "description", "register_classes", "flags_read", "flags_written",
    "memory_effects", "privilege", "extensions", "feature_requirements",
    "exceptions", "semantic_id", "native_mapping", "compatibility_mapping",
    "encoding_status", "execution_status", "source_ref", "source_revision",
    "source_sha256", "license",
)
PIPELINE = (
    ("tools/catalogs/refresh_online_catalogs.py", ["--refresh"]),
    ("tools/isa/crawl_sources.py", ["--refresh"]),
    ("tools/isa/import_riscv_opcodes.py", []),
    ("tools/catalogs/merge_online_catalogs.py", []),
)

def run(path: str, args: list[str]) -> None:
    command = [sys.executable, str(ROOT / path), *args]
    print("[ISA-REFRESH] " + " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)

def validate_catalog(path: Path) -> dict:
    if not path.is_file():
        raise ValueError(f"generated universal catalog missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("instructions")
    if not isinstance(rows, list) or not rows:
        raise ValueError("universal catalog contains no instruction records")
    missing = sorted({field for row in rows for field in SEMANTIC_FIELDS if field not in row})
    if missing:
        raise ValueError("instruction records missing semantic/provenance fields: " + ", ".join(missing))
    allowed = {"conformance-tested", "implemented-unverified", "not-implemented", "not-applicable"}
    invalid = sorted({str(row.get("execution_status")) for row in rows if row.get("execution_status") not in allowed})
    if invalid:
        raise ValueError("invalid execution status values: " + ", ".join(invalid))
    return {
        "schema": "CHM-ISA-REFRESH-REPORT-1",
        "catalog": str(path.relative_to(ROOT)),
        "instruction_records": len(rows),
        "architecture_count": len(data.get("unique_architectures", [])),
        "semantic_fields_checked": list(SEMANTIC_FIELDS),
        "conformance_tested_records": sum(row.get("execution_status") == "conformance-tested" for row in rows),
        "implemented_unverified_records": sum(row.get("execution_status") == "implemented-unverified" for row in rows),
        "not_implemented_records": sum(row.get("execution_status") == "not-implemented" for row in rows),
        "policy": "Discovery and metadata validation do not implement an ISA backend or establish conformance."
    }

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--refresh", action="store_true", help="fetch configured public ISA sources, then regenerate catalogs")
    mode.add_argument("--offline", action="store_true", help="regenerate from the locally cached database/import files only")
    mode.add_argument("--self-test", action="store_true", help="validate the catalog schema without network access")
    ap.add_argument("--output", type=Path, default=ROOT / "isa/generated/universal-instruction-catalog.json")
    args = ap.parse_args()
    if args.self_test:
        sample = {field: None for field in SEMANTIC_FIELDS}
        sample.update(execution_status="not-implemented", architecture="test", mnemonic="NOP")
        assert all(field in sample for field in SEMANTIC_FIELDS)
        print(f"ISA refresh schema self-test passed ({len(SEMANTIC_FIELDS)} semantic/provenance fields)")
        return 0
    if args.refresh:
        for path, argv in PIPELINE:
            run(path, argv)
    input_file = ROOT / "isa/sources/imports/riscv-opcodes.json"
    cmd = ["--output", str(args.output)]
    if input_file.is_file():
        cmd = ["--input", str(input_file), *cmd]
    run("tools/isa/build_universal_catalog.py", cmd)
    report = validate_catalog(args.output)
    report_path = ROOT / "isa/generated/isa-refresh-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
    print(f"[ISA-REFRESH] records={report['instruction_records']} architectures={report['architecture_count']} "
          f"conformance-tested={report['conformance_tested_records']} not-implemented={report['not_implemented_records']}")
    print(f"[ISA-REFRESH] report={report_path.relative_to(ROOT)}")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (subprocess.CalledProcessError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[ISA-REFRESH] ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
