#!/usr/bin/env python3
import importlib.util, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("chimera_nbit_core",root/"python/chimera_nbit/core.py")
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
assert m.add(m.NBitInt(255,8),1,out_width=9).value==256
assert m.add(m.NBitInt(255,8),1,out_width=8).value==0
assert m.mul(m.NBitInt((1<<8192)-1,8193),3,out_width=8195).value==((1<<8192)-1)*3
assert m.div(m.NBitInt(-7,8,True),3,signed=True).value==-2
assert m.mod(m.NBitInt(-7,8,True),3,signed=True).value==-1
assert m.bit_and(m.NBitInt(0b111100,6),m.NBitInt(0b1010,4),out_width=6).value==8
assert m.rol(m.NBitInt(0b10000001,8),1).value==3
assert m.ror(m.NBitInt(3,8),1).value==129
assert m.popcount(m.NBitInt(0b101101,6))==4
assert m.clz(m.NBitInt(1,8))==7 and m.ctz(m.NBitInt(8,8))==3
assert str(m.fdiv("1","8",precision=80).value)=="0.125"
assert str(m.fma(2,3,4,precision=30).value)=="10"
assert m.NBitConstant("K",255,"u8").resolve().value==255
try: m.div(1,0); raise AssertionError("division by zero accepted")
except ZeroDivisionError: pass
try: m.add(m.NBitInt(127,8,True),1,out_width=8,signed=True,overflow=m.OverflowMode.TRAP); raise AssertionError("overflow accepted")
except OverflowError: pass
print("python N-bit library: 14 checks passed")
