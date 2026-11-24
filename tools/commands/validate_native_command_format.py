#!/usr/bin/env python3
"""Validate a CHMCMD v1 file and, optionally, cross-check its catalogue rows.

Malformed records are rejected with a nonzero exit code. A record is never
accepted as implemented unless it carries provider symbols and the matching
provider function exists in the real multicall source.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from chmcmd_format import FILE_MAGIC, FILE_VERSION, FormatError, unpack_file

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BINARY = ROOT / "build/native-command-format/native-commands.chmcmd"
DEFAULT_CATALOGUE = ROOT / "system/commands/native-command-catalog.json"
DEFAULT_SOURCE = ROOT / "src/chimera-command-compat/chimera-cmd.c"
EXPECTED_OFFICIAL = {"status": "not-run", "conformance_tested": 0, "not_implemented": 1613}


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
        print(json.dumps({"valid": False, "error": str(exc)}), file=sys.stderr)
        return 1

    summary = {
        "valid": True,
        "format": header["magic"],
        "version": header["version"],
        "record_count": header["record_count"],
        "implemented": sum(1 for row in records
                           if row["implementation"] != "not_implemented"),
        "not_implemented": sum(1 for row in records
                               if row["implementation"] == "not_implemented"),
        "cross_checked": False,
        "conformance_claim": False,
    }

    if header["magic"] != FILE_MAGIC.decode("ascii") or header["version"] != FILE_VERSION:
        print(json.dumps({"valid": False, "error": "unexpected header"}), file=sys.stderr)
        return 1

    if not args.no_cross_check:
        catalogue = json.loads(args.catalogue.read_text(encoding="utf-8"))
        source = args.source.read_text(encoding="utf-8")
        rows = catalogue["records"]

        if len(rows) != len(records):
            print(json.dumps({"valid": False, "error": "catalogue/binary count mismatch"}),
                  file=sys.stderr)
            return 1

        verified_providers = set()
        for row in rows:
            if row["implementation"] == "not_implemented":
                continue
            provider = row["implementation_details"]["function"]
            if f'strcmp(cmd, "{row["name"]}")' not in source:
                print(json.dumps({"valid": False,
                                  "error": f"no dispatch for {row['name']}"}),
                      file=sys.stderr)
                return 1
            if f"static int {provider}(" not in source:
                print(json.dumps({"valid": False,
                                  "error": f"no provider function {provider}"}),
                      file=sys.stderr)
                return 1
            verified_providers.add(row["name"])

        for catalog_row, binary_row in zip(rows, records):
            if catalog_row["name"] != binary_row["name"]:
                print(json.dumps({"valid": False, "error": "row order mismatch"}),
                      file=sys.stderr)
                return 1
            if catalog_row["implementation"] != binary_row["implementation"]:
                print(json.dumps({"valid": False,
                                  "error": f"implementation mismatch: {catalog_row['name']}"}),
                      file=sys.stderr)
                return 1
            if binary_row["implementation"] != "not_implemented" and (
                    not binary_row["symbols"] or binary_row["implementation_reason"]):
                print(json.dumps({"valid": False,
                                  "error": f"invalid implemented record: {catalog_row['name']}"}),
                      file=sys.stderr)
                return 1
            if binary_row["implementation"] == "not_implemented" and (
                    binary_row["symbols"] or not binary_row["implementation_reason"]):
                print(json.dumps({"valid": False,
                                  "error": f"invalid unimplemented record: {catalog_row['name']}"}),
                      file=sys.stderr)
                return 1

        official = catalogue["official_status_snapshot"]
        if any(official.get(key) != value for key, value in EXPECTED_OFFICIAL.items()):
            print(json.dumps({"valid": False, "error": "official status was altered"}),
                  file=sys.stderr)
            return 1

        summary["cross_checked"] = True
        summary["verified_providers"] = len(verified_providers)

    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
