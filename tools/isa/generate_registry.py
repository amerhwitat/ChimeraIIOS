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
canonical_db = ROOT / "isa/isa_database.json"


def decode_registry(payload: str):
    try:
        raw = base64.b64decode(payload.strip(), validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(
            f"ISA registry payload is not valid base64: {exc}"
        ) from exc

    try:
        data = gzip.decompress(raw)
    except (gzip.BadGzipFile, EOFError, OSError) as exc:
        raise ValueError(
            f"ISA registry gzip payload failed CRC/decompression: {exc}"
        ) from exc

    try:
        rows = json.loads(data)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"ISA registry payload is not valid JSON: {exc}"
        ) from exc

    if not isinstance(rows, list):
        raise ValueError("ISA registry JSON must contain a list")

    return rows, raw


def registry_rows_from_canonical_database():
    if not canonical_db.exists():
        return None

    try:
        db = json.loads(canonical_db.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"warning: cannot read canonical ISA database: {exc}")
        return None

    architectures = {}

    for row in db.get("architectures", []):
        if len(row) >= 3:
            architectures[row[0]] = {
                "class": row[1],
                "family": row[2],
            }

    instructions = db.get("instructions", [])

    if not instructions:
        print("warning: canonical ISA database contains no instructions")
        return None

    rows = []

    for index, item in enumerate(instructions):
        if not isinstance(item, list) or len(item) != 8:
            print(
                f"warning: skipping malformed canonical ISA row {index}"
            )
            continue

        (
            architecture,
            mnemonic,
            form_id,
            operands,
            syntax,
            length_bits,
            value_bits,
            mask_bits,
        ) = item

        arch = architectures.get(architecture)

        if arch is None:
            print(
                f"warning: skipping ISA row {index}: "
                f"unknown architecture {architecture}"
            )
            continue

        try:
            length_bits = int(length_bits)
            value = int(str(value_bits), 2)

            hex_digits = max(1, (length_bits + 3) // 4)
            opcode_hex = "0x" + format(
                value,
                f"0{hex_digits}X",
            )
        except (TypeError, ValueError):
            opcode_hex = "0x0"

        if operands:
            operand_text = ", ".join(str(x) for x in operands)
        else:
            operand_text = "none"

        rows.append(
            {
                "Family": arch["family"],
                "Architecture": architecture,
                "Mnemonic": mnemonic,
                "OpcodeHex": opcode_hex,
                "Encoding": str(mask_bits),
                "Operands": operand_text,
                "Description": f"{syntax} [{form_id}]",
                "Bits": length_bits,
            }
        )

    if not rows:
        return None

    return rows


def write_canonical_payload(rows):
    payload_json = json.dumps(
        rows,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    compressed = gzip.compress(
        payload_json,
        compresslevel=9,
        mtime=0,
    )

    encoded = base64.b64encode(compressed).decode("ascii")

    src.parent.mkdir(parents=True, exist_ok=True)

    tmp = src.with_suffix(src.suffix + ".canonical.tmp")
    tmp.write_text(encoded + "\n", encoding="ascii")
    tmp.replace(src)

    # Validate what we just wrote.
    decoded_rows, raw = decode_registry(encoded)

    if len(decoded_rows) != len(rows):
        raise RuntimeError(
            "canonical ISA payload validation changed row count"
        )

    print(
        "recovered ISA registry from canonical "
        f"isa/isa_database.json ({len(raw)} bytes, "
        f"{len(decoded_rows)} entries)"
    )

    return decoded_rows


def recover_from_git():
    rel = src.relative_to(ROOT).as_posix()

    try:
        payload = subprocess.check_output(
            ["git", "-C", str(ROOT), "show", f"HEAD:{rel}"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
    ):
        return None

    try:
        rows, raw = decode_registry(payload)
    except ValueError:
        return None

    tmp = src.with_suffix(src.suffix + ".repair.tmp")
    tmp.write_text(payload.strip() + "\n", encoding="utf-8")
    tmp.replace(src)

    print(
        f"recovered valid ISA registry payload from git HEAD "
        f"({len(raw)} bytes)"
    )

    return rows


def load_registry():
    # 1. Try the working-tree payload.
    try:
        return decode_registry(
            src.read_text(encoding="utf-8")
        )[0]

    except (OSError, ValueError) as local_error:

        # 2. Try a valid Git HEAD copy.
        recovered = recover_from_git()

        if recovered is not None:
            print(
                f"warning: {local_error}; "
                f"restored {src.relative_to(ROOT)} from git HEAD"
            )
            return recovered

        # 3. Rebuild from the canonical JSON database.
        canonical_rows = registry_rows_from_canonical_database()

        if canonical_rows is not None:
            print(
                f"warning: {local_error}; "
                "rebuilding ISA registry from canonical database"
            )
            return write_canonical_payload(canonical_rows)

        raise SystemExit(
            f"ERROR: {local_error}\n"
            f"Source: {src}\n"
            "The working-tree payload is corrupt, git HEAD is "
            "also invalid, and the canonical ISA database could "
            "not be used."
        )


rows = load_registry()

out.parent.mkdir(parents=True, exist_ok=True)


def esc(value):
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
    )


required = {
    "Family",
    "Architecture",
    "Mnemonic",
    "OpcodeHex",
    "Encoding",
    "Operands",
    "Description",
    "Bits",
}


for index, row in enumerate(rows):
    if not isinstance(row, dict) or not required.issubset(row):
        raise SystemExit(
            f"ERROR: invalid ISA registry row {index}: "
            f"expected keys {sorted(required)}"
        )


lines = [
    "#pragma once",
    "#include <stdint.h>",
    (
        "struct chimera_isa_entry { "
        "const char* family; "
        "const char* architecture; "
        "const char* mnemonic; "
        "const char* opcode; "
        "const char* encoding; "
        "const char* operands; "
        "const char* description; "
        "uint16_t bits; "
        "};"
    ),
    (
        "static const chimera_isa_entry "
        "CHIMERA_ISA_REGISTRY[] = {"
    ),
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
    "sizeof(CHIMERA_ISA_REGISTRY)/"
    "sizeof(CHIMERA_ISA_REGISTRY[0]);"
)

out.write_text(
    "\n".join(lines) + "\n",
    encoding="utf-8",
)

print(
    f"generated {len(rows)} ISA entries -> {out}"
)
