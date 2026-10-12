#!/usr/bin/env python3
"""Normalize sourced ISA instruction records for Chimera II OS.

This tool never invents opcodes or claims that catalog presence means execution
support. Importers should supply architecture-specific records from licensed,
versioned machine-readable sources (e.g. LLVM TableGen, GNU binutils opcode
tables, or vendor-published machine-readable specifications).
"""
from __future__ import annotations
import argparse
import json
import hashlib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "isa" / "isa_database.json"
DEFAULT_OUT = ROOT / "isa" / "generated" / "universal-instruction-catalog.json"
SCHEMA = "CHM-ISA-UNIVERSAL-1"
ENDIAN = {"little", "big", "bi", "instruction-little", "mixed", "not-applicable"}

REQUIRED = ("architecture", "mnemonic", "form_id", "operands", "length_bits")

def normalize(row: dict[str, Any], source: str) -> dict[str, Any]:
    arch = str(row.get("architecture", "")).strip().lower()
    mnemonic = str(row.get("mnemonic", "")).strip().upper()
    form = str(row.get("form_id", row.get("form", "unspecified"))).strip()
    if not arch or not mnemonic:
        raise ValueError("architecture and mnemonic are required")
    length = row.get("length_bits")
    if not isinstance(length, int) or length <= 0:
        raise ValueError(f"{arch}:{mnemonic}: length_bits must be a positive integer")
    operands = row.get("operands", [])
    if not isinstance(operands, (list, str)):
        raise ValueError(f"{arch}:{mnemonic}: operands must be a list or syntax string")
    endian = str(row.get("endianness", "not-applicable")).lower()
    if endian not in ENDIAN:
        raise ValueError(f"{arch}:{mnemonic}: unknown endianness {endian}")
    value = row.get("value_bits", row.get("opcode_bits"))
    mask = row.get("mask_bits", row.get("opcode_mask"))
    if value is not None and not isinstance(value, str):
        value = format(int(value), "b")
    if mask is not None and not isinstance(mask, str):
        mask = format(int(mask), "b")
    if value is not None and (len(value) != length or any(ch not in "01" for ch in value)):
        raise ValueError(f"{arch}:{mnemonic}: value_bits must be {length} binary characters")
    if mask is not None and (len(mask) != length or any(ch not in "01" for ch in mask)):
        raise ValueError(f"{arch}:{mnemonic}: mask_bits must be {length} binary characters")
    if (value is None) != (mask is None):
        raise ValueError(f"{arch}:{mnemonic}: value_bits and mask_bits must be supplied together")
    source_url = str(row.get("source_ref", source))
    encoding_status = "sourced-mask-verified" if value is not None else "encoding-unspecified"
    execution = str(row.get("execution_status", "not-implemented"))
    if execution not in {"conformance-tested", "implemented-unverified", "not-implemented", "not-applicable"}:
        execution = "not-implemented"
    record = {
        "architecture": arch,
        "mnemonic": mnemonic,
        "form_id": form,
        "operands": operands,
        "syntax": row.get("syntax", ""),
        "description": row.get("description", ""),
        "length_bits": length,
        "value_bits": value,
        "mask_bits": mask,
        "opcode_hex": row.get("opcode_hex"),
        "encoding": row.get("encoding", "unspecified"),
        "endianness": endian,
        "instruction_byte_order": row.get("instruction_byte_order", endian),
        "operand_endianness": row.get("operand_endianness", "architecture-defined"),
        "immediate_fields": row.get("immediate_fields", []),
        "register_classes": row.get("register_classes", []),
        "flags_read": row.get("flags_read", []),
        "flags_written": row.get("flags_written", []),
        "memory_effects": row.get("memory_effects", "unknown"),
        "privilege": row.get("privilege", "architecture-defined"),
        "extensions": row.get("extensions", []),
        "feature_requirements": row.get("feature_requirements", []),
        "exceptions": row.get("exceptions", []),
        "semantic_id": row.get("semantic_id"),
        "native_mapping": row.get("native_mapping"),
        "compatibility_mapping": row.get("compatibility_mapping"),
        "encoding_status": encoding_status,
        "execution_status": execution,
        "source_ref": source_url,
        "source_revision": row.get("source_revision", "unspecified"),
        "source_sha256": row.get("source_sha256"),
        "license": row.get("license", "check-source-terms"),
    }
    return record

