#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inspect_file(path: str | Path) -> dict:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(p)
    data = p.read_bytes()[:4096]
    fmt = "raw"
    if data.startswith(b"\x7fELF"): fmt = "elf"
    elif data.startswith(b"MZ"): fmt = "pe"
    elif data.startswith(b"\x89PNG\r\n\x1a\n"): fmt = "raw"
    elif data[:6] in (b"CD001\x01", b"\x00\x00\x01\x00\x00\x00"): fmt = "iso"
    elif data[:4] in (b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf", b"\xcf\xfa\xed\xfe", b"\xca\xfe\xba\xbe"): fmt = "macho"
    return {"path": str(p), "format": fmt, "size": p.stat().st_size, "sha256": sha256(p)}


def create_manifest(path: str | Path, architecture: str) -> dict:
    info = inspect_file(path)
    return {"schema": "CHIMERA-IMAGE-1", "architecture": architecture, **info, "bootable": info["format"] in {"raw", "iso", "elf", "pe", "macho"}}


def validate_manifest(manifest: dict) -> bool:
    required = {"schema", "architecture", "path", "format", "size", "sha256"}
    if manifest.get("schema") != "CHIMERA-IMAGE-1" or not required.issubset(manifest):
        return False
    p = Path(manifest["path"])
    return p.is_file() and p.stat().st_size == manifest["size"] and sha256(p) == manifest["sha256"]


def main() -> int:
    ap = argparse.ArgumentParser(prog="chimera-image")
    sub = ap.add_subparsers(dest="command", required=True)
    i = sub.add_parser("inspect"); i.add_argument("path")
    m = sub.add_parser("manifest"); m.add_argument("path"); m.add_argument("architecture"); m.add_argument("--output")
    v = sub.add_parser("validate"); v.add_argument("manifest")
    args = ap.parse_args()
    if args.command == "inspect":
        print(json.dumps(inspect_file(args.path), indent=2))
    elif args.command == "manifest":
        data = create_manifest(args.path, args.architecture)
        text = json.dumps(data, indent=2) + "\n"
        if args.output: Path(args.output).write_text(text, encoding="utf-8")
        else: print(text, end="")
    else:
        data = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        return 0 if validate_manifest(data) else 1
    return 0

if __name__ == "__main__": raise SystemExit(main())
