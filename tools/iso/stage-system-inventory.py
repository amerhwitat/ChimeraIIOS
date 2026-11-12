#!/usr/bin/env python3
"""Stage generated applications and system composition metadata into the ISO.

Only files actually present in build output directories are called generated
artifacts. Registries and source trees are labelled separately so the ISO
inventory never implies that a declared app/service/target is executable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

SOURCE_MAP = {
    "applications/catalog.json": "usr/share/chimera/catalogues/applications/catalog.json",
    "desktop/desktop_profiles.json": "usr/share/chimera/catalogues/desktop/desktop_profiles.json",
    "desktop/profiles/desktop-profiles.json": "usr/share/chimera/catalogues/desktop/desktop-profiles.json",
    "desktop/aurora/desktop-environment.json": "usr/share/chimera/catalogues/desktop/desktop-environment.json",
    "desktop/aurora/aurora_app_registry.json": "usr/share/chimera/catalogues/desktop/aurora_app_registry.json",
    "desktop/aurora/aurora_desktop_capabilities.json": "usr/share/chimera/catalogues/desktop/aurora_desktop_capabilities.json",
    "services/service_schema.json": "usr/share/chimera/catalogues/services/service_schema.json",
    "services/service_registry.json": "usr/share/chimera/catalogues/services/service_registry.json",
    "services/linux/service-catalog.json": "usr/share/chimera/catalogues/services/service-catalog.json",
    "boot/boot-menu-contract.json": "usr/share/chimera/catalogues/boot/boot-menu-contract.json",
    "boot/iso/iso-layout.json": "usr/share/chimera/catalogues/boot/iso-layout.json",
}
TREE_MAP = {
    "desktop": "usr/share/chimera/desktops/source",
    "desktop/aurora": "usr/share/chimera/desktops/aurora",
    "desktop/aurora-shell": "usr/share/chimera/desktops/aurora-shell",
    "desktop/x11": "usr/share/chimera/desktops/x11",
    "services": "usr/share/chimera/services",
    "applications": "usr/share/chimera/applications",
    "apps": "usr/share/chimera/apps",
    "boot/jasper": "usr/share/chimera/boot/jasper",
    "boot/installation": "usr/share/chimera/boot/installation",
    "boot/recovery": "usr/share/chimera/boot/recovery",
}
GENERATED_MAP = {
    "build/desktop": "opt/chimera/generated/desktop",
    "build/apps": "opt/chimera/generated/apps",
    "build/services": "opt/chimera/generated/services",
    "build/targets": "opt/chimera/generated/targets",
    "build/koronos/x86_64": "opt/chimera/generated/targets/x86_64",
    "build/koronos/ports": "opt/chimera/generated/architecture-ports",
    "build/mobile": "opt/chimera/generated/mobile",
    "build/compatibility": "opt/chimera/generated/compatibility",
    "build/toolchains": "opt/chimera/generated/toolchains",
    "build/network-tools": "opt/chimera/generated/network-tools",
    "build/live-boot": "opt/chimera/generated/live-boot",
}
UNIT_DIRS = (
    ("systemd", "usr/lib/systemd/system"),
    ("init.d", "etc/init.d"),
    ("rc0.d", "etc/rc0.d"), ("rc1.d", "etc/rc1.d"),
    ("rc2.d", "etc/rc2.d"), ("rc3.d", "etc/rc3.d"),
    ("rc4.d", "etc/rc4.d"), ("rc5.d", "etc/rc5.d"),
    ("rc6.d", "etc/rc6.d"),
)

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def copy_file(src: Path, dst: Path, root: Path, kind: str, records: list[dict]) -> None:
    if not src.is_file() or src.is_symlink():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    records.append({"kind": kind, "source": src.relative_to(root).as_posix(),
                    "iso_path": "/" + dst.as_posix(), "bytes": dst.stat().st_size,
                    "sha256": digest(dst)})

def copy_tree(src: Path, dst: Path, root: Path, kind: str, records: list[dict]) -> None:
    if not src.is_dir():
        return
    for current, dirs, files in os.walk(src, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in {".git", "__pycache__", "node_modules", ".cache"})
        current_path = Path(current)
        rel = current_path.relative_to(src)
        target_dir = dst / rel
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in sorted(files):
            source = current_path / name
            if source.is_symlink() or not source.is_file():
                continue
            copy_file(source, target_dir / name, root, kind, records)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--iso", required=True, type=Path)
    args = ap.parse_args()
    root, iso = args.root.resolve(), args.iso.resolve()
    records: list[dict] = []
    missing_generated = []
    for rel, target in SOURCE_MAP.items():
        src = root / rel
        if src.is_file():
            copy_file(src, iso / target, root, "registry-or-contract", records)
    for rel, target in TREE_MAP.items():
        copy_tree(root / rel, iso / target, root, "source-runtime-or-desktop-assets", records)
    for rel, target in GENERATED_MAP.items():
        src = root / rel
        if src.is_dir():
            copy_tree(src, iso / target, root, "generated-build-output", records)
        else:
            missing_generated.append(rel)
    # Carry target ELF handoff manifests and binaries if they were built.
    target_dir = root / "build/koronos/x86_64"
    for target in ("live", "installer", "recovery"):
        for suffix in ("elf", "manifest.json"):
            src = target_dir / f"target-init-{target}.{suffix}"
            if src.is_file():
                copy_file(src, iso / f"boot/targets/{src.name}", root, "target-init-payload-or-manifest", records)
    # Collect declared unit/target files from repository trees into a discoverable
    # directory; only actual unit files are copied here (not arbitrary source).
    unit_suffixes = {".service", ".target", ".timer", ".socket", ".path", ".mount", ".automount"}
    for service_root in (root / "services", root / "boot", root / "system"):
        if not service_root.is_dir():
            continue
        for src in service_root.rglob("*"):
            if src.is_file() and not src.is_symlink() and src.suffix in unit_suffixes:
                copy_file(src, iso / "usr/lib/systemd/system" / src.name,
                          root, "service-unit-definition", records)
    # Expose explicit target/runlevel registries when present.
    for rel, target in (
        ("system/targets", "usr/share/chimera/targets"),
        ("system/runlevels", "usr/share/chimera/runlevels"),
        ("config/targets", "usr/share/chimera/targets/config"),
        ("config/runlevels", "usr/share/chimera/runlevels/config"),
        ("services/targets", "usr/share/chimera/targets/services"),
    ):
        copy_tree(root / rel, iso / target, root, "target-or-runlevel-definition", records)
    # Stage service-manager definitions and SysV runlevel links from generated
    # rootfs as well as repository source, preserving the level directories.
    rootfs = root / "build/rootfs"
    for rel, target in UNIT_DIRS:
        src = rootfs / ("etc/" + rel if rel not in ("services", "systemd") else
                        ("etc/systemd/system" if rel == "systemd" else "usr/lib/systemd/system"))
        if rel == "services":
            src = root / "services"
            copy_tree(src, iso / target, root, "service-source", records)
        else:
            copy_tree(src, iso / target, root, "generated-service-or-runlevel", records)
    records.sort(key=lambda item: (item["kind"], item["iso_path"]))
    inventory = {
        "schema": "CHM-ISO-COMPONENT-INVENTORY-1",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "semantics": {
            "registry": "catalogue/contract only; not proof of installed or runnable implementation",
            "generated-build-output": "copied from existing build output; each file is SHA-256 indexed",
            "target-init-payload-or-manifest": "payload readiness/production status is defined by its manifest",
        },
        "generated_directories_missing": missing_generated,
        "files": len(records),
        "bytes": sum(item["bytes"] for item in records),
        "kinds": {},
        "entries": records,
    }
    for item in records:
        inventory["kinds"][item["kind"]] = inventory["kinds"].get(item["kind"], 0) + 1
    out = iso / "boot/chimera/manifests/ISO-COMPONENT-INVENTORY.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    sums = iso / "boot/chimera/manifests/ISO-COMPONENT-SHA256SUMS"
    sums.write_text("".join(f'{item["sha256"]}  {item["iso_path"].lstrip("/") }\n' for item in records), encoding="utf-8")
    print(f"[ISO-INVENTORY] {len(records)} files, {inventory['bytes']} bytes, kinds={inventory['kinds']}")
    print(f"[ISO-INVENTORY] missing generated directories (not fabricated): {', '.join(missing_generated)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
