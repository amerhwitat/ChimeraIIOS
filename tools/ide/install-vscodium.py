#!/usr/bin/env python3
"""Install VSCodium through the current OS's official package manager.

Default operation is a dry-run. Pass --install to invoke the selected manager.
This helper does not download, unpack, or execute arbitrary release archives.
"""
from __future__ import annotations
import argparse
import platform
import shutil
import subprocess
import sys

def install_plan(system: str, which=shutil.which) -> list[str]:
    name = system.lower()
    if name == "linux":
        if not which("flatpak"):
            raise RuntimeError("Flatpak is not installed. Install Flatpak using your distribution's official package manager first.")
        return ["flatpak", "install", "--user", "--noninteractive", "flathub", "com.vscodium.codium"]
    if name == "windows":
        if not which("winget"):
            raise RuntimeError("winget is unavailable. Install App Installer from Microsoft Store first.")
        return ["winget", "install", "--id", "VSCodium.VSCodium", "--exact", "--source", "winget",
                "--accept-source-agreements", "--accept-package-agreements"]
    if name == "darwin":
        if not which("brew"):
            raise RuntimeError("Homebrew is unavailable. Install Homebrew from brew.sh first.")
        return ["brew", "install", "--cask", "vscodium"]
    raise RuntimeError(f"unsupported host OS: {system}")

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true", help="run the official package-manager install command")
    args = parser.parse_args()
    try:
        command = install_plan(platform.system())
    except RuntimeError as exc:
        print(f"vscodium: {exc}", file=sys.stderr)
        return 2
    print("Install plan:", " ".join(command))
    if not args.install:
        print("Dry run only. Review the command, then pass --install to proceed.")
        return 0
    completed = subprocess.run(command, check=False)
    if completed.returncode:
        print(f"vscodium: package manager exited with {completed.returncode}", file=sys.stderr)
        return completed.returncode
    print("VSCodium installation command completed. Verify the installed package and signature with the package manager.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
