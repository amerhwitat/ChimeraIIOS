#!/usr/bin/env python3
"""Reference arithmetic engine for Chimera's variable-width N-bit ISA.

This is a host-side executable specification, not a claim that the kernel or
native compilers already emit arbitrary-width machine instructions.
"""
from __future__ import annotations
import argparse
import json
import math
from decimal import Decimal, getcontext

getcontext().prec = 10000

def mask(width: int) -> int:
    if width < 1:
        raise ValueError("width must be >= 1")
    return (1 << width) - 1

def coerce(value: int, width: int, signed: bool = False) -> int:
    value &= mask(width)
    if signed and value & (1 << (width - 1)):
        value -= 1 << width
    return value

def integer_op(op: str, a: int, aw: int, b: int, bw: int, out_width: int,
               signed: bool = False) -> dict:
    if min(aw, bw, out_width) < 1:
        raise ValueError("operand and result widths must be positive")
    a, b = coerce(a, aw, signed), coerce(b, bw, signed)
    if op == "add": result = a + b
    elif op == "sub": result = a - b
    elif op == "mul": result = a * b
    elif op == "div":
        if b == 0: raise ZeroDivisionError("integer division by zero")
        result = abs(a) // abs(b) * (-1 if (a < 0) != (b < 0) else 1)
    elif op == "mod":
        if b == 0: raise ZeroDivisionError("integer modulo by zero")
        q = abs(a) // abs(b) * (-1 if (a < 0) != (b < 0) else 1)
        result = a - q * b
    elif op == "and": result = (a & mask(aw)) & (b & mask(bw))
    elif op == "or": result = (a & mask(aw)) | (b & mask(bw))
    elif op == "xor": result = (a & mask(aw)) ^ (b & mask(bw))
    elif op == "not": result = ~(a & mask(aw))
    elif op == "shl":
        if b < 0: raise ValueError("negative shift count")
        result = (a & mask(aw)) << b
    elif op == "shr":
        if b < 0: raise ValueError("negative shift count")
        result = a >> b if signed else (a & mask(aw)) >> b
    elif op == "eq": result = int(a == b)
    elif op == "ne": result = int(a != b)
    elif op == "lt": result = int(a < b)
    elif op == "le": result = int(a <= b)
    elif op == "gt": result = int(a > b)
    elif op == "ge": result = int(a >= b)
    else: raise ValueError(f"unsupported integer operation: {op}")
    return {"op": op, "a": a, "a_width": aw, "b": b, "b_width": bw,
            "result": coerce(result, out_width, signed), "result_width": out_width,
            "signed": signed, "overflow": not (-(1 << (out_width-1)) <= result < (1 << (out_width-1))) if signed else not (0 <= result <= mask(out_width))}

def float_op(op: str, a: str, b: str, precision: int = 256) -> dict:
    if precision < 2 or precision > 10000:
        raise ValueError("decimal precision must be in 2..10000")
    with __import__("decimal").localcontext() as ctx:
        ctx.prec = precision
        x, y = Decimal(a), Decimal(b)
        if op == "fadd": z = x + y
        elif op == "fsub": z = x - y
        elif op == "fmul": z = x * y
        elif op == "fdiv":
            if y == 0: raise ZeroDivisionError("floating division by zero")
            z = x / y
        elif op == "fsqrt":
            if x < 0: raise ValueError("sqrt domain error")
            z = x.sqrt()
        elif op == "fma": z = x * y + Decimal(0) # third operand is not yet accepted
        else: raise ValueError(f"unsupported floating operation: {op}")
        return {"op": op, "a": str(x), "b": str(y), "result": str(z),
                "precision_decimal_digits": precision, "model": "Decimal reference; not IEEE-754 bit-exact"}

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("op", choices=["add","sub","mul","div","mod","and","or","xor","not","shl","shr","eq","ne","lt","le","gt","ge","fadd","fsub","fmul","fdiv","fsqrt"])
    p.add_argument("a")
    p.add_argument("b", nargs="?", default="0")
    p.add_argument("--a-width", type=int, default=64)
    p.add_argument("--b-width", type=int, default=64)
    p.add_argument("--out-width", type=int, default=128)
    p.add_argument("--signed", action="store_true")
    p.add_argument("--precision", type=int, default=256)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    if args.op.startswith("f"):
        result = float_op(args.op, args.a, args.b, args.precision)
    else:
        result = integer_op(args.op, int(args.a, 0), args.a_width,
                            int(args.b, 0), args.b_width, args.out_width, args.signed)
    print(json.dumps(result, indent=2) if args.json else result["result"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
