#!/usr/bin/env python3
"""Run a staged Chimera multicall command for a Linux ABI using QEMU user mode.

This is a hosted-Linux compatibility runner. It does not execute Linux ELF files
inside the native Koronos kernel and never claims Koronos ABI compatibility.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

MANIFEST = Path("/usr/share/chimera/catalogs/linux-abi-command-matrix.json")
BIN_ROOT = Path("/usr/lib/chimera/commands/linux-abi")
QEMU = {
    "i686": "qemu-i386-static",
    "armel": "qemu-arm-static",
    "aarch64": "qemu-aarch64-static",
    "armv7": "qemu-arm-static",
    "riscv64": "qemu-riscv64-static",
    "ppc64le": "qemu-ppc64le-static",
    "s390x": "qemu-s390x-static",
}


def usage() -> None:
    print("Usage: chimera-run-abi <x86_64|i686|armel|aarch64|armv7|riscv64|ppc64le|s390x> <command> [args...]")
    print("       chimera-run-abi --list")
    print("Runs a staged Linux-ABI command; this is not a Koronos-native executable loader.")


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        usage()
        return 0 if argv else 2
    if argv[0] == "--list":
        try:
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"chimera-run-abi: cannot read ABI manifest: {exc}", file=sys.stderr)
            return 1
        for row in manifest.get("targets", []):
            if row.get("binary_status") == "cross-compiled-and-elf-machine-validated":
                print(f'{row["target"]}: {len(row.get("aliases", []))} commands')
        return 0
    if len(argv) < 2:
        usage()
        return 2

    arch, command, *args = argv
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"chimera-run-abi: cannot read ABI manifest: {exc}", file=sys.stderr)
        return 1
    target = next((row for row in manifest.get("targets", []) if row.get("target") == arch), None)
    if not target or target.get("binary_status") != "cross-compiled-and-elf-machine-validated":
        print(f"chimera-run-abi: ABI is not built and ELF-validated: {arch}", file=sys.stderr)
        return 2
    if command not in target.get("aliases", []):
        print(f"chimera-run-abi: command is not in the {arch} multicall manifest: {command}", file=sys.stderr)
        return 2

    executable = BIN_ROOT / arch / command
    if not executable.is_file() or not os.access(executable, os.X_OK):
        print(f"chimera-run-abi: staged executable is missing: {executable}", file=sys.stderr)
        return 127

    runner = QEMU.get(arch)
    if runner:
        qemu = shutil.which(runner)
        if not qemu:
            print(f"chimera-run-abi: install qemu-user-static; missing {runner}", file=sys.stderr)
            return 127
        os.execv(qemu, [qemu, str(executable), *args])
    os.execv(str(executable), [str(executable), *args])
    return 127


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
