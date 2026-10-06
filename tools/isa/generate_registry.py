#!/usr/bin/env python3
import base64
import binascii
import gzip
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
src = ROOT / "data/isa/isa-registry.json.gz.b64"
out = ROOT / "kernel/generated/chimera_isa_registry.generated.h"


def decode_registry(payload: str):
    try:
        raw = base64.b64decode(payload.strip(), validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"ISA registry payload is not valid base64: {exc}") from exc
    try:
        data = gzip.decompress(raw)
    except (gzip.BadGzipFile, EOFError, OSError) as exc:
        raise ValueError(f"ISA registry gzip payload failed CRC/decompression: {exc}") from exc
    try:
        rows = json.loads(data)
    except json.JSONDecodeError as exc:
        raise ValueError(f"ISA registry payload is not valid JSON: {exc}") from exc
    if not isinstance(rows, list):
        raise ValueError("ISA registry JSON must contain a list")
    return rows, raw


def recover_from_git():
    rel = src.relative_to(ROOT).as_posix()
    try:
        payload = subprocess.check_output(
            ["git", "-C", str(ROOT), "show", f"HEAD:{rel}"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    try:
        rows, raw = decode_registry(payload)
    except ValueError:
        return None

    # Repair only the generated transport payload; never invent registry data.
    tmp = src.with_suffix(src.suffix + ".repair.tmp")
    tmp.write_text(payload.strip() + "\n", encoding="utf-8")
    tmp.replace(src)
    print(f"recovered valid ISA registry payload from git HEAD ({len(raw)} bytes)")
    return rows


def load_registry():
    try:
        return decode_registry(src.read_text(encoding="utf-8"))[0]
    except ValueError as local_error:
        recovered = recover_from_git()
        if recovered is not None:
            print(f"warning: {local_error}; restored {src.relative_to(ROOT)} from git HEAD")
            return recovered
        raise SystemExit(
            f"ERROR: {local_error}\n"
            f"Source: {src}\n"
            "The working-tree payload is corrupt and no valid git HEAD copy is available."
        )


rows = load_registry()
out.parent.mkdir(parents=True, exist_ok=True)


def esc(value):
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


required = {"Family", "Architecture", "Mnemonic", "OpcodeHex", "Encoding", "Operands", "Description", "Bits"}
for index, row in enumerate(rows):
    if not isinstance(row, dict) or not required.issubset(row):
        raise SystemExit(f"ERROR: invalid ISA registry row {index}: expected keys {sorted(required)}")

lines = [
    "#pragma once",
    "#include <stdint.h>",
    "struct chimera_isa_entry { const char* family; const char* architecture; const char* mnemonic; const char* opcode; const char* encoding; const char* operands; const char* description; uint16_t bits; };",
    "static const chimera_isa_entry CHIMERA_ISA_REGISTRY[] = {",
]
for row in rows:
    lines.append(
        '  {"%s","%s","%s","%s","%s","%s","%s",%s},'
        % (
            esc(row["Family"]),
            esc(row["Architecture"]),
            esc(row["Mnemonic"]),
            esc(row["OpcodeHex"]),
            esc(row["Encoding"]),
            esc(row["Operands"]),
            esc(row["Description"]),
            row["Bits"] or 0,
        )
    )
lines.append("};")
lines.append(
    "static const uint32_t CHIMERA_ISA_REGISTRY_COUNT = "
    "sizeof(CHIMERA_ISA_REGISTRY)/sizeof(CHIMERA_ISA_REGISTRY[0]);"
)
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"generated {len(rows)} ISA entries -> {out}")
