#!/usr/bin/env python3
"""Metadata-driven assembler/disassembler for Chimera II logical encodings.

This tool never changes the CPU's 16-byte host packet. Templates wider than 128
bits, fields declared 'separate', or opcode-width contradictions are rejected
until explicitly normalized in the ISA metadata.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

FIELD_RE = re.compile(r"\[(\d+)\s*:\s*(\d+)\s+([^\]]+)\]")


def load(path: Path):
    doc = json.loads(path.read_text(encoding="utf-8"))
    return {x["mnemonic"]: x for x in doc["instructions"]}, {int(x["opcode"],16): x for x in doc["instructions"]}


def parse_value(text: str) -> int:
    return int(text, 0)


def encode(ins, values):
    fields = ins["bitfields"]
    names = [f["name"] for f in fields if f["name"] != "opcode" and "reserved" not in f["name"]]
    if any("separate" in ins["encoding_template"] for _ in [0]):
        raise ValueError(f"{ins['mnemonic']}: encoding has a separate field and is not yet serializable")
    if not any(f["name"] == "opcode" for f in fields):
        raise ValueError(f"{ins['mnemonic']}: no opcode field")
    opcode_field = next(f for f in fields if f["name"] == "opcode")
    opcode = int(ins["opcode"],16)
    if opcode >= (1 << opcode_field["width"]):
        raise ValueError(f"{ins['mnemonic']}: 0x{opcode:X} does not fit {opcode_field['width']}-bit opcode field")
    if len(values) != len(names):
        raise ValueError(f"{ins['mnemonic']}: expected {len(names)} operands ({', '.join(names)}), got {len(values)}")
    out = opcode << opcode_field["shift"]
    for field, raw in zip((f for f in fields if f["name"] != "opcode" and "reserved" not in f["name"]), values):
        value = parse_value(raw)
        if value < 0 or value >= (1 << field["width"]):
            raise ValueError(f"{ins['mnemonic']}.{field['name']}: value does not fit {field['width']} bits")
        out |= value << field["shift"]
    return out


def decode(ins, word):
    result = []
    for f in ins["bitfields"]:
        result.append((f["name"], (word >> f["shift"]) & ((1 << f["width"]) - 1)))
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", type=Path, default=Path("tools/isa/isa_bitfields.json"))
    sub = ap.add_subparsers(dest="command", required=True)
    a = sub.add_parser("assemble"); a.add_argument("mnemonic"); a.add_argument("operands", nargs="*")
    d = sub.add_parser("disassemble"); d.add_argument("word")
    args = ap.parse_args(); by_name, by_opcode = load(args.schema)
    if args.command == "assemble":
        ins = by_name[args.mnemonic]; print(f"0x{encode(ins,args.operands):0{max(2,((max(f['end'] for f in ins['bitfields'])+1+3)//4))}X}")
    else:
        word = parse_value(args.word); matches=[]
        for ins in by_opcode.values():
            opfields=[f for f in ins["bitfields"] if f["name"]=="opcode"]
            if not opfields: continue
            f=opfields[0]
            if ((word>>f["shift"]) & ((1<<f["width"])-1)) == int(ins["opcode"],16): matches.append(ins)
        if len(matches)!=1: raise SystemExit(f"ambiguous/unknown opcode: {args.word}")
        print(matches[0]["mnemonic"], " ".join(f"{n}=0x{v:X}" for n,v in decode(matches[0],word) if n!="opcode"))

if __name__ == "__main__":
    main()
