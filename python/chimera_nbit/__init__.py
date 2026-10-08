"""Chimera N-bit arithmetic library.

Variable-width integer operations use Python's exact integers as the reference
model. Floating operations use Decimal and are not bit-exact IEEE-754 emulation.
"""
from .core import (
    NBitInt, NBitFloat, NBitConstant, NBitError, OverflowMode,
    add, sub, mul, div, mod, bit_and, bit_or, bit_xor, bit_not,
    shl, shr, rol, ror, compare, popcount, clz, ctz, gcd, lcm,
    fadd, fsub, fmul, fdiv, fsqrt, fma, parse_int, format_value,
    MASK, ZERO, ONE, PI, E,
)
__all__ = [name for name in globals() if not name.startswith("_")]
