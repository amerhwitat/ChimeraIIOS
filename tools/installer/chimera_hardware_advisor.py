#!/usr/bin/env python3
"""Explainable hardware recommendations for the Chimera II OS installer.

This is a conservative rules-based baseline. It consumes explicitly detected or
user-entered hardware facts; it does not guess unknown device properties or claim
that cataloged ISAs are supported by the installed kernel.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import platform
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "isa" / "isa_database.json"


def _arch_rows(db: dict[str, Any]) -> list[dict[str, Any]]:
    fields = ("id", "class", "family", "word_bits", "status", "encoding_model",
              "source_ref", "verified_form_count")
    return [dict(zip(fields, row)) for row in db.get("architectures", []) if isinstance(row, list)]


def recommend(db: dict[str, Any], hardware: dict[str, Any]) -> dict[str, Any]:
    """Rank only evidence-backed platform matches and expose unknowns as unknown."""
    archs = _arch_rows(db)
    detected = str(hardware.get("architecture") or "").strip().lower()
    aliases = {
        "amd64": "x86-64", "x86_64": "x86-64", "x64": "x86-64",
        "i386": "x86-32", "i686": "x86-32", "x86": "x86-32",
        "aarch64": "aarch64", "arm64": "aarch64", "armv7l": "arm32",
        "riscv64": "riscv64", "riscv32": "riscv32",
    }
    known_ids = {str(a["id"]).lower() for a in archs}
    canonical = aliases.get(detected)
    if canonical is None and detected in known_ids:
        canonical = detected
    exact = next((a for a in archs if a["id"].lower() == canonical), None)
    evidence = []
    if exact:
        evidence.append({
            "kind": "host-architecture-match", "architecture": exact["id"],
            "status": exact["status"], "verified_form_count": exact["verified_form_count"],
            "source_ref": exact["source_ref"],
            "interpretation": "Host architecture matches a database inventory entry; this alone does not prove kernel, driver, or binary compatibility."
        })
    else:
        evidence.append({
            "kind": "unknown-host-architecture", "architecture": canonical or None,
            "interpretation": "No exact host-architecture match found. Do not infer support."
        })

    ram_gib = hardware.get("ram_gib")
    storage_gib = hardware.get("storage_gib")
    free_storage_gib = hardware.get("free_storage_gib")
    firmware = str(hardware.get("firmware") or "unknown").lower()
    gpu = str(hardware.get("gpu") or "unknown")
    network = str(hardware.get("network") or "unknown")
    use_case = str(hardware.get("use_case") or "general").lower()
    constraints = []
    if not isinstance(ram_gib, (int, float)) or ram_gib <= 0:
        constraints.append({"field": "ram_gib", "status": "unknown", "message": "Detect or ask the user for RAM before sizing memory-heavy features."})
    if not isinstance(storage_gib, (int, float)) or storage_gib <= 0:
        constraints.append({"field": "storage_gib", "status": "unknown", "message": "Detect disk capacity and available space before installation or partition changes."})
    if firmware not in ("uefi", "bios", "unknown"):
        constraints.append({"field": "firmware", "status": "unrecognized", "message": "Confirm firmware boot mode using platform detection."})
    if gpu.lower() == "unknown":
        constraints.append({"field": "gpu", "status": "unknown", "message": "Identify GPU model and driver availability before enabling accelerated desktop features."})
    if network.lower() == "unknown":
        constraints.append({"field": "network", "status": "unknown", "message": "Verify network adapter and installer network support."})

    # Conservative, explainable tiers; these are recommendations, not hard minimums.
    if isinstance(ram_gib, (int, float)) and ram_gib > 0:
        if ram_gib < 2:
            ram_tier = ("minimal", "Very limited memory: use a lightweight live/recovery profile; disable optional services.")
        elif ram_gib < 4:
            ram_tier = ("basic", "Prefer a basic desktop and modest background services.")
        elif ram_gib < 8:
            ram_tier = ("standard", "A standard desktop profile is a reasonable starting point.")
        else:
            ram_tier = ("enhanced", "Memory headroom may permit optional desktop and development tools.")
    else:
        ram_tier = ("undetermined", "RAM is unknown; do not promise a profile until detected.")
    if isinstance(storage_gib, (int, float)) and storage_gib > 0:
        if storage_gib < 16:
            storage_tier = ("constrained", "Check the selected edition's measured footprint; do not proceed with destructive partitioning without explicit confirmation.")
        elif storage_gib < 64:
            storage_tier = ("basic", "Keep optional language packs, caches and development toolchains configurable.")
        else:
            storage_tier = ("roomy", "There may be room for optional developer packages, subject to actual free space.")
    else:
        storage_tier = ("undetermined", "Storage capacity is unknown; probe free space and partition layout before install.")
    if isinstance(free_storage_gib, (int, float)) and free_storage_gib >= 0:
        storage_note = f"Reported free space: {free_storage_gib:g} GiB; compare against the measured image/rootfs size plus safety margin."
    else:
        storage_note = "Free space is unknown; query the target filesystem before writing."

    recommendations = [
        {"area": "edition", "choice": "native-platform edition only when a matching, tested boot/kernel target exists",
         "reason": f"Detected/canonical architecture: {canonical or 'unknown'}. Database inventory is not a compatibility guarantee."},
        {"area": "memory-profile", "choice": ram_tier[0], "reason": ram_tier[1]},
        {"area": "storage-profile", "choice": storage_tier[0], "reason": storage_tier[1] + " " + storage_note},
        {"area": "graphics", "choice": "accelerated if a matching tested driver exists; otherwise safe fallback",
         "reason": f"GPU reported as {gpu}; driver support must be checked independently."},
        {"area": "network", "choice": "enable only detected and supported adapters",
         "reason": f"Network adapter reported as {network}; unknown devices must not be represented as supported."},
        {"area": "firmware", "choice": "match installer media and bootloader to detected firmware",
         "reason": f"Firmware mode: {firmware}."},
    ]
    if use_case in ("developer", "development", "ai", "ml"):
        recommendations.append({"area": "optional-packages", "choice": "offer toolchains/model runtimes as opt-in components",
                                "reason": "Use-case preference supplied; check RAM, storage, accelerator, and package availability before installation."})
    result = {
        "schema": "CHM-HARDWARE-ADVICE-1",
        "database_version": db.get("version"),
        "hardware_facts": {
            "architecture": hardware.get("architecture"), "canonical_architecture": canonical or None,
            "ram_gib": ram_gib, "storage_gib": storage_gib, "free_storage_gib": free_storage_gib,
            "firmware": firmware, "gpu": gpu, "network": network, "use_case": use_case,
            "cpu_model": hardware.get("cpu_model", "unknown"), "cpu_features": hardware.get("cpu_features", []),
            "secure_boot": hardware.get("secure_boot", "unknown"), "tpm": hardware.get("tpm", "unknown"),
            "battery_powered": hardware.get("battery_powered", "unknown"),
        },
        "isa_evidence": evidence,
        "recommendations": recommendations,
        "unknowns_and_checks": constraints,
        "safety": {
            "automatic_partitioning": False, "automatic_firmware_changes": False,
            "recommendation_is_not_support_proof": True,
            "require_user_confirmation_for_destructive_actions": True,
            "do_not_send_hardware_inventory_to_remote_model_without_consent": True,
        }
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=pathlib.Path, default=DEFAULT_DB)
    parser.add_argument("--facts", type=pathlib.Path, help="JSON file with installer-detected or user-entered hardware facts.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        db = json.loads(args.database.read_text(encoding="utf-8"))
        if args.facts:
            facts = json.loads(args.facts.read_text(encoding="utf-8"))
        else:
            facts = {"architecture": platform.machine(), "use_case": "general"}
        result = recommend(db, facts)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"chimera-hardware-advisor: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
