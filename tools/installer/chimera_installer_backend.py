#!/usr/bin/env python3
"""Local, allowlisted installer adapter for Chimera II.

Run this component only on a machine/session where the operator is authorized
and understands the package-manager changes it may perform. The browser UI
must never execute this module directly.
"""
import platform
import shutil
import subprocess
from typing import Dict, List

APP_MAP: Dict[str, Dict[str, List[str]]] = {
    "git": {
        "linux": ["git"],
        "windows": ["Git.Git"],
    },
    "firefox": {
        "linux": ["firefox"],
        "windows": ["Mozilla.Firefox"],
    },
    "vscode": {
        "linux": ["code"],
        "windows": ["Microsoft.VisualStudioCode"],
    },
    "vlc": {
        "linux": ["vlc"],
        "windows": ["VideoLAN.VLC"],
    },
    "python3": {
        "linux": ["python3"],
        "windows": ["Python.Python.3.13"],
    },
}

LINUX_MANAGERS = [
    ("apt", ["apt-get", "install", "-y"]),
    ("dnf", ["dnf", "install", "-y"]),
    ("pacman", ["pacman", "-S", "--noconfirm"]),
    ("zypper", ["zypper", "--non-interactive", "install"]),
    ("apk", ["apk", "add"]),
]


def _platform_name() -> str:
    return "windows" if platform.system().lower().startswith("win") else "linux"


def _linux_manager():
    for name, command in LINUX_MANAGERS:
        if shutil.which(command[0]):
            return name, command
    if shutil.which("flatpak"):
        return "flatpak", ["flatpak", "install", "-y"]
    return None, None


def plan(app_id: str, target_platform: str = None):
    target = (target_platform or _platform_name()).lower()
    if app_id not in APP_MAP:
        raise ValueError("unsupported application id")
    if target not in APP_MAP[app_id]:
        raise ValueError("unsupported target platform")
    if target == "windows":
        if not shutil.which("winget"):
            raise RuntimeError("backend-unavailable: winget")
        return "winget", ["winget", "install", "--exact", "--accept-package-agreements", "--accept-source-agreements", APP_MAP[app_id][target][0]]
    name, prefix = _linux_manager()
    if not prefix:
        raise RuntimeError("backend-unavailable: linux package manager")
    return name, prefix + APP_MAP[app_id][target]


def execute(app_id: str, target_platform: str = None, dry_run: bool = True):
    backend, command = plan(app_id, target_platform)
    result = {"ok": False, "backend": backend, "operation": "dry-run" if dry_run else "install", "command": command}
    if dry_run:
        result["ok"] = True
        return result
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    result["ok"] = completed.returncode == 0
    result["returncode"] = completed.returncode
    result["stdout"] = completed.stdout[-4000:]
    result["stderr"] = completed.stderr[-4000:]
    return result


if __name__ == "__main__":
    import argparse, json
    parser = argparse.ArgumentParser(description="Chimera II allowlisted installer adapter")
    parser.add_argument("app_id", choices=sorted(APP_MAP))
    parser.add_argument("--platform", choices=["linux", "windows"])
    parser.add_argument("--apply", action="store_true", help="perform the package-manager operation")
    args = parser.parse_args()
    print(json.dumps(execute(args.app_id, args.platform, dry_run=not args.apply), indent=2))
