#!/usr/bin/env python3
"""Generate a compact 30-instruction encoder/decoder fixture from the canonical registry."""
from __future__ import annotations
import argparse, json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("registry", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--count", type=int, default=30)
    args = ap.parse_args()
    data = json.loads(args.registry.read_text(encoding="utf-8"))
    instructions = data["instructions"][: args.count]
    if len(instructions) < args.count:
        raise SystemExit(f"registry contains only {len(instructions)} instructions")
    sample = {
        "schema": "chimera-ii-isa-encoder-decoder-sample",
        "schema_version": 1,
        "source_registry": "tools/isa/isa_bitfields.json",
        "instruction_count": len(instructions),
        "instructions": instructions,
    }
    args.output.write_text(json.dumps(sample, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
