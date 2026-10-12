#!/usr/bin/env python3
"""Validate capability claims and evidence links without promoting maturity."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs" / "validation" / "capability-evidence.json"
ALLOWED = {
    "documented", "cataloged", "implemented", "compiled", "booted",
    "userspace-ready", "conformance-tested", "partial", "planned",
    "not-implemented", "not-verified",
}
PROMOTED = {"implemented", "compiled", "booted", "userspace-ready", "conformance-tested"}


def validate(registry: dict) -> list[str]:
    errors: list[str] = []
    if registry.get("schema") != "CHM-CAPABILITY-EVIDENCE-1":
        errors.append("unsupported capability evidence schema")
    if registry.get("version") != 1:
        errors.append("unsupported capability evidence version")
    caps = registry.get("capabilities")
    if not isinstance(caps, list) or not caps:
        return errors + ["capabilities must be a non-empty list"]
    ids: set[str] = set()
    for cap in caps:
        if not isinstance(cap, dict):
            errors.append("each capability must be an object")
            continue
        cid = cap.get("id")
        if not isinstance(cid, str) or not cid:
            errors.append("capability is missing a non-empty id")
            continue
        if cid in ids:
            errors.append(f"duplicate capability id: {cid}")
        ids.add(cid)
        status = cap.get("status")
        if status not in ALLOWED:
            errors.append(f"{cid}: invalid status {status!r}")
        evidence = cap.get("evidence", [])
        if not isinstance(evidence, list):
            errors.append(f"{cid}: evidence must be a list")
            continue
        if status in PROMOTED and not evidence:
            errors.append(f"{cid}: promoted status requires evidence")
        for item in evidence:
            if not isinstance(item, dict):
                errors.append(f"{cid}: evidence entries must be objects")
                continue
            kind, ref, claim = item.get("kind"), item.get("ref"), item.get("claim")
            if not all(isinstance(v, str) and v.strip() for v in (kind, ref, claim)):
                errors.append(f"{cid}: evidence needs kind, ref and claim")
                continue
            target = ROOT / ref
            if not target.exists():
                errors.append(f"{cid}: evidence reference does not exist: {ref}")
        if cid == "real-smp":
            if status in PROMOTED:
                errors.append("real-smp: cannot promote without a dedicated SMP evidence bundle")
            if cap.get("sequential_simulation_counts_as_smp", False):
                errors.append("real-smp: sequential simulation must never count as SMP")
    principles = set(registry.get("principles", []))
    required = {
        "documented-is-not-implemented",
        "cataloged-is-not-executable",
        "compiled-is-not-booted",
        "booted-is-not-userspace-ready",
        "sequential-multicpu-simulation-is-not-smp",
    }
    missing = required - principles
    if missing:
        errors.append("missing required principles: " + ", ".join(sorted(missing)))
    rules = registry.get("promotion_rules", {})
    for stage in ("compiled", "booted", "userspace-ready", "conformance-tested", "real-smp"):
        if not rules.get(stage):
            errors.append(f"missing promotion requirements for {stage}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    try:
        registry = json.loads(args.registry.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[capability-status] ERROR: cannot read registry: {exc}", file=sys.stderr)
        return 2
    errors = validate(registry)
    if errors:
        for error in errors:
            print(f"[capability-status] ERROR: {error}", file=sys.stderr)
        return 1
    if not args.quiet:
        print(f"[capability-status] OK: {len(registry['capabilities'])} capabilities; no maturity inferred from catalog presence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
