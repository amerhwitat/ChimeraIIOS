# Chimera N-bit Python library

Import the library from the repository's `python/` directory:

```python
from chimera_nbit import NBitInt, add, mul, div, bit_xor, fma
a = NBitInt((1 << 8192) - 1, 8193)
b = NBitInt(3, 2)
product = mul(a, b, out_width=8195)
print(product.type_name, product.hex)
print(div(NBitInt(-7, 8, True), 3, signed=True))
```

The library includes typed signed/unsigned N-bit values, exact-width constants,
wrap/trap/saturate overflow policies, add/subtract/multiply/divide/remainder,
bitwise operations, shifts and rotates, comparisons, population count, leading
and trailing zero counts, GCD/LCM, formatting, and Decimal-backed floating
add/subtract/multiply/divide/square-root/FMA.

Integer values are exact. Floating values use Python Decimal precision and are
not binary IEEE-754 bit patterns; do not use this as a bit-exact hardware FPU
model. Python integers are a reference implementation, not a claim of native
register widths. The core has no third-party dependency.
