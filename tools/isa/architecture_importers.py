#!/usr/bin/env python3
"""Strict, provenance-aware adapters for normalized ISA instruction-form data.

This module deliberately does not scrape or infer encodings from prose. Source-
specific importers should convert a versioned machine-readable source into this
schema, then call validate_form(). A validated row is still catalog data, not
proof that Chimera can decode, execute, or conform to the instruction.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SUPPORTED_FAMILIES = {
    "x86", "x86-64", "arm32", "aarch64", "powerpc", "ppc64",
    "mips32", "mips64", "sparc", "sparc-v9", "loongarch32",
    "loongarch64", "riscv32", "riscv64", "s390x", "m68k",
    "alpha", "hppa", "sh4", "xtensa", "avr", "openrisc",
}
REQUIRED_PROVENANCE = ("source_url", "source_revision", "source_license", "retrieved_sha256")
EFFECT_KEYS = (
    "registers_read", "registers_written", "flags_read", "flags_written",
    "memory_read", "memory_written", "exceptions", "privilege",
    "extensions", "endianness",
)


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_form(row: dict[str, Any]) -> list[str]:
    """Return validation errors; never silently fill in missing architecture facts."""
    errors: list[str] = []
    for key in ("architecture", "mnemonic", "form_id", "encoding", "operands", "provenance"):
        if key not in row:
            errors.append(f"missing required field: {key}")
    arch = row.get("architecture")
    if arch not in SUPPORTED_FAMILIES:
        errors.append(f"unsupported or unnormalized architecture identifier: {arch!r}")
    if not _nonempty(row.get("mnemonic")):
        errors.append("mnemonic must be a non-empty string")
    if not _nonempty(row.get("form_id")):
        errors.append("form_id must be a stable, non-empty source identifier")
    enc = row.get("encoding")
    if not isinstance(enc, dict):
        errors.append("encoding must be an object")
    else:
        length = enc.get("length_bits")
        value = enc.get("value")
        mask = enc.get("mask")
        if not isinstance(length, int) or length <= 0 or length > 2048:
            errors.append("encoding.length_bits must be an integer in 1..2048")
        elif length % 8:
            errors.append("encoding.length_bits must be byte-aligned for an instruction form")
        else:
            limit = (1 << length) - 1
            if not isinstance(value, int) or value < 0 or value > limit:
                errors.append("encoding.value must fit the declared instruction length")
            if not isinstance(mask, int) or mask < 0 or mask > limit:
                errors.append("encoding.mask must fit the declared instruction length")
            if isinstance(value, int) and isinstance(mask, int) and value & ~mask:
                errors.append("encoding.value sets bits outside encoding.mask")
        byte_order = enc.get("byte_order")
        if byte_order not in ("little", "big", "mixed", "architecture-defined"):
            errors.append("encoding.byte_order must be explicit")
        if not _nonempty(enc.get("source_expression")):
            errors.append("encoding.source_expression must preserve the source's encoding rule")
    operands = row.get("operands")
    if not isinstance(operands, list):
        errors.append("operands must be a list")
    elif any(not isinstance(op, dict) or not _nonempty(op.get("kind")) for op in operands):
        errors.append("each operand must be an object with a non-empty kind")
    provenance = row.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("provenance must be an object")
    else:
        for key in REQUIRED_PROVENANCE:
            if not _nonempty(provenance.get(key)):
                errors.append(f"provenance.{key} must be present and non-empty")
    effects = row.get("effects")
    if not isinstance(effects, dict):
        errors.append("effects must be an object; use explicit unknown values rather than guessing")
    else:
        for key in EFFECT_KEYS:
            if key not in effects:
                errors.append(f"effects.{key} is missing; use [] or 'unknown' explicitly")
            elif key == "endianness":
                if effects[key] not in ("little", "big", "mixed", "architecture-defined", "unknown"):
                    errors.append("effects.endianness must explicitly describe data-memory endianness")
            elif not (isinstance(effects[key], list) or effects[key] == "unknown"):
                errors.append(f"effects.{key} must be a list or the literal 'unknown'")
    status = row.get("status", "catalog-only")
    if status not in ("catalog-only", "encoding-verified", "decoded", "executed", "conformance-tested"):
        errors.append(f"invalid status: {status!r}")
    if status in ("decoded", "executed", "conformance-tested") and not _nonempty(row.get("implementation_ref")):
        errors.append(f"status {status!r} requires implementation_ref evidence")
    if status == "conformance-tested" and not _nonempty(row.get("conformance_test_ref")):
        errors.append("conformance-tested status requires conformance_test_ref evidence")
    return errors


def import_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                rejected.append({"line": line_no, "errors": [f"invalid JSON: {exc.msg}"]})
                continue
            if not isinstance(row, dict):
                rejected.append({"line": line_no, "errors": ["each JSONL record must be an object"]})
                continue
            errors = validate_form(row)
            if errors:
                rejected.append({"line": line_no, "id": row.get("form_id"), "errors": errors})
            else:
                accepted.append(row)
    return accepted, rejected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSONL with normalized, source-backed instruction forms")
    parser.add_argument("--output", type=Path, help="write accepted forms as JSON")
    args = parser.parse_args()
    accepted, rejected = import_jsonl(args.input)
    result = {"schema": "CHIMERA-ISA-FORM-IMPORT-1", "accepted": accepted,
              "rejected": rejected, "counts": {"accepted": len(accepted), "rejected": len(rejected)},
              "policy": "Validation is schema/provenance validation, not architectural verification or conformance."}
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(serialized, encoding="utf-8")
    else:
        print(serialized, end="")
    return 1 if rejected else 0


if __name__ == "__main__":
    raise SystemExit(main())
