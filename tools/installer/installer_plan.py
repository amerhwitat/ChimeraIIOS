#!/usr/bin/env python3
"""Safe, cross-platform installer planner for Chimera II OS.

This layer inventories and plans. Platform adapters may execute privileged
operations only after explicit confirmation. The default plan is dry-run and
non-destructive.
"""
from __future__ import annotations

import json
import platform as py_platform
import shutil
from pathlib import Path
from typing import Any


def load_capability_catalog(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def detect_platform() -> str:
    name = py_platform.system().lower()
    if name.startswith("windows"):
        return "windows"
    if name == "darwin":
        return "darwin"
    return "linux"


def _commands_for(target: str) -> list[str]:
    common = ["python3"]
    if target == "linux":
        common += ["lsblk", "blkid", "lspci", "lsusb", "ip", "mount"]
    elif target == "windows":
        common += ["powershell", "pnputil", "diskpart"]
    return [x for x in common if shutil.which(x) or x == "python3"]


def build_plan(target: str | None = None, profile: str = "interactive", *, dry_run: bool = True) -> dict[str, Any]:
    target = target or detect_platform()
    if target not in {"linux", "windows", "darwin"}:
        raise ValueError(f"unsupported target: {target}")
    if profile not in {"interactive", "workstation", "server", "developer", "minimal"}:
        raise ValueError(f"unsupported profile: {profile}")

    steps = [
        "firmware_boot_check",
        "hardware_inventory",
        "driver_plan",
        "network_plan",
        "storage_plan",
        "filesystem_plan",
        "chimera_directory_layout",
        "base_install",
        "bootloader_install",
        "aurora_wayland_optional",
        "service_profile",
        "post_install_validation",
    ]
    if profile in {"server", "developer"}:
        steps += ["network_services", "storage_services"]
    if profile == "minimal":
        steps = [x for x in steps if x not in {"aurora_wayland_optional", "network_services", "storage_services"}]

    driver_sources = ["linux_driver_database", "firmware"] if target != "windows" else ["windows_driver_catalog"]
    return {
        "schema": "chimera-ii-installer-plan",
        "version": 1,
        "platform": target,
        "profile": profile,
        "dry_run": dry_run,
        "destructive_storage": False,
        "commands_detected": _commands_for(target),
        "driver_sources": driver_sources,
        "steps": steps,
        "storage_policy": {
            "partition_table": "GPT",
            "legacy_mbr_read_compatibility": True,
            "default_filesystem": "ext4",
            "alternatives": ["xfs", "btrfs", "zfs-optional"],
            "raid": ["mdraid", "lvm", "hardware-raid-hba", "storage-spaces-interop"],
            "destructive_actions": "disabled until explicit confirmation",
        },
        "desktop_policy": {
            "name": "Aurora",
            "display": "Wayland-first",
            "renderer_fallback": ["Vulkan", "OpenGL", "software"],
            "media": "PipeWire-optional",
        },
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Plan a safe Chimera II installation")
    parser.add_argument("--target", choices=["linux", "windows", "darwin"], default=None)
    parser.add_argument("--profile", choices=["interactive", "workstation", "server", "developer", "minimal"], default="interactive")
    parser.add_argument("--execute", action="store_true", help="request execution mode; adapters still require confirmation")
    parser.add_argument("--catalog", type=Path, default=Path(__file__).with_name("installer_capabilities.json"))
    args = parser.parse_args()
    load_capability_catalog(args.catalog)
    plan = build_plan(args.target, args.profile, dry_run=not args.execute)
    print(json.dumps(plan, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
