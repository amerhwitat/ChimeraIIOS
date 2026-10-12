#!/usr/bin/env python3
"""Byte/bit utilities for ISA encodings; not a substitute for ISA-specific codecs."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

def bitstring_to_int(bits: str) -> int:
    if not bits or any(c not in "01" for c in bits):
        raise ValueError("encoding must be a non-empty binary string")
    return int(bits, 2)

def encode_bytes(bits: str, byte_order: str, *, parcel_bits: int | None = None) -> bytes:
    value = bitstring_to_int(bits)
    width = len(bits)
    if width % 8:
        raise ValueError("byte serialization requires a whole number of bytes")
    if byte_order == "instruction-little":
        # RISC-V instruction parcels are little-endian 16-bit units even when
        # data memory byte order differs; preserve parcel order by address.
        parcel_bits = parcel_bits or 16
        if width % parcel_bits or parcel_bits % 8:
            raise ValueError("instruction parcel width must divide the encoding and be byte aligned")
        chunks = [bits[i:i+parcel_bits] for i in range(0, width, parcel_bits)]
        return b"".join(int(chunk, 2).to_bytes(parcel_bits // 8, "little") for chunk in chunks)
    if byte_order not in {"little", "big"}:
        raise ValueError("byte order must be little, big, or instruction-little")
    return value.to_bytes(width // 8, byte_order)

def decode_bytes(data: bytes, byte_order: str, *, parcel_bits: int | None = None) -> str:
    if not data:
        raise ValueError("empty instruction bytes")
    if byte_order == "instruction-little":
        parcel_bits = parcel_bits or 16
        parcel_bytes = parcel_bits // 8
        if parcel_bytes < 1 or len(data) % parcel_bytes:
            raise ValueError("data length is not a whole number of instruction parcels")
        chunks = [format(int.from_bytes(data[i:i+parcel_bytes], "little"), f"0{parcel_bits}b")
                  for i in range(0, len(data), parcel_bytes)]
        return "".join(chunks)
    if byte_order not in {"little", "big"}:
        raise ValueError("byte order must be little, big, or instruction-little")
    return format(int.from_bytes(data, byte_order), f"0{len(data)*8}b")

def apply_mask(value_bits: str, mask_bits: str, candidate_bits: str) -> bool:
    if not (len(value_bits) == len(mask_bits) == len(candidate_bits)):
        return False
    if any(c not in "01" for c in value_bits + mask_bits + candidate_bits):
        return False
    return all(m == "0" or v == c for v, m, c in zip(value_bits, mask_bits, candidate_bits))

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--bits", help="instruction encoding bits to serialize")
    p.add_argument("--bytes", help="hex bytes to decode")
    p.add_argument("--order", required=True, choices=["little", "big", "instruction-little"])
    p.add_argument("--parcel-bits", type=int, default=16)
    a = p.parse_args()
    if a.bits is not None:
        print(encode_bytes(a.bits, a.order, parcel_bits=a.parcel_bits).hex(" "))
    elif a.bytes is not None:
        raw = bytes.fromhex(a.bytes)
        print(decode_bytes(raw, a.order, parcel_bits=a.parcel_bits))
    else:
        p.error("provide --bits or --bytes")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
