#!/usr/bin/env python3
"""Fail-closed verifier for the six-case Chimera production release evidence.

This checks declarations and SHA-256 linkage in a signed-off evidence manifest.
It does not create evidence, boot an image, or replace the underlying CI traces.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SCHEMA = "CHIMERA-PRODUCTION-ACCEPTANCE-1"
TARGETS = ("live", "installer", "recovery")
FIRMWARE = ("bios", "uefi")
HEX64 = re.compile(r"^[0-9a-f]{64}$")

REQUIRED_SYSTEM_GATES = {
    "scheduler": ("preemptive_context_switching", "two_cpu_overlap"),
    "storage": ("block_device_io", "persistent_vfs"),
    "installed_root": ("validated_mount_and_handoff",),
    "installer": ("partition_format_and_persistent_install",),
    "recovery": ("filesystem_repair_postcondition",),
    "services": ("supervised_pid1",),
    "desktops": ("aurora_native_session", "marine_native_session",
                 "freexp_native_session", "freewin11_native_session"),
    "catalogues": ("all_command_providers_verified", "all_claimed_isa_backends_conformant"),
}


class AcceptanceError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AcceptanceError(message)


def verify(document: object, iso_path: Path | None = None) -> dict:
    require(isinstance(document, dict), "acceptance manifest must be a JSON object")
    require(document.get("schema") == SCHEMA, f"schema must be {SCHEMA}")
    iso_sha = document.get("iso_sha256")
    require(isinstance(iso_sha, str) and HEX64.fullmatch(iso_sha) is not None,
            "iso_sha256 must be a lowercase 64-character SHA-256")
    if iso_path is not None:
        require(iso_path.is_file(), f"ISO file does not exist: {iso_path}")
        digest = hashlib.sha256()
        with iso_path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        actual = digest.hexdigest()
        require(actual == iso_sha, "acceptance ISO SHA-256 does not match the release ISO")

    cases = document.get("cases")
    require(isinstance(cases, list) and len(cases) == 6,
            "exactly six target/firmware cases are required")
    indexed = {}
    for case in cases:
        require(isinstance(case, dict), "each case must be an object")
        key = (case.get("target"), case.get("firmware"))
        require(key not in indexed, f"duplicate target/firmware case: {key}")
        indexed[key] = case
        require(case.get("iso_sha256") == iso_sha,
                f"{key}: ISO SHA-256 differs from the release ISO")
        trace_sha = case.get("firmware_trace_sha256")
        require(isinstance(trace_sha, str) and HEX64.fullmatch(trace_sha) is not None,
                f"{key}: firmware_trace_sha256 must be a lowercase SHA-256")
        for field in ("kernel_ready", "cpl3_init_ack", "matching_nonzero_pid1",
                      "persistent_runtime", "target_postcondition"):
            require(case.get(field) is True, f"{key}: {field} is not verified")
    expected = {(target, firmware) for target in TARGETS for firmware in FIRMWARE}
    require(set(indexed) == expected,
            "cases must cover Live, Installer and Recovery on both BIOS and UEFI")

    gates = document.get("system_gates")
    require(isinstance(gates, dict), "system_gates object is required")
    for group, fields in REQUIRED_SYSTEM_GATES.items():
        values = gates.get(group)
        require(isinstance(values, dict), f"system_gates.{group} object is required")
        for field in fields:
            require(values.get(field) is True,
                    f"system_gates.{group}.{field} is not verified")

    evidence = document.get("evidence")
    require(isinstance(evidence, list) and evidence,
            "at least one trace/build evidence reference is required")
    for item in evidence:
        require(isinstance(item, dict), "each evidence reference must be an object")
        require(isinstance(item.get("uri"), str) and item["uri"].strip(),
                "each evidence reference needs a non-empty uri")
        digest = item.get("sha256")
        require(isinstance(digest, str) and HEX64.fullmatch(digest) is not None,
                "each evidence reference needs a lowercase SHA-256")
    return {"iso_sha256": iso_sha, "cases": 6, "evidence_items": len(evidence)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--iso", type=Path)
    args = parser.parse_args()
    try:
        doc = json.loads(args.manifest.read_text(encoding="utf-8"))
        result = verify(doc, args.iso)
    except (OSError, json.JSONDecodeError, AcceptanceError) as exc:
        print(f"FAIL: production release acceptance: {exc}")
        return 1
    print("PASS: six-case BIOS/UEFI production acceptance manifest")
    print(f"PASS: iso_sha256={result['iso_sha256']}")
    print(f"PASS: cases={result['cases']} evidence_items={result['evidence_items']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
