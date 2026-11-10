#!/usr/bin/env python3
"""Build redistributable Amiga ADF and Commodore 64 D64 media.

The Amiga boot floppy is an official AROS m68k nightly image. No proprietary
Kickstart ROM or copyrighted AmigaOS binary is fetched or redistributed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import tempfile
import urllib.request
import zipfile

ADF_SIZE = 880 * 1024
D64_SIZE = 174848


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_c64_basic_prg(path: pathlib.Path) -> None:
    # Tokenized Commodore BASIC V2 program at $0801. It is intentionally
    # self-contained and uses only ROM BASIC, so it runs on a stock C64.
    lines = [
        (10, [0x99] + list(b'"CHIMERA II OS - COMMODORE 64"')),
        (20, [0x99] + list(b'"BASIC COMPATIBILITY MEDIA"')),
        (30, [0x99] + list(b'"AMIGA ADF + C64 D64 MEDIA BUILDER"')),
        (40, [0x80]),
    ]
    body = bytearray()
    address = 0x0801
    for number, tokens in lines:
        record = bytearray(b"\\x00\\x00")
        record += number.to_bytes(2, "little")
        record += bytes(tokens) + b"\\x00"
        next_address = address + len(record)
        record[0:2] = next_address.to_bytes(2, "little")
        body += record
        address = next_address
    body += b"\\x00\\x00"
    path.write_bytes((0x0801).to_bytes(2, "little") + body)


def download_aros_adf(date: str, out: pathlib.Path) -> dict:
    archive_name = f"AROS-{date}-amiga-m68k-boot-floppy.zip"
    url = f"https://sourceforge.net/projects/aros/files/nightly2/{date}/Binaries/{archive_name}/download"
    request = urllib.request.Request(url, headers={"User-Agent": "ChimeraOS-media-builder/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        archive_bytes = response.read()
    with tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
        tmp.write(archive_bytes)
        tmp.flush()
        with zipfile.ZipFile(tmp.name) as archive:
            candidates = []
            for info in archive.infolist():
                if info.is_dir():
                    continue
                name = pathlib.PurePosixPath(info.filename).name.lower()
                if name.endswith((".adf", ".img", ".bin")) and info.file_size == ADF_SIZE:
                    candidates.append(info)
            if not candidates:
                raise RuntimeError(
                    f"AROS archive {archive_name} contains no 901120-byte floppy image"
                )
            candidate = candidates[0]
            payload = archive.read(candidate)
    if payload[:3] != b"DOS":
        raise RuntimeError("Downloaded AROS floppy lacks the AmigaDOS/AROS DOS boot signature")
    adf = out / "AROS-Amiga-500-2000-m68k-boot.adf"
    adf.write_bytes(payload)
    return {"source": url, "archive_member": candidate.filename, "size": len(payload), "sha256": sha256(adf)}


def build_d64(out: pathlib.Path) -> dict:
    if not shutil_which("c1541"):
        raise RuntimeError("VICE c1541 is required; install the 'vice' package")
    prg = out / "CHIMERA64.PRG"
    d64 = out / "CHIMERA-Commodore-64.d64"
    build_c64_basic_prg(prg)
    command = [
        "c1541", "-format", "CHIMERA,01", str(d64),
        "-write", str(prg), "CHIMERA", "-list",
    ]
    result = subprocess.run(command, check=True, text=True, capture_output=True)
    if d64.stat().st_size != D64_SIZE:
        raise RuntimeError(f"Unexpected D64 size: {d64.stat().st_size}")
    if "CHIMERA" not in (result.stdout + result.stderr).upper():
        raise RuntimeError("c1541 did not list the CHIMERA program on the generated disk")
    return {"size": d64.stat().st_size, "sha256": sha256(d64), "c1541_listing": (result.stdout + result.stderr).strip()}


def shutil_which(command: str) -> str | None:
    import shutil
    return shutil.which(command)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aros-date", default=os.environ.get("AROS_NIGHTLY_DATE", "20261109"))
    parser.add_argument("--out", default="build/retro-media")
    args = parser.parse_args()
    if not (len(args.aros_date) == 8 and args.aros_date.isdigit()):
        parser.error("--aros-date must be YYYYMMDD")
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    amiga = download_aros_adf(args.aros_date, out)
    commodore = build_d64(out)
    manifest = {
        "schema": "CHIMERA-RETRO-MEDIA-1",
        "amiga": {
            "machine_family": ["Amiga 500", "Amiga 2000"],
            "cpu": "Motorola 68000",
            "format": "ADF",
            "boot_media": "AROS m68k official boot floppy",
            **amiga,
        },
        "commodore": {
            "machine_family": ["Commodore 64"],
            "format": "D64 (1541 floppy format; not ADF)",
            "program": "CHIMERA64.PRG",
            "builder": "VICE c1541",
            **commodore,
        },
        "policy": "No proprietary Kickstart, AmigaOS ROM, Commodore ROM, or commercial application is bundled.",
    }
    (out / "media-manifest.json").write_text(json.dumps(manifest, indent=2) + "\\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
