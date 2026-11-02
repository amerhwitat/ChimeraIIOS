#!/usr/bin/env python3
"""Explicit, package-manager-backed installer for optional Chimera language profiles.

The catalog describes capabilities; this helper installs only packages exposed by
the selected host package manager. It never downloads proprietary toolchains.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "toolchains" / "language-toolchain-catalog.json"


def package_manager():
    for name in ("apt-get", "dnf", "pacman"):
        if shutil.which(name):
            return name
    return None


def main():
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    profiles = data["install_profiles"]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", nargs="?", choices=sorted(profiles))
    parser.add_argument("--list", action="store_true", help="list supported optional profiles")
    parser.add_argument("--dry-run", action="store_true", help="print package plan without installing")
    parser.add_argument("--yes", action="store_true", help="confirm package installation")
    args = parser.parse_args()
    if args.list:
        for key, profile in profiles.items():
            print(f"{key}: {profile['description']}")
        return 0
    if not args.profile:
        parser.error("select a profile or use --list")
    manager = package_manager()
    if not manager:
        print("No supported package manager found (apt-get, dnf, pacman).", file=sys.stderr)
        return 2
    packages = profiles[args.profile]["packages"].get(
        "apt" if manager == "apt-get" else manager, []
    )
    if not packages:
        print(f"No package mapping for {args.profile} on {manager}.", file=sys.stderr)
        return 2
    print(f"Package manager: {manager}")
    print("Profile:", args.profile)
    print("Packages:", " ".join(packages))
    if args.dry_run:
        return 0
    if not args.yes:
        print("Refusing to install without explicit --yes confirmation.", file=sys.stderr)
        return 3
    if manager == "apt-get":
        cmd = ["apt-get", "install", "-y", "--no-install-recommends", *packages]
    elif manager == "dnf":
        cmd = ["dnf", "install", "-y", *packages]
    else:
        cmd = ["pacman", "-S", "--needed", "--noconfirm", *packages]
    if hasattr(__import__("os"), "geteuid") and __import__("os").geteuid() != 0:
        cmd = ["sudo", *cmd]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
