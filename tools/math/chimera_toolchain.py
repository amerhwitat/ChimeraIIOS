#!/usr/bin/env python3
"""Width-aware Chimera N-bit IR, pseudo-assembler, lowering, and debug helpers.

This is an explicit portable IR layer. Backend output is pseudo-assembly until
a selected target's emitter and ABI are implemented and conformance-tested.
"""
from __future__ import annotations
import argparse, json, math, re, struct
from dataclasses import dataclass, asdict
from typing import Optional

OPS = {"add","sub","mul","div","mod","and","or","xor","not","shl","shr",
       "eq","ne","lt","le","gt","ge","fadd","fsub","fmul","fdiv","fsqrt"}
NATIVE_WIDTHS = {"x86_64": {8,16,32,64}, "aarch64": {8,16,32,64},
                 "arm32": {8,16,32}, "rv32": {8,16,32}, "rv64": {8,16,32,64},
                 "mips32": {8,16,32}, "power64": {8,16,32,64}}

@dataclass
class ValueType:
    kind: str
    width: int
    signed: bool = False
    frac: int = 0
    def __post_init__(self):
        if self.kind not in {"int","float","fixed","bool"}: raise ValueError("unknown type kind")
        if self.width < 1: raise ValueError("type width must be positive")
        if self.kind == "fixed" and not 0 <= self.frac < self.width: raise ValueError("fixed fraction must be in [0,width)")
        if self.kind == "bool" and self.width != 1: raise ValueError("bool width must be 1")
    def spelling(self):
        if self.kind == "bool": return "bool"
        if self.kind == "float": return f"f{self.width}"
        if self.kind == "fixed": return f"q{self.width}.{self.frac}"
        return ("i" if self.signed else "u") + str(self.width)

def parse_type(s: str) -> ValueType:
    if s == "bool": return ValueType("bool",1)
    m=re.fullmatch(r"([iu])(\d+)",s)
    if m: return ValueType("int",int(m.group(2)),m.group(1)=="i")
    m=re.fullmatch(r"f(\d+)",s)
    if m: return ValueType("float",int(m.group(1)))
    m=re.fullmatch(r"q(\d+)\.(\d+)",s)
    if m: return ValueType("fixed",int(m.group(1)),True,int(m.group(2)))
    raise ValueError(f"invalid type: {s}")

@dataclass
class Instruction:
    op: str
    dst: str
    dst_type: ValueType
    lhs: str
    lhs_type: ValueType
    rhs: Optional[str] = None
    rhs_type: Optional[ValueType] = None
    overflow: str = "wrap"
    def __post_init__(self):
        if self.op not in OPS: raise ValueError(f"unsupported op: {self.op}")
        if self.overflow not in {"wrap","trap","saturate","flags"}: raise ValueError("invalid overflow policy")
        if self.op not in {"not","fsqrt"} and self.rhs is None: raise ValueError("operation requires rhs")
        if self.op in {"fadd","fsub","fmul","fdiv","fsqrt"} and self.dst_type.kind != "float": raise ValueError("floating op requires float destination")
        if self.op not in {"fadd","fsub","fmul","fdiv","fsqrt"} and self.dst_type.kind not in {"int","bool"}: raise ValueError("integer op requires integer/bool destination")

def parse_instruction(line: str) -> Instruction:
    line=line.split(";",1)[0].strip()
    if not line: raise ValueError("empty instruction")
    # op dst:type, lhs:type, rhs:type [overflow=wrap]
    m=re.fullmatch(r"([a-z]+)\s+([\w.$]+):([\w.]+)\s*,\s*([\w.$+-]+):([\w.]+)(?:\s*,\s*([\w.$+-]+):([\w.]+))?(?:\s+overflow=(wrap|trap|saturate|flags))?",line)
    if not m: raise ValueError("expected: op dst:type, lhs:type[, rhs:type] [overflow=policy]")
    op,dst,dt,lhs,lt,rhs,rt,ov=m.groups()
    return Instruction(op,dst,parse_type(dt),lhs,parse_type(lt),rhs,parse_type(rt) if rt else None,ov or "wrap")

