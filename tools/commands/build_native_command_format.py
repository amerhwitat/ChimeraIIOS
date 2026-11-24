#!/usr/bin/env python3
"""Build CHMCMD v1 native command-object records from the normalized catalogue.

One binary record is emitted per catalogue command. Implementation status is
copied from verified provider data only; catalog metadata cannot promote a row.
Records with empty operand/option/register descriptors are rejected.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

from chmcmd_format import ARCH_IDS, FILE_MAGIC, FILE_VERSION, FormatError, pack_file

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOGUE = ROOT / "system/commands/native-command-catalog.json"
DEFAULT_OUTPUT = ROOT / "build/native-command-format/native-commands.chmcmd"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--reference-arch", choices=sorted(ARCH_IDS), default="x86_64")
    args = parser.parse_args()

    if not args.catalogue.is_file():
        raise SystemExit(f"missing catalogue: {args.catalogue}")

    document = json.loads(args.catalogue.read_text(encoding="utf-8"))
    if document.get("schema") != "CHM-NATIVE-COMMAND-CATALOG-1":
        raise SystemExit("unsupported catalogue schema")
    if document.get("full_conformance") or document.get("conformance_claim"):
        raise SystemExit("catalogue illegally claims conformance")

    rows = document["records"]
    if len(rows) != document["record_count"]:
        raise SystemExit("catalogue record_count mismatch")

    try:
        data = pack_file(rows, args.reference_arch)
    except FormatError as exc:
        raise SystemExit(f"cannot build CHMCMD record: {exc}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)

    manifest = {
        "schema": "CHM-NATIVE-COMMAND-FORMAT-BUILD-1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "format": FILE_MAGIC.decode("ascii"),
        "format_version": FILE_VERSION,
        "catalogue": str(args.catalogue.relative_to(ROOT)
                         if args.catalogue.is_relative_to(ROOT) else args.catalogue),
        "reference_arch": args.reference_arch,
        "record_count": len(rows),
        "implemented_records": sum(
            1 for row in rows if row["implementation"] != "not_implemented"
        ),
        "not_implemented_records": sum(
            1 for row in rows if row["implementation"] == "not_implemented"
        ),
        "rows_with_operands": sum(1 for row in rows if row["operands"]),
        "rows_with_options": sum(1 for row in rows if row["options"]),
        "rows_with_effects_on_registers": sum(
            1 for row in rows if row["effects_on_registers"]
        ),
        "rows_with_register_effects_status_object": sum(
            1 for row in rows if isinstance(row["register_effects_status"], dict)
        ),
        "binary": str(args.output.relative_to(args.output.parent.parent)
                      if args.output.is_relative_to(ROOT) else args.output),
        "byte_length": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "official_status_snapshot": document["official_status_snapshot"],
        "conformance_claim": False,
        "production_acceptance": False,
    }
    manifest_path = args.output.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8")

    print(json.dumps({
        "record_count": len(rows),
        "implemented": manifest["implemented_records"],
        "not_implemented": manifest["not_implemented_records"],
        "descriptor_counts": {
            key: manifest[key] for key in (
                "rows_with_operands", "rows_with_options",
                "rows_with_effects_on_registers",
                "rows_with_register_effects_status_object",
            )
        },
        "bytes": len(data),
        "output": str(args.output),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
