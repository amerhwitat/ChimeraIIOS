#!/usr/bin/env python3
"""Chimera II package-manager adapter.

The native package managers remain authoritative. This tool discovers the
host package manager, prints safe install plans, and optionally executes an
explicitly authorized command. It never downloads arbitrary scripts.
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "repositories.json"

MANAGERS = {
    "apt": {"cmd": "apt", "install": ["apt", "install"], "update": ["apt", "update"]},
    "apt-get": {"cmd": "apt-get", "install": ["apt-get", "install"], "update": ["apt-get", "update"]},
    "dpkg": {"cmd": "dpkg", "install": ["dpkg", "-i"]},
    "dnf": {"cmd": "dnf", "install": ["dnf", "install"], "update": ["dnf", "makecache"]},
    "yum": {"cmd": "yum", "install": ["yum", "install"], "update": ["yum", "makecache"]},
    "pacman": {"cmd": "pacman", "install": ["pacman", "-S"], "update": ["pacman", "-Sy"]},
    "zypper": {"cmd": "zypper", "install": ["zypper", "install"], "update": ["zypper", "refresh"]},
    "apk": {"cmd": "apk", "install": ["apk", "add"], "update": ["apk", "update"]},
    "xbps": {"cmd": "xbps-install", "install": ["xbps-install", "-S"], "update": ["xbps-install", "-S" ]},
    "portage": {"cmd": "emerge", "install": ["emerge"], "update": ["emerge", "--sync"]},
    "fnd": {"cmd": "fnd", "install": ["fnd", "install"]},
    "winget": {"cmd": "winget", "install": ["winget", "install"], "update": ["winget", "source", "update"]},
    "choco": {"cmd": "choco", "install": ["choco", "install"], "update": ["choco", "outdated"]},
    "scoop": {"cmd": "scoop", "install": ["scoop", "install"], "update": ["scoop", "update"]},
}


def load_sources():
    return json.loads(SOURCES.read_text(encoding="utf-8"))


def detect():
    return [name for name, spec in MANAGERS.items() if shutil.which(spec["cmd"])]


def plan(manager: str, package: str):
    if manager not in MANAGERS:
        raise SystemExit(f"unknown manager: {manager}")
    spec = MANAGERS[manager]
    return {"manager": manager, "command": spec["install"] + [package], "execute": False,
            "note": "Review and explicitly authorize this plan before execution."}


def main():
    p = argparse.ArgumentParser(prog="chimera-pkg")
    s = p.add_subparsers(dest="command", required=True)
    s.add_parser("detect")
    s.add_parser("sources")
    q = s.add_parser("plan"); q.add_argument("manager"); q.add_argument("package")
    q = s.add_parser("install"); q.add_argument("manager"); q.add_argument("package"); q.add_argument("--yes", action="store_true")
    q = s.add_parser("update"); q.add_argument("manager")
    a = p.parse_args()
    if a.command == "detect":
        print("\n".join(detect()))
    elif a.command == "sources":
        print(json.dumps(load_sources(), indent=2, ensure_ascii=False))
    elif a.command == "plan":
        print(json.dumps(plan(a.manager, a.package), indent=2))
    elif a.command == "install":
        pl = plan(a.manager, a.package)
        print(json.dumps(pl, indent=2))
        if not a.yes:
            print("Not executed. Re-run with --yes after reviewing the plan.")
            return 0
        subprocess.run(pl["command"], check=True)
    elif a.command == "update":
        spec = MANAGERS.get(a.manager)
        if not spec or "update" not in spec:
            raise SystemExit(f"manager does not define an update operation: {a.manager}")
        subprocess.run(spec["update"], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
