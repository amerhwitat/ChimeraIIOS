#!/usr/bin/env python3
"""Create a byte-preserving offline artwork, executable-command, ELF and EFI bundle.

Only files discovered in repository artwork roots and explicit build/command roots
are included. Each copied file is hashed; conflicting command names fail closed.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
import shutil
import stat
import struct
import sys
from pathlib import Path

ART_EXTS = {".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".mp4", ".avif"}
def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def is_elf(data: bytes) -> bool:
    return data.startswith(b"\x7fELF")

def is_pe(data: bytes) -> bool:
    if len(data) < 0x40 or data[:2] != b"MZ":
        return False
    off = struct.unpack_from("<I", data, 0x3C)[0]
    return off + 4 <= len(data) and data[off:off+4] == b"PE\0\0"

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path.cwd())
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--binary-root", action="append", type=Path, default=[])
    ap.add_argument("--command-root", action="append", type=Path, default=[])
    ap.add_argument("--require-efi", action="store_true")
    ap.add_argument("--require-elf", action="store_true")
    ap.add_argument("--require-commands", action="store_true")
    args = ap.parse_args()
    root, out = args.root.resolve(), args.output.resolve()
    art_roots = [
        root / "Library", root / "library",
        root / "desktop/aurora/assets", root / "desktop/marine/assets",
        root / "boot/splash", root / "boot/visual",
        root / "vendor/chimera-ii-os/source/Library",
        root / "vendor/chimera-ii-os/source/library",
        root / "vendor/chimera-ii-os/source/desktop/aurora/assets",
        root / "vendor/chimera-ii-os/source/desktop/marine/assets",
        root / "vendor/chimera-ii-os/source/boot/splash",
        root / "vendor/chimera-ii-os/source/boot/visual",
    ]
    artwork, seen_art = [], set()
    for base in art_roots:
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in ART_EXTS:
                continue
            if out == path or out in path.parents:
                continue
            rel = path.relative_to(root).as_posix()
            if rel in seen_art:
                continue
            raw = path.read_bytes()
            if not raw:
                raise ValueError(f"empty artwork asset: {rel}")
            original = out / "artwork" / rel
            original.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, original)
            artwork.append({"path": rel, "packaged_path": original.relative_to(out).as_posix(),
                            "media_type": path.suffix.lower(), "size_bytes": len(raw),
                            "sha256": sha256(raw), "base64": base64.b64encode(raw).decode("ascii")})
            seen_art.add(rel)
    if not artwork:
        raise ValueError("no artwork assets found; refusing to emit an empty offline bundle")

    binary_roots = [p.resolve() for p in args.binary_root]
    for candidate in (root / "build", root / "vendor/chimera-ii-os/source/build"):
        if candidate.is_dir() and candidate.resolve() not in binary_roots:
            binary_roots.append(candidate.resolve())
    found = {}
    for base in binary_roots:
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or out == path or out in path.parents:
                continue
            if any(part in {"offline-assets", "os-asset-bundle"} for part in path.parts):
                continue
            try:
                raw = path.read_bytes()
            except OSError:
                continue
            if is_elf(raw):
                fmt = "ELF"
            elif is_pe(raw):
                fmt = "PE/COFF"
            else:
                continue
            digest = sha256(raw)
            if digest in found:
                continue
            dest = out / "binaries" / digest[:12] / path.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)
            found[digest] = {"source": str(path.relative_to(root)) if root in path.parents else str(path),
                             "path": dest.relative_to(out).as_posix(), "format": fmt,
                             "size_bytes": len(raw), "sha256": digest}

    # Collect executable command files from root and staging trees. /usr/bin maps
    # to /bin and /usr/sbin maps to /sbin for the requested root-level command layout.
    command_roots = [p.resolve() for p in args.command_root]
    for candidate in (root, root / "rootfs", root / "vendor/chimera-ii-os/source/rootfs"):
        if candidate.is_dir() and candidate.resolve() not in command_roots:
            command_roots.append(candidate.resolve())
    commands = {}
    for base in command_roots:
        if not base.is_dir():
            continue
        for subdir, destdir in (("bin", "bin"), ("sbin", "sbin"),
                                ("usr/bin", "bin"), ("usr/sbin", "sbin"),
                                ("compat/bin", "bin"), ("compat/sbin", "sbin"),
                                ("tools/commands", "bin"), ("tools/kali", "sbin"),
                                ("userland/bin", "bin"), ("userland/sbin", "sbin"),
                                ("userspace/bin", "bin"), ("userspace/sbin", "sbin")):
            srcdir = base / subdir
            if not srcdir.is_dir():
                continue
            for path in sorted(srcdir.iterdir()):
                if not path.is_file():
                    continue
                if path.name.startswith(".") or path.suffix.lower() in {".json", ".md", ".txt", ".csv", ".yaml", ".yml"}:
                    continue
                if subdir == "tools/commands" and (path.name.startswith("test") or path.name in {
                    "crawl_ss64.py", "dos-payload-builder.py", "generate_runtime_manifest.py",
                    "import_command_candidates.py",
                }):
                    continue
                if subdir == "tools/kali" and not path.name.startswith("chimera-kali"):
                    continue
                try:
                    mode = path.stat().st_mode
                    raw = path.read_bytes()
                except OSError:
                    continue
                target = f"{destdir}/{path.name}"
                digest = sha256(raw)
                prior = commands.get(target)
                if prior and prior["sha256"] != digest:
                    raise ValueError(f"conflicting command implementations for /{target}: {prior['source']} and {path}")
                if prior:
                    continue
                dest = out / "commands" / target
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, dest)
                dest.chmod((mode & 0o777) | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                commands[target] = {
                    "source": str(path.relative_to(root)) if root in path.parents else str(path),
                    "path": dest.relative_to(out).as_posix(), "install_path": "/" + target,
                    "size_bytes": len(raw), "sha256": digest, "mode": oct((mode & 0o777) | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH),
                    "format": "ELF" if is_elf(raw) else ("PE/COFF" if is_pe(raw) else "script-or-other-executable"),
                }

    elfs = [x for x in found.values() if x["format"] == "ELF"]
    efis = [x for x in found.values() if x["format"] == "PE/COFF"]
    if args.require_elf and not elfs:
        raise ValueError("no valid build-produced ELF binaries found")
    if args.require_efi and not efis:
        raise ValueError("no valid PE/COFF EFI binaries found")
    if args.require_commands and not commands:
        raise ValueError("no executable command files found in /bin, /sbin, /usr/bin or /usr/sbin roots")
    out.mkdir(parents=True, exist_ok=True)
    (out / "embedded-artwork.json").write_text(
        json.dumps({"schema":"OS-OFFLINE-ARTWORK-BASE64-2","assets":artwork},
                   ensure_ascii=False, separators=(",",":")) + "\n", encoding="utf-8")
    manifest = {"schema":"OS-BUILD-BINARY-BUNDLE-2","elf_count":len(elfs),
                "efi_count":len(efis),"artwork_count":len(artwork),
                "command_count":len(commands),
                "binaries":sorted(found.values(), key=lambda x:x["path"]),
                "commands":sorted(commands.values(), key=lambda x:x["install_path"])}
    (out / "binary-manifest.json").write_text(json.dumps(manifest, indent=2)+"\\n", encoding="utf-8")
    print(f"ASSET BUNDLE PASS: artwork={len(artwork)} ELF={len(elfs)} EFI={len(efis)} commands={len(commands)}")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"ASSET BUNDLE FAIL: {exc}", file=sys.stderr)
        raise SystemExit(2)
