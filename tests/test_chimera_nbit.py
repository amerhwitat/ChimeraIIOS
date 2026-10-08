#!/usr/bin/env python3
import importlib.util
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"tools/math/chimera_nbit.py"
spec=importlib.util.spec_from_file_location("chimera_nbit",p)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
assert m.integer_op("add", 255, 8, 1, 1, 9)["result"] == 256
assert m.integer_op("mul", (1<<8192)-1, 8193, 3, 2, 8195)["result"] == ((1<<8192)-1)*3
assert m.integer_op("add", 255, 8, 1, 8, 8)["result"] == 0
assert m.integer_op("div", -7, 8, 3, 8, 8, True)["result"] == -2
assert m.integer_op("mod", -7, 8, 3, 8, 8, True)["result"] == -1
assert m.integer_op("and", 0b111100, 6, 0b1010, 4, 6)["result"] == 0b001000
assert m.float_op("fdiv","1","8",80)["result"] == "0.125"
print("chimera_nbit: 7 checks passed")
