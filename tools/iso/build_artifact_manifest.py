#!/usr/bin/env python3
"""Create a deterministic, hash-bound inventory of every staged ISO artifact."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from pathlib import Path

SCHEMA = "CHIMERA-ISO-ARTIFACTS-1"
DEFAULT_REQUIRED = (
    "boot/grub/grub.cfg",
    "boot/koronos/koronos.elf",
    "boot/live/chimera-live-initramfs.img",
    "boot/recovery/chimera-recovery-initramfs.img",
    "install/installer/installation.img",
    "EFI/BOOT/BOOTX64.EFI",
)

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def classify(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in {".img", ".initrd", ".initramfs"}:
        return "ram-disk-image"
    if suffix in {".iso", ".iso.zst"}:
        return "optical-image"
    if suffix in {".elf", ".efi"}:
        return "executable-image"
    if suffix in {".bin", ".o", ".obj"}:
        return "boot-binary"
    if suffix in {".squashfs", ".sqfs"}:
        return "root-filesystem-image"
    if suffix in {".mp4", ".png", ".jpg", ".jpeg", ".svg", ".webp"}:
        return "visual-media"
    if suffix in {".json", ".toml", ".yaml", ".yml"}:
        return "metadata"
    return "file"

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="ISO staging tree")
    parser.add_argument("--manifest", required=True, type=Path, help="JSON inventory output")
    parser.add_argument("--checksums", type=Path, help="Optional sha256sum-compatible output")
    parser.add_argument("--require", action="append", default=[], help="Required relative path (repeatable)")
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        parser.error(f"ISO root is not a directory: {root}")
    manifest_path = args.manifest.resolve()
    checksum_path = args.checksums.resolve() if args.checksums else None
    excluded = {manifest_path, checksum_path}
    required = tuple(dict.fromkeys((*DEFAULT_REQUIRED, *args.require)))
    missing = [name for name in required if not (root / name).is_file() or (root / name).is_symlink()]
    if missing:
        print("ERROR: required ISO artifacts missing: " + ", ".join(missing), file=sys.stderr)
        return 2

    records = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        if not path.is_file() and not path.is_symlink():
            continue
        if path.resolve(strict=False) in excluded:
            continue
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            target = os.readlink(path)
            payload = target.encode("utf-8", errors="surrogateescape")
            digest = hashlib.sha256(payload).hexdigest()
            records.append({
                "path": rel, "kind": "symlink", "bytes": len(payload),
                "sha256": digest, "target": target,
            })
        else:
            info = path.stat()
            records.append({
                "path": rel, "kind": classify(rel), "bytes": info.st_size,
                "sha256": sha256_file(path), "mode": stat.S_IMODE(info.st_mode),
            })

    if not records:
        print("ERROR: ISO staging tree contains no files", file=sys.stderr)
        return 2

    kinds = {}
    for item in records:
        kinds[item["kind"]] = kinds.get(item["kind"], 0) + 1
    document = {
        "schema": SCHEMA,
        "root": ".",
        "required_artifacts": list(required),
        "artifact_count": len(records),
        "kind_counts": dict(sorted(kinds.items())),
        "artifacts": records,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if checksum_path:
        checksum_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [f'{item["sha256"]}  {item["path"]}' for item in records if item["kind"] != "symlink"]
        checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[ISO ARTIFACTS] inventoried={len(records)} kinds={json.dumps(dict(sorted(kinds.items())), sort_keys=True)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
