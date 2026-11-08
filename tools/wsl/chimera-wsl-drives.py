#!/usr/bin/env python3
"""Configure WSL2 Windows-drive automounts under /mnt/drive.

This is a WSL distribution integration, not a Koronos block-device driver.
WSL2 performs the actual DrvFs mounts when the distribution starts.
"""
from __future__ import annotations

import argparse
import configparser
import os
import platform
import sys
from pathlib import Path


def is_wsl() -> bool:
    release = platform.release().lower()
    return "microsoft" in release or bool(os.environ.get("WSL_INTEROP"))


def configure(config_path: Path, mount_root: Path) -> None:
    if not is_wsl():
        raise RuntimeError("Windows drive automount requires a WSL2 environment")
    if os.geteuid() != 0:
        raise PermissionError("run 'chimera-wsl-drives configure' as root")

    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.optionxform = str
    if config_path.exists():
        with config_path.open(encoding="utf-8") as stream:
            config.read_file(stream)

    if not config.has_section("automount"):
        config.add_section("automount")
    config.set("automount", "enabled", "true")
    config.set("automount", "root", str(mount_root))
    config.set("automount", "options", "metadata,umask=22,fmask=11")

    config_path.parent.mkdir(parents=True, exist_ok=True)
    backup = config_path.with_name(config_path.name + ".chimera-backup")
    if config_path.exists() and not backup.exists():
        backup.write_bytes(config_path.read_bytes())
        backup.chmod(0o600)

    temporary = config_path.with_name(config_path.name + ".chimera-new")
    with temporary.open("w", encoding="utf-8") as stream:
        config.write(stream)
    temporary.chmod(0o644)
    os.replace(temporary, config_path)
    mount_root.mkdir(parents=True, exist_ok=True)
    print(f"Configured WSL2 DrvFs automount root: {mount_root}")
    print("Restart the distribution (from Windows: wsl --shutdown) to apply it.")
    print("Windows fixed drives will appear as /mnt/drive/c, /mnt/drive/d, etc.")


def status(mount_root: Path) -> int:
    if not is_wsl():
        print("Not running under WSL; Windows DrvFs mounts are unavailable.")
        return 2
    print(f"WSL detected. Windows-drive root: {mount_root}")
    if not mount_root.is_dir():
        print("Drive root does not exist yet; run configure as root and restart WSL.")
        return 1
    drives = sorted(p for p in mount_root.iterdir() if p.is_dir())
    if not drives:
        print("No automounted drives found.")
        return 1
    for drive in drives:
        print(f"{drive} -> {drive}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("configure", "status"))
    parser.add_argument("--config", type=Path, default=Path("/etc/wsl.conf"))
    parser.add_argument("--mount-root", type=Path, default=Path("/mnt/drive"))
    args = parser.parse_args(argv)
    try:
        if args.action == "configure":
            configure(args.config, args.mount_root)
            return 0
        return status(args.mount_root)
    except (OSError, RuntimeError, PermissionError) as exc:
        print(f"chimera-wsl-drives: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
