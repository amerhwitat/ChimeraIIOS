#!/usr/bin/env python3
"""Capability-gated launcher for QEMU system emulation in Chimera II.

This is a host-side orchestration tool, not a hypervisor or CPU emulator itself.
It never invokes a shell and only launches a fixed, allow-listed QEMU binary.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "tools/virtualization/hypervisor-backends.json"
ACCELERATORS = {"auto", "tcg", "kvm"}


def load_registry(path=REGISTRY):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != "CHM-HYPERVISOR-BACKENDS-1":
        raise ValueError("unsupported hypervisor registry schema")
    ids = [x["id"] for x in data.get("backends", [])]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate backend id")
    return data


def probe(registry=None, which=shutil.which, kvm_path=Path("/dev/kvm")):
    registry = registry or load_registry()
    result = []
    for item in registry["backends"]:
        binary_name = item.get("binary")
        binary = which(binary_name) if item.get("enabled") and binary_name else None
        accelerators = list(item.get("accelerators", [])) if binary else []
        if binary and "kvm" in accelerators and not kvm_path.exists():
            accelerators.remove("kvm")
        result.append({
            "id": item["id"], "family": item["family"],
            "available": bool(binary) if item.get("binary") else False,
            "binary": binary, "accelerators": accelerators,
            "reason": item.get("reason") if not binary else None
        })
    return result


def build_command(backend_id, accelerator="auto", memory="512M", disk=None,
                  cdrom=None, firmware_kernel=None, headless=True, registry=None,
                  which=shutil.which, kvm_path=Path("/dev/kvm"), profile=None, vcpus=1,
                  profiles_path=ROOT / "tools/virtualization/machine-profiles.json"):
    if accelerator not in ACCELERATORS:
        raise ValueError("accelerator must be auto, tcg, or kvm")
    registry = registry or load_registry()
    item = next((x for x in registry["backends"] if x["id"] == backend_id), None)
    if item is None:
        raise ValueError("unknown backend id")
    if not item.get("enabled") or not item.get("binary"):
        raise ValueError(item.get("reason", "backend disabled pending implementation"))
    binary = which(item["binary"])
    if not binary:
        raise FileNotFoundError("required QEMU binary not installed: " + item["binary"])
    supported = item.get("accelerators", [])
    if accelerator == "kvm":
        if "kvm" not in supported or not kvm_path.exists():
            raise RuntimeError("KVM unavailable for this target/host; select auto or tcg")
        selected = "kvm"
    elif accelerator == "tcg":
        if "tcg" not in supported:
            raise RuntimeError("TCG is not declared for this target")
        selected = "tcg"
    else:
        selected = "kvm" if "kvm" in supported and kvm_path.exists() else "tcg"
        if selected not in supported:
            raise RuntimeError("no supported accelerator is available for this backend")
    if type(vcpus) is not int or not 1 <= vcpus <= 4:
        raise ValueError("vcpus must be between 1 and 4")
    args = [binary, "-accel", selected, "-m", memory, "-smp", str(vcpus),
            "-display", "none" if headless else "gtk"]
    if profile:
        profile_data = json.loads(Path(profiles_path).read_text(encoding="utf-8"))
        chosen = next((p for p in profile_data.get("profiles", [])
                       if p.get("id") == profile and p.get("backend") == backend_id), None)
        if chosen is None:
            raise ValueError("unknown or mismatched machine profile")
        args += ["-machine", chosen["machine"], "-cpu", chosen["cpu"]]
        for device in chosen.get("devices", []):
            args += ["-device", device]
        firmware = chosen.get("firmware")
        if firmware:
            found = which(firmware)
            if found:
                args += ["-bios", found]
    if disk:
        p = Path(disk).expanduser().resolve()
        if not p.is_file():
            raise FileNotFoundError("disk image not found")
        args += ["-drive", "file=" + str(p) + ",format=qcow2,if=virtio"]
    if cdrom:
        p = Path(cdrom).expanduser().resolve()
        if not p.is_file():
            raise FileNotFoundError("CD-ROM/ISO image not found")
        args += ["-cdrom", str(p)]
    if firmware_kernel:
        p = Path(firmware_kernel).expanduser().resolve()
        if not p.is_file():
            raise FileNotFoundError("kernel image not found")
        args += ["-kernel", str(p)]
    args += ["-no-reboot"]
    return args


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("list", "run"))
    parser.add_argument("--backend")
    parser.add_argument("--accel", default="auto", choices=sorted(ACCELERATORS))
    parser.add_argument("--memory", default="512M")
    parser.add_argument("--disk")
    parser.add_argument("--cdrom")
    parser.add_argument("--kernel")
    parser.add_argument("--profile")
    parser.add_argument("--vcpus", type=int, default=1)
    parser.add_argument("--gui", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    ns = parser.parse_args(argv)
    try:
        if ns.command == "list":
            print(json.dumps(probe(), indent=2))
            return 0
        if not ns.backend:
            parser.error("run requires --backend")
        args = build_command(ns.backend, ns.accel, ns.memory, ns.disk,
                             ns.cdrom, ns.kernel, not ns.gui, profile=ns.profile,
                             vcpus=ns.vcpus)
        if ns.dry_run:
            print(json.dumps({"command": args, "shell": False}, indent=2))
            return 0
        return subprocess.run(args, check=False).returncode
    except (ValueError, OSError, RuntimeError, json.JSONDecodeError) as exc:
        print("chimera-hypervisor: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
