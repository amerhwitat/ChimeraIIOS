#!/usr/bin/env python3
"""Generate a verifiable manifest for a freestanding Koronos target-init ELF.

These current target payloads prove a ring-3 syscall/readiness handshake only.
They are intentionally labelled probe-only until the real Live session,
installer disk writer, and recovery repair runtime exist.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

LIMITATIONS = {
    "live": [
        "ring-3 console/readiness probe only",
        "no production graphical session or native compositor",
    ],
    "installer": [
        "storage-plan dry run only",
        "no block-device writer or persistent installation backend",
    ],
    "recovery": [
        "diagnostics probe only",
        "no filesystem repair, boot repair, or account repair backend",
    ],
}


def readelf(*args: str) -> str:
    result = subprocess.run(
        ["readelf", *args], check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return result.stdout


def field(text: str, name: str) -> str:
    match = re.search(rf"^\\s*{re.escape(name)}:\\s*(.*?)\\s*$", text, re.M)
    if not match:
        raise SystemExit(f"ELF header is missing {name}")
    return match.group(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, choices=("live", "installer", "recovery"))
    parser.add_argument("--elf", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    elf = args.elf.resolve(strict=True)
    if not elf.is_file() or elf.stat().st_size == 0:
        raise SystemExit(f"target ELF is empty or not a file: {elf}")

    header = readelf("-h", str(elf))
    program_headers = readelf("-lW", str(elf))
    elf_class = field(header, "Class")
    elf_type = field(header, "Type").split()[0]
    machine = field(header, "Machine")
    entry = field(header, "Entry point address")
    loads = [
        line.strip() for line in program_headers.splitlines()
        if re.match(r"^\\s*LOAD\\s", line)
    ]

    if elf_class != "ELF64":
        raise SystemExit(f"expected ELF64, got {elf_class}")
    if elf_type != "EXEC":
        raise SystemExit(f"expected ET_EXEC, got {elf_type}")
    if machine != "Advanced Micro Devices X86-64":
        raise SystemExit(f"expected x86-64 ELF, got {machine}")
    if not any(re.search(r"\\bR\\s+E\\b", line) for line in loads):
        raise SystemExit("target ELF has no readable/executable PT_LOAD segment")

    digest = hashlib.sha256(elf.read_bytes()).hexdigest()
    manifest = {
        "schema": "CHM-NATIVE-TARGET-INIT-1",
        "target": args.target,
        "init_elf": f"/boot/targets/{elf.name}",
        "sha256": digest,
        "size_bytes": elf.stat().st_size,
        "elf": {
            "class": elf_class,
            "type": elf_type,
            "machine": machine,
            "entry_point": entry,
            "load_segments": loads,
        },
        "payload_kind": "ring3-readiness-probe",
        "production_ready": False,
        "limitations": LIMITATIONS[args.target],
    }

    output = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=output.name + ".", dir=output.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(manifest, stream, indent=2)
            stream.write("\n")
        os.replace(temporary, output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(f"[TARGET-MANIFEST] {args.target}: sha256={digest} production_ready=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