def format_hex(value: int, width: int) -> str:
    if width < 1: raise ValueError("width must be positive")
    return "0x"+format(value & ((1<<width)-1), f"0{(width+3)//4}x")

def debug_value(value: int, typ: ValueType) -> dict:
    if typ.kind in {"int","fixed","bool"}:
        raw=value & ((1<<typ.width)-1)
        signed=raw-(1<<typ.width) if typ.signed and raw&(1<<(typ.width-1)) else raw
        return {"type":typ.spelling(),"hex":format_hex(raw,typ.width),"unsigned":raw,"signed":signed,
                "fixed_value":signed/(1<<typ.frac) if typ.kind=="fixed" else None}
    return {"type":typ.spelling(),"bits":format_hex(value,typ.width),"note":"float bit decoding requires an explicitly defined binary format"}

def lower_instruction(ins: Instruction, target: str) -> list[str]:
    if target not in NATIVE_WIDTHS: raise ValueError(f"unknown target: {target}")
    width=ins.dst_type.width
    if width in NATIVE_WIDTHS[target]:
        return [f"{target}.native.{ins.op}.{ins.dst_type.spelling()} {ins.dst}, {ins.lhs}"+(f", {ins.rhs}" if ins.rhs is not None else "")]
    limbs=(width+63)//64
    lines=[f"; {ins.op} {ins.dst_type.spelling()} lowered as {limbs} x 64-bit limbs on {target}",
           f"CALL __chimera_{ins.op}_{ins.dst_type.spelling()} ; ABI helper, preserve exact widths"]
    if ins.overflow != "wrap": lines.append(f"CHECK_OVERFLOW_POLICY {ins.overflow}")
    return lines

def assemble(source: str) -> dict:
    rows=[]
    for lineno,line in enumerate(source.splitlines(),1):
        if not line.strip() or line.lstrip().startswith(";"): continue
        try:
            ins=parse_instruction(line)
            rows.append({"line":lineno,"instruction":asdict(ins),"canonical":f"{ins.op} {ins.dst}:{ins.dst_type.spelling()}, {ins.lhs}:{ins.lhs_type.spelling()}"+(f", {ins.rhs}:{ins.rhs_type.spelling()}" if ins.rhs_type else "")+f" overflow={ins.overflow}"})
        except Exception as e: raise ValueError(f"line {lineno}: {e}") from e
    return {"format":"CHIR-NIR-1","instructions":rows}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("assemble"); a.add_argument("source")
    d=sub.add_parser("disassemble"); d.add_argument("ir")
    l=sub.add_parser("lower"); l.add_argument("source"); l.add_argument("--target",choices=sorted(NATIVE_WIDTHS),required=True)
    g=sub.add_parser("debug"); g.add_argument("type"); g.add_argument("value",type=lambda x:int(x,0))
    args=p.parse_args()
    if args.cmd=="assemble":
        with open(args.source,encoding="utf-8") as f: out=assemble(f.read())
    elif args.cmd=="disassemble":
        with open(args.ir,encoding="utf-8") as f: data=json.load(f)
        out=[row["canonical"] for row in data["instructions"]]
    elif args.cmd=="lower":
        with open(args.source,encoding="utf-8") as f: data=assemble(f.read())
        out=[]
        for row in data["instructions"]:
            d=row["instruction"]; dt=d["dst_type"]; lt=d["lhs_type"]; rt=d["rhs_type"]
            ins=Instruction(d["op"],d["dst"],ValueType(**dt),d["lhs"],ValueType(**lt),d["rhs"],ValueType(**rt) if rt else None,d["overflow"])
            out.extend(lower_instruction(ins,args.target))
    else: out=debug_value(args.value,parse_type(args.type))
    print(json.dumps(out,indent=2))
if __name__=="__main__": main()
