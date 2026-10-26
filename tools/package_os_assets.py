#!/usr/bin/env python3
"""Package offline artwork and genuine build-produced ELF/EFI binaries.

The generated bundle is a build artifact, not a substitute for source files.
Artwork is embedded as Base64 for offline consumers; executable binaries are
copied byte-for-byte with SHA-256 and format validation. Missing EFI payloads
fail closed when --require-efi is supplied.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import shutil
import struct
import sys
from pathlib import Path

ART_EXTS = {".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".mp4", ".avif"}
BIN_EXTS = {".elf", ".efi"}
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
    ap.add_argument("--require-efi", action="store_true")
    ap.add_argument("--require-elf", action="store_true")
    args = ap.parse_args()
    root = args.root.resolve()
    out = args.output.resolve()
    if out == root or root in out.parents:
        # Output under root is allowed, but never scan it as input.
        pass
    art_roots = [
        root / "desktop/aurora/assets", root / "desktop/marine/assets",
        root / "boot/splash", root / "boot/visual",
        root / "vendor/chimera-ii-os/source/desktop/aurora/assets",
        root / "vendor/chimera-ii-os/source/boot/splash",
        root / "vendor/chimera-ii-os/source/boot/visual",
    ]
    artwork = []
    seen_art = set()
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
            artwork.append({"path": rel, "media_type": path.suffix.lower(),
                            "size_bytes": len(raw), "sha256": sha256(raw),
                            "base64": base64.b64encode(raw).decode("ascii")})
            seen_art.add(rel)
    if not artwork:
        raise ValueError("no artwork assets found; refusing to emit an empty offline bundle")

    binary_roots = [p.resolve() for p in args.binary_root]
    defaults = [root / "build", root / "vendor/chimera-ii-os/source/build"]
    binary_roots.extend(p.resolve() for p in defaults if p.is_dir() and p.resolve() not in binary_roots)
    found = {}
    for base in binary_roots:
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in BIN_EXTS:
                continue
            if out == path or out in path.parents:
                continue
            raw = path.read_bytes()
            ext = path.suffix.lower()
            valid = is_elf(raw) if ext == ".elf" else is_pe(raw)
            if not valid:
                # Build trees sometimes contain test fixtures; never package a
                # mislabeled or non-executable file as a boot payload.
                continue
            key = sha256(raw)
            if key in found:
                continue
            name = path.name
            dest = out / "binaries" / key[:12] / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)
            found[key] = {"source": str(path.relative_to(root)) if root in path.parents else str(path),
                          "path": dest.relative_to(out).as_posix(),
                          "format": "ELF" if ext == ".elf" else "PE/COFF",
                          "size_bytes": len(raw), "sha256": key}
    elfs = [x for x in found.values() if x["format"] == "ELF"]
    efis = [x for x in found.values() if x["format"] == "PE/COFF"]
    if args.require_elf and not elfs:
        raise ValueError("no valid build-produced ELF binaries found")
    if args.require_efi and not efis:
        raise ValueError("no valid PE/COFF EFI binaries found")
    out.mkdir(parents=True, exist_ok=True)
    (out / "embedded-artwork.json").write_text(
        json.dumps({"schema":"OS-OFFLINE-ARTWORK-BASE64-1","assets":artwork},
                   ensure_ascii=False, separators=(",",":")) + "\n", encoding="utf-8")
    manifest = {"schema":"OS-BUILD-BINARY-BUNDLE-1","elf_count":len(elfs),
                "efi_count":len(efis),"artwork_count":len(artwork),
                "binaries":sorted(found.values(), key=lambda x:x["path"])}
    (out / "binary-manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    print(f"ASSET BUNDLE PASS: artwork={len(artwork)} embedded_base64_bytes="
          f"{(out/'embedded-artwork.json').stat().st_size} elf={len(elfs)} efi={len(efis)}")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"ASSET BUNDLE FAIL: {exc}", file=sys.stderr)
        raise SystemExit(2)
