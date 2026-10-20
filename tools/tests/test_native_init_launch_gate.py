#!/usr/bin/env python3
"""Regression guard for fail-closed native init ELF dispatch.

This source-contract test prevents production payloads from being reported as
successfully handled when no native USER_INIT_ELF module is supplied. It is
not a runtime boot test and does not establish production readiness.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
LAUNCH = ROOT / "kernel/core/target_launch.cpp"
BOOTSTRAP = ROOT / "kernel/core/koronos.cpp"


def fail(message: str) -> int:
    print(f"NATIVE INIT LAUNCH GATE FAIL: {message}", file=sys.stderr)
    return 1


def main() -> int:
    launch = LAUNCH.read_text(encoding="utf-8")
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")

    if "if (count==0)" not in launch:
        return fail("missing explicit zero-USER_INIT_ELF branch")
    zero_branch = launch.split("if (count==0)", 1)[1].split(
        "if (count!=1", 1
    )[0]
    for required in (
        "CHIMERA_MODULE_LIVE_INITRAMFS",
        "CHIMERA_MODULE_RECOVERY_INITRAMFS",
        "CHIMERA_MODULE_INSTALL_IMAGE",
        "if (!has_target_payload) return 0;",
        "no USER_INIT_ELF module was supplied",
        "return -12;",
    ):
        if required not in zero_branch:
            return fail(f"zero-module production failure contract missing: {required}")

    for target, marker in (
        ("live", "CHIMERA_MODULE_LIVE_INITRAMFS"),
        ("recovery", "CHIMERA_MODULE_RECOVERY_INITRAMFS"),
        ("installer", "CHIMERA_MODULE_INSTALL_IMAGE"),
    ):
        if marker not in bootstrap:
            return fail(f"{target} payload recognition is missing")
        diagnostic = target.capitalize() + " payload has no launchable production init ELF"
        if diagnostic not in bootstrap:
            return fail(f"{target} missing-init failure diagnostic is missing")

    build_path = ROOT / "kernel/build-koronos.sh"
    build = build_path.read_text(encoding="utf-8")
    if "user-init-${target}.elf" in build and not ("acceptance probes" in build and "not production shells" in build):
        return fail("smoke probe artifacts are not explicitly isolated from production")

    print("NATIVE INIT LAUNCH GATE PASS: missing production ELF fails closed; probes remain isolated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