def from_legacy(db: dict[str, Any]) -> list[dict[str, Any]]:
    family_endian = {
        "x86-64": "little", "x86": "little", "aarch64": "little",
        "arm32": "bi", "riscv32": "instruction-little", "riscv64": "instruction-little",
        "power": "bi", "mips32": "bi", "mips64": "bi", "sparc": "big",
        "m68k": "big", "systemz": "big",
    }
    out = []
    for raw in db.get("instructions", []):
        if not isinstance(raw, (list, tuple)) or len(raw) < 6:
            continue
        arch, mnemonic, form, operands, syntax, length = raw[:6]
        value = raw[6] if len(raw) > 6 else None
        mask = raw[7] if len(raw) > 7 else None
        # Legacy entries use string bit fields. Do not upgrade malformed masks.
        row = {
            "architecture": arch, "mnemonic": mnemonic, "form_id": form,
            "operands": operands, "syntax": syntax, "length_bits": length,
            "value_bits": value, "mask_bits": mask,
            "endianness": family_endian.get(str(arch).lower(), "not-applicable"),
            "source_ref": "isa/isa_database.json",
            "source_revision": str(db.get("version", "unknown")),
            "execution_status": "not-implemented",
        }
        try:
            out.append(normalize(row, "isa/isa_database.json"))
        except (ValueError, TypeError):
            continue
    return out

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=DEFAULT_DB)
    parser.add_argument("--input", type=Path, action="append", default=[],
                        help="additional JSON file containing an array of sourced instruction objects")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    db = load_json(args.database)
    records = from_legacy(db)
    for path in args.input:
        payload = load_json(path)
        rows = payload if isinstance(payload, list) else payload.get("instructions", [])
        if not isinstance(rows, list):
            raise SystemExit(f"{path}: expected an array or an object with instructions[]")
        for row in rows:
            if not isinstance(row, dict):
                continue
            source = str(row.get("source_ref", path.as_posix()))
            records.append(normalize(row, source))
    unique = {}
    for rec in records:
        key = (rec["architecture"], rec["mnemonic"], rec["form_id"], rec["length_bits"],
               rec["value_bits"], rec["mask_bits"])
        unique[key] = rec
    final = sorted(unique.values(), key=lambda r: (r["architecture"], r["mnemonic"], r["form_id"], r["length_bits"]))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": SCHEMA,
        "database_version": db.get("version", "unknown"),
        "record_count": len(final),
        "unique_architectures": sorted({r["architecture"] for r in final}),
        "coverage": {
            "sourced_encoding_masks": sum(r["encoding_status"] == "sourced-mask-verified" for r in final),
            "encoding_unspecified": sum(r["encoding_status"] != "sourced-mask-verified" for r in final),
            "conformance_tested": sum(r["execution_status"] == "conformance-tested" for r in final),
            "implemented_unverified": sum(r["execution_status"] == "implemented-unverified" for r in final),
            "not_implemented": sum(r["execution_status"] == "not-implemented" for r in final),
        },
        "property_schema": [
            "architecture", "mnemonic", "form_id", "operands", "syntax", "description",
            "length_bits", "value_bits", "mask_bits", "opcode_hex", "encoding",
            "endianness", "instruction_byte_order", "operand_endianness",
            "immediate_fields", "register_classes", "flags_read", "flags_written",
            "memory_effects", "privilege", "extensions", "feature_requirements",
            "exceptions", "semantic_id", "native_mapping", "compatibility_mapping",
            "encoding_status", "execution_status", "source_ref", "source_revision",
            "source_sha256", "license"
        ],
        "source_policy": "Records are imported only from supplied source files or the existing database. Missing encodings are null; no masks, execution semantics, or conformance claims are synthesized.",
        "instructions": final,
    }
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Universal ISA catalog: {len(final)} forms across {len(report['unique_architectures'])} architectures")
    print(json.dumps(report["coverage"], sort_keys=True))
    print(f"wrote {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
