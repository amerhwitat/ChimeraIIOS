#!/usr/bin/env python3
import importlib.util, json, tempfile
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"tools/math/chimera_toolchain.py"
s=importlib.util.spec_from_file_location("ct",p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
assert m.parse_type("u8193").width==8193
assert m.parse_type("i257").signed
assert m.parse_type("q128.32").frac==32
assert m.format_hex(-1,9)=="0x1ff"
v=m.debug_value(-1,m.parse_type("i8")); assert v["signed"]==-1 and v["unsigned"]==255
ins=m.parse_instruction("add result:u9000, lhs:u257, rhs:u8193 overflow=wrap")
assert ins.dst_type.width==9000
lo=m.lower_instruction(ins,"x86_64"); assert any("__chimera_add_u9000" in x for x in lo)
assert m.lower_instruction(m.parse_instruction("add r:u64, a:u64, b:u64"),"x86_64")[0].startswith("x86_64.native")
asm=m.assemble("; test\nadd result:u9000, lhs:u257, rhs:u8193 overflow=wrap")
assert asm["format"]=="CHIR-NIR-1" and len(asm["instructions"])==1
try: m.parse_type("u0"); raise AssertionError("u0 accepted")
except ValueError: pass
print("chimera_toolchain: 9 checks passed")
