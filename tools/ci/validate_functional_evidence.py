#!/usr/bin/env python3
"""Validate machine-generated functional evidence without trusting PASS labels alone.

The producing test harness must include a non-empty run ID, target, test name,
an explicit true result, and a SHA-256 digest of the associated raw trace.
This schema validator does not execute tests; absent artifacts fail closed.
"""
from __future__ import annotations
import hashlib
import json
import pathlib
import sys

REQUIRED = ("schema_version", "test", "target", "run_id", "passed", "trace_path", "trace_sha256")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_functional_evidence.py evidence.json", file=sys.stderr)
        return 2
    path = pathlib.Path(sys.argv[1])
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INVALID EVIDENCE: {path}: {exc}", file=sys.stderr)
        return 1
    missing = [key for key in REQUIRED if key not in data]
    if missing:
        print(f"INVALID EVIDENCE: missing fields: {', '.join(missing)}", file=sys.stderr)
        return 1
    if data["schema_version"] != 1 or data["passed"] is not True:
        print("INVALID EVIDENCE: unsupported schema or test did not pass", file=sys.stderr)
        return 1
    for key in ("test", "target", "run_id"):
        if not isinstance(data[key], str) or not data[key].strip():
            print(f"INVALID EVIDENCE: {key} must be a non-empty string", file=sys.stderr)
            return 1
    trace = pathlib.Path(data["trace_path"])
    if not trace.is_absolute():
        trace = path.parent / trace
    try:
        digest = hashlib.sha256(trace.read_bytes()).hexdigest()
    except OSError as exc:
        print(f"INVALID EVIDENCE: trace unavailable: {exc}", file=sys.stderr)
        return 1
    if not isinstance(data["trace_sha256"], str) or digest != data["trace_sha256"].lower():
        print("INVALID EVIDENCE: trace SHA-256 mismatch", file=sys.stderr)
        return 1
    print(f"EVIDENCE STRUCTURE PASS: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
