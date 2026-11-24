#!/usr/bin/env python3
"""Validate a CHMCMD v1 file and, optionally, cross-check its catalogue rows.

Malformed records are rejected with a nonzero exit code. A record is never
accepted as implemented unless it carries provider symbols and the matching
provider function exists in the real multicall source. Every row must have
non-empty structured operand, option and register-effect descriptors.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from chmcmd_format import FILE_MAGIC, FILE_VERSION, FormatError, unpack_file

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BINARY = ROOT / "build/native-command-format/native-commands.chmcmd"
DEFAULT_CATALOGUE = ROOT / "system/commands/native-command-catalog.json"
DEFAULT_SOURCE = ROOT / "src/chimera-command-compat/chimera-cmd.c"
EXPECTED_OFFICIAL = {"status": "not-run", "conformance_tested": 0, "not_implemented": 1613}


def describe_missing(row: dict) -> list[str]:
    problems = []
    for field in ("operands", "options"):
        value = row.get(field)
        if not isinstance(value, list) or not value:
            problems.append(f"{field} is empty or not a list")
        elif any(not isinstance(item, dict) or not item for item in value):
            problems.append(f"{field} contains non-object or empty descriptors")
    value = row.get("effects_on_registers")
    if not isinstance(value, dict) or not value:
        problems.append("effects_on_registers is empty or not an object")
    value = row.get("register_effects_status")
    if not isinstance(value, dict) or not value:
        problems.append("register_effects_status is empty or not an object")
    return problems


def fail(error: str) -> int:
    print(json.dumps({"valid": False, "error": error}), file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--no-cross-check", action="store_true")
    args = parser.parse_args()

    if not args.binary.is_file():
        raise SystemExit(f"missing binary: {args.binary}")

    try:
        header, records = unpack_file(args.binary.read_bytes())
    except FormatError as exc:
        return fail(str(exc))

    summary = {
        "valid": True,
        "format": header["magic"],
        "version": header["version"],
        "record_count": header["record_count"],
        "implemented": sum(1 for row in records
                           if row["implementation"] != "not_implemented"),
        "not_implemented": sum(1 for row in records
                               if row["implementation"] == "not_implemented"),
        "rows_with_operands": sum(1 for row in records if row["operands"]),
        "rows_with_options": sum(1 for row in records if row["options"]),
        "rows_with_effects_on_registers": sum(
            1 for row in records if row["effects_on_registers"]
        ),
        "rows_with_register_effects_status_object": sum(
            1 for row in records if isinstance(row["register_effects_status"], dict)
        ),
        "cross_checked": False,
        "conformance_claim": False,
    }

    if header["magic"] != FILE_MAGIC.decode("ascii") or header["version"] != FILE_VERSION:
        return fail("unexpected header")

    for record in records:
        problems = describe_missing(record)
        if problems:
            return fail(f"{record['name']}: " + "; ".join(problems))

    if not args.no_cross_check:
        catalogue = json.loads(args.catalogue.read_text(encoding="utf-8"))
        source = args.source.read_text(encoding="utf-8")
        rows = catalogue["records"]

        if len(rows) != len(records):
            return fail("catalogue/binary count mismatch")

        verified_providers = set()
        for row in rows:
            problems = describe_missing(row)
            if problems:
                return fail(f"catalogue {row['name']}: " + "; ".join(problems))
            if row["implementation"] == "not_implemented":
                continue
            provider = row["implementation_details"]["function"]
            if f'strcmp(cmd, "{row["name"]}")' not in source:
                return fail(f"no dispatch for {row['name']}")
            if f"static int {provider}(" not in source:
                return fail(f"no provider function {provider}")
            verified_providers.add(row["name"])

        for catalog_row, binary_row in zip(rows, records):
            if catalog_row["name"] != binary_row["name"]:
                return fail("row order mismatch")
            if catalog_row["implementation"] != binary_row["implementation"]:
                return fail(f"implementation mismatch: {catalog_row['name']}")
            for field in ("operands", "options", "effects_on_registers",
                          "register_effects_status"):
                if catalog_row[field] != binary_row[field]:
                    return fail(f"{field} mismatch: {catalog_row['name']}")
            if binary_row["implementation"] != "not_implemented" and (
                    not binary_row["symbols"] or binary_row["implementation_reason"]):
                return fail(f"invalid implemented record: {catalog_row['name']}")
            if binary_row["implementation"] == "not_implemented" and (
                    binary_row["symbols"] or not binary_row["implementation_reason"]):
                return fail(f"invalid unimplemented record: {catalog_row['name']}")

        official = catalogue["official_status_snapshot"]
        if any(official.get(key) != value for key, value in EXPECTED_OFFICIAL.items()):
            return fail("official status was altered")

        summary["cross_checked"] = True
        summary["verified_providers"] = len(verified_providers)

    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
