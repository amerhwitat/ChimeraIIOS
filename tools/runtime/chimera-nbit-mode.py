#!/usr/bin/env python3
"""Inspect or exercise Chimera's software N-bit integer mode.

This command uses Python's arbitrary-precision integers as a software reference
model. It does not claim that the host CPU has native registers of the selected
width, and it does not execute Chimera guest machine code.
"""
from __future__ import annotations

import argparse
import json
import sys

MIN_BITS = 8
MAX_BITS = 65536


def parse_width(value: str) -> int:
    try:
        width = int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("width must be an integer") from exc
    if width < MIN_BITS or width > MAX_BITS or width % 8:
        raise argparse.ArgumentTypeError("width must be byte-aligned and in 8..65536")
    return width


def evaluate(operation: str, lhs: int, rhs: int, width: int) -> int:
    mask = (1 << width) - 1
    lhs &= mask
    rhs &= mask
    if operation == "add":
        value = lhs + rhs
    elif operation == "sub":
        value = lhs - rhs
    elif operation == "and":
        value = lhs & rhs
    elif operation == "or":
        value = lhs | rhs
    elif operation == "xor":
        value = lhs ^ rhs
    elif operation == "shl":
        value = lhs << rhs if rhs < width else 0
    elif operation == "shr":
        value = lhs >> rhs if rhs < width else 0
    else:
        raise ValueError(f"unsupported operation: {operation}")
    return value & mask


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=parse_width, default=8192)
    parser.add_argument("--operation", choices=("add", "sub", "and", "or", "xor", "shl", "shr"))
    parser.add_argument("--lhs", type=lambda x: int(x, 0))
    parser.add_argument("--rhs", type=lambda x: int(x, 0))
    parser.add_argument("--json", action="store_true", help="emit machine-readable mode metadata")
    args = parser.parse_args(argv)

    info = {
        "schema": "CHIMERA-NBIT-MODE-1",
        "width_bits": args.width,
        "execution": "software-reference",
        "hardware_native": False,
        "guest_isa_execution": False,
        "note": "Software reference arithmetic only; no native host-width or guest-execution claim.",
    }
    if args.operation is None:
        print(json.dumps(info, indent=2) if args.json else
              f"Chimera software N-bit mode: {args.width} bits (reference model; not native hardware)")
        return 0
    if args.lhs is None or args.rhs is None:
        parser.error("--operation requires both --lhs and --rhs")
    result = evaluate(args.operation, args.lhs, args.rhs, args.width)
    if args.json:
        info.update({"operation": args.operation, "lhs": hex(args.lhs), "rhs": hex(args.rhs), "result": hex(result)})
        print(json.dumps(info, indent=2))
    else:
        print(f"0x{result:X}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OverflowError) as exc:
        print(f"chimera-nbit-mode: {exc}", file=sys.stderr)
        raise SystemExit(2)
