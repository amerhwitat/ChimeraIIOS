#!/usr/bin/env python3
"""Fail-closed verifier for the six-case Chimera production release evidence.

This verifies declarations, candidate ISO bytes, and the bytes of every
locally staged evidence artifact. It does not create evidence, boot an image,
or replace review of the underlying CI traces.
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_evidence(root: Path, relative: object, label: str) -> Path:
    require(isinstance(relative, str) and relative.strip(),
            f"{label} needs a relative local path")
    relpath = Path(relative)
    require(not relpath.is_absolute() and ".." not in relpath.parts,
            f"{label} path must be relative and cannot traverse parent directories")
    try:
        artifact = (root / relpath).resolve(strict=True)
    except OSError as exc:
        raise AcceptanceError(f"{label} artifact is missing: {relative}") from exc
    require(artifact.is_relative_to(root),
            f"{label} artifact resolves outside the evidence root")
    require(artifact.is_file(), f"{label} artifact is not a file: {relative}")
    return artifact


def verify(document: object, iso_path: Path | None = None,
           evidence_root: Path | None = None) -> dict:
    require(isinstance(document, dict), "acceptance manifest must be a JSON object")
    require(document.get("schema") == SCHEMA, f"schema must be {SCHEMA}")
    iso_sha = document.get("iso_sha256")
    require(isinstance(iso_sha, str) and HEX64.fullmatch(iso_sha) is not None,
            "iso_sha256 must be a lowercase 64-character SHA-256")
    if iso_path is not None:
        require(iso_path.is_file(), f"ISO file does not exist: {iso_path}")
        require(sha256_file(iso_path) == iso_sha,
                "acceptance ISO SHA-256 does not match the release ISO")

    require(evidence_root is not None and evidence_root.is_dir(),
            "evidence_root must be an existing directory containing staged evidence files")
    root = evidence_root.resolve()

    cases = document.get("cases")
    require(isinstance(cases, list) and len(cases) == 6,
            "exactly six target/firmware cases are required")
    indexed = {}
    trace_paths = set()
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
        trace_path = case.get("firmware_trace_path")
        trace_file = resolve_evidence(root, trace_path, f"{key}: firmware trace")
        require(trace_path not in trace_paths,
                f"{key}: firmware trace path is reused by another case")
        trace_paths.add(trace_path)
        require(sha256_file(trace_file) == trace_sha,
                f"{key}: firmware trace SHA-256 does not match its artifact")
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
        uri = item.get("uri")
        require(isinstance(uri, str) and uri.strip(),
                "each evidence reference needs a non-empty uri")
        artifact = resolve_evidence(root, item.get("path"), "evidence")
        digest = item.get("sha256")
        require(isinstance(digest, str) and HEX64.fullmatch(digest) is not None,
                "each evidence reference needs a lowercase SHA-256")
        require(sha256_file(artifact) == digest,
                f"evidence artifact SHA-256 does not match: {item['path']}")
    return {"iso_sha256": iso_sha, "cases": 6, "evidence_items": len(evidence)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--iso", type=Path)
    args = parser.parse_args()
    try:
        doc = json.loads(args.manifest.read_text(encoding="utf-8"))
        result = verify(doc, args.iso, args.manifest.resolve().parent)
    except (OSError, json.JSONDecodeError, AcceptanceError) as exc:
        print(f"FAIL: production release acceptance: {exc}")
        return 1
    print("PASS: six-case BIOS/UEFI production acceptance manifest")
    print(f"PASS: iso_sha256={result['iso_sha256']}")
    print(f"PASS: cases={result['cases']} evidence_items={result['evidence_items']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
