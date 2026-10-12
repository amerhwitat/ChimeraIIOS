#!/usr/bin/env python3
"""Import actual LLVM TableGen JSON records into a provenance-preserving catalog.

Generate inputs with the matching target's LLVM TableGen build (for example,
llvm-tblgen -dump-json target-instructions.td). This tool imports records; it
does not infer instruction encodings or claim execution/conformance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ARCHITECTURES = {
    "x86", "x86-64", "arm32", "aarch64", "powerpc", "ppc64", "mips32",
    "mips64", "sparc", "sparc-v9", "loongarch32", "loongarch64",
    "riscv32", "riscv64", "s390x", "m68k", "alpha", "hppa", "sh4",
    "xtensa", "avr", "openrisc",
}
INSTRUCTION_CLASSES = ("Instruction", "Inst", "PseudoInst")


def _record_names(document: dict[str, Any]) -> list[str]:
    """Read LLVM's !instanceof class index when present, with a cautious fallback."""
    index = document.get("!instanceof")
    if isinstance(index, dict):
        names: set[str] = set()
        for class_name in INSTRUCTION_CLASSES:
            values = index.get(class_name, [])
            if isinstance(values, list):
                names.update(x for x in values if isinstance(x, str))
        if names:
            return sorted(names)
    return sorted(
        key for key, value in document.items()
        if not key.startswith("!") and isinstance(value, dict)
        and any(k in value for k in ("AsmString", "Inst", "Opcode", "Namespace"))
    )


def import_target(architecture: str, path: Path, source_url: str,
                  source_revision: str, source_license: str) -> list[dict[str, Any]]:
    if architecture not in ARCHITECTURES:
        raise ValueError(f"unsupported architecture identifier: {architecture}")
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    document = json.loads(raw.decode("utf-8"))
    if not isinstance(document, dict):
        raise ValueError(f"{path}: LLVM TableGen dump must be a JSON object")
    result = []
    for record_name in _record_names(document):
        record = document.get(record_name)
        if not isinstance(record, dict):
            continue
        asm = record.get("AsmString")
        mnemonic = None
        if isinstance(asm, str) and asm.strip():
            mnemonic = asm.strip().split()[0].strip('"')
        if not mnemonic:
            candidate = record.get("Mnemonic")
            if isinstance(candidate, str) and candidate.strip():
                mnemonic = candidate.strip()
        if not mnemonic:
            # Keep the raw record in the output rather than inventing a mnemonic.
            mnemonic = record_name
        result.append({
            "architecture": architecture,
            "mnemonic": mnemonic,
            "form_id": record_name,
            "source_record": record_name,
            "syntax": asm if isinstance(asm, str) else None,
            "encoding_source_fields": {
                key: record[key] for key in ("Inst", "Opcode", "Size", "TSFlags")
                if key in record
            },
            "operand_source_fields": {
                key: record[key] for key in (
                    "InOperandList", "OutOperandList", "Operands", "Constraints"
                ) if key in record
            },
            "effect_source_fields": {
                key: record[key] for key in (
                    "Uses", "Defs", "mayLoad", "mayStore", "isBranch",
                    "isCall", "isReturn", "hasSideEffects"
                ) if key in record
            },
            "effects": {
                "registers_read": "unknown",
                "registers_written": "unknown",
                "flags_read": "unknown",
                "flags_written": "unknown",
                "memory_read": "unknown",
                "memory_written": "unknown",
                "exceptions": "unknown",
                "privilege": "unknown",
                "extensions": "unknown",
                "endianness": "unknown",
            },
            "source_provenance": {
                "source_url": source_url,
                "source_revision": source_revision,
                "source_license": source_license,
                "input_file": str(path),
                "input_sha256": digest,
            },
            "status": "catalog-only",
            "encoding_verified": False,
            "execution_implemented": False,
            "conformance_tested": False,
            "llvm_tablegen_fields": record,
        })
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", required=True, metavar="ARCH=JSON",
                        help="LLVM -dump-json output; repeat for each target")
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--source-revision", required=True,
                        help="immutable LLVM commit SHA or release identifier")
    parser.add_argument("--source-license", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rows: list[dict[str, Any]] = []
    for item in args.input:
        if "=" not in item:
            parser.error(f"--input must be ARCH=JSON, got {item!r}")
        arch, filename = item.split("=", 1)
        rows.extend(import_target(arch, Path(filename), args.source_url,
                                  args.source_revision, args.source_license))
    output = {
        "schema": "chimera-llvm-tablegen-import-v2",
        "instruction_count": len(rows),
        "status_policy": "Imported records are catalog-only; unknown effects remain unknown.",
        "instructions": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Imported {len(rows)} actual LLVM TableGen instruction records into {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
