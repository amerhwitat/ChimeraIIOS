#!/usr/bin/env python3
"""Build an experimental NCB1 executable from a JSON manifest."""
import argparse
import json
import sys
from pathlib import Path

# Support invocation from any working directory.
TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

from chimera_binary import (  # noqa: E402
    NCB_HEADER, NCB_SECTION, MAX_SECTIONS, validate_ncb, NCB_MAGIC,
)


def build(manifest_path, output_path):
    manifest = Path(manifest_path).expanduser().resolve()
    if not manifest.is_file():
        raise FileNotFoundError(f"manifest is not a regular file: {manifest}")
    try:
        m = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON manifest {manifest}: {exc}") from exc
    if not isinstance(m, dict):
        raise ValueError("manifest root must be a JSON object")

    word = int(m["word_bits"])
    isa = int(m.get("isa_id", 1))
    flags = int(m.get("flags", 0))
    stack = int(m.get("stack_bytes", 1 << 20))
    heap = int(m.get("heap_limit_bytes", 1 << 30))
    base = int(m.get("image_base", 0))
    sections = m["sections"]
    if not 8 <= word <= 1048576 or word % 8:
        raise ValueError("word_bits must be byte-aligned 8..1048576")
    if not isinstance(sections, list) or not 1 <= len(sections) <= MAX_SECTIONS:
        raise ValueError("sections must be a list containing 1..128 entries")

    table = NCB_HEADER.size
    cursor = table + len(sections) * NCB_SECTION.size
    records, payloads = [], []
    entry = 0
    entry_name = m.get("entry_section", ".text")
    for index, section in enumerate(sections):
        if not isinstance(section, dict) or "name" not in section:
            raise ValueError(f"section {index} must be an object with a name")
        name_text = str(section["name"])
        try:
            name = name_text.encode("ascii")
        except UnicodeEncodeError as exc:
            raise ValueError(f"section name must be ASCII: {name_text!r}") from exc
        if not name or len(name) > 15:
            raise ValueError("section name must be 1..15 ASCII bytes")
        fl = int(section.get("flags", 4))
        align = int(section.get("alignment", 1))
        if align < 1 or align & (align - 1):
            raise ValueError("alignment must be a positive power of two")
        cursor = (cursor + align - 1) & ~(align - 1)
        if "path" in section and "hex" in section:
            raise ValueError(f"section {name_text}: specify either path or hex, not both")
        if "path" in section:
            payload_path = Path(section["path"]).expanduser()
            if not payload_path.is_absolute():
                payload_path = manifest.parent / payload_path
            if not payload_path.is_file():
                raise FileNotFoundError(f"section payload is not a regular file: {payload_path}")
            data = payload_path.read_bytes()
        elif "hex" in section:
            try:
                data = bytes.fromhex(section["hex"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"section {name_text}: invalid hexadecimal payload") from exc
        else:
            data = b""
        mem = int(section.get("memory_size", len(data)))
        if mem < len(data) or mem < 0:
            raise ValueError("memory_size cannot be smaller than file data or negative")
        records.append((name, fl, cursor, len(data), mem, align))
        payloads.append((cursor, data))
        if name_text == entry_name:
            off = int(m.get("entry_offset_in_section", 0))
            if not fl & 1 or not 0 <= off < len(data):
                raise ValueError("entry must be in file-backed executable section")
            entry = cursor + off
        cursor += len(data)
    if not entry:
        raise ValueError("entry section missing or invalid")

    out = bytearray(cursor)
    for i, record in enumerate(records):
        NCB_SECTION.pack_into(out, table + i * NCB_SECTION.size,
                              record[0].ljust(16, b"\0"), *record[1:])
    for offset, data in payloads:
        out[offset:offset + len(data)] = data
    NCB_HEADER.pack_into(out, 0, NCB_MAGIC, 1, NCB_HEADER.size, flags, isa,
                         word, len(records), entry, table, len(out), stack,
                         heap, base, 0)
    validate_ncb(bytes(out))
    output = Path(output_path).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(out)
    return {"output": str(output), "file_size": len(out), "word_bits": word,
            "sections": len(records), "entry_offset": entry}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="path to a JSON NCB1 manifest")
    parser.add_argument("output", help="path for the generated NCB1 file")
    args = parser.parse_args()
    try:
        result = build(args.manifest, args.output)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
