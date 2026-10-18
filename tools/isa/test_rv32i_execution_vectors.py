#!/usr/bin/env python3
"""Focused RV32I execution vectors for the implemented Python interpreter subset."""
import importlib.util
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("chimera_riscv_codec",ROOT/"tools/isa/riscv_codec.py")
codec=importlib.util.module_from_spec(spec);spec.loader.exec_module(codec)
sys.path.insert(0,str(ROOT/"tools/isa"))
from rv32_machine import RV32Machine

def run(assembly,memory_size=256):
 words=[codec.encode(line) for line in assembly]
 machine=RV32Machine(memory_size=memory_size)
 machine.load(0,b"".join(w.to_bytes(4,"little") for w in words))
 machine.run(max_steps=len(words)+1)
 return machine

class RV32IExecutionVectors(unittest.TestCase):
 def test_integer_register_alu_families_execute(self):
  m=run(["ADDI x1, x0, 12","ADDI x2, x0, 3","ADD x3, x1, x2","SUB x4, x1, x2",
         "SLL x5, x2, x2","SLT x6, x2, x1","SLTU x7, x2, x1","XOR x8, x1, x2",
         "SRL x9, x1, x2","OR x10, x1, x2","AND x11, x1, x2","SRA x12, x1, x2","EBREAK"])
  self.assertEqual(m.regs[3:13],[15,9,24,1,1,15,1,15,0,1])
 def test_immediate_alu_and_shift_families_execute(self):
  m=run(["ADDI x1, x0, 12","ADDI x2, x1, -4","SLTI x3, x1, 13","SLTIU x4, x1, 13",
         "XORI x5, x1, 3","ORI x6, x1, 3","ANDI x7, x1, 10","SLLI x8, x1, 2",
         "SRLI x9, x1, 2","SRAI x10, x1, 2","EBREAK"])
  self.assertEqual(m.regs[2:11],[8,1,1,15,15,8,48,3,3])
 def test_signed_unsigned_loads_and_all_store_widths(self):
  m=run(["ADDI x1, x0, 64","ADDI x2, x0, 255","SB x2, 0(x1)","LB x3, 0(x1)","LBU x4, 0(x1)",
         "SH x2, 2(x1)","LH x5, 2(x1)","LHU x6, 2(x1)","SW x2, 4(x1)","LW x7, 4(x1)","EBREAK"])
  self.assertEqual(m.regs[3],0xffffffff);self.assertEqual(m.regs[4],255)
  self.assertEqual(m.regs[5],255);self.assertEqual(m.regs[6],255);self.assertEqual(m.regs[7],255)
 def test_all_branch_conditions_take_and_skip_expected_paths(self):
  cases=[("BEQ",5,5,True),("BNE",5,5,False),("BLT",4,5,True),("BGE",5,5,True),("BLTU",4,5,True),("BGEU",5,4,True)]
  for op,left,right,taken in cases:
   with self.subTest(op=op):
    m=run([f"ADDI x1, x0, {left}",f"ADDI x2, x0, {right}",f"{op} x1, x2, 8","ADDI x3, x0, 1","ADDI x3, x0, 2","EBREAK"])
    self.assertEqual(m.regs[3],2 if taken else 1)
 def test_signed_comparisons_and_arithmetic_shift(self):
  m=run(["ADDI x1, x0, -8","SRAI x2, x1, 1","SLT x3, x1, x0","SLTU x4, x1, x0","EBREAK"])
  self.assertEqual(m.regs[2],0xfffffffc)
  self.assertEqual(m.regs[3],1)
  self.assertEqual(m.regs[4],0)
 def test_jal_and_jalr_execute_with_link_addresses(self):
  jal=run(["JAL x1, 8","ADDI x2, x0, 1","ADDI x2, x0, 2","EBREAK"])
  self.assertEqual(jal.regs[1],4);self.assertEqual(jal.regs[2],2)
  jalr=run(["ADDI x1, x0, 12","JALR x2, 0(x1)","ADDI x3, x0, 1","ADDI x3, x0, 2","EBREAK"])
  self.assertEqual(jalr.regs[2],8);self.assertEqual(jalr.regs[3],2)
 def test_jumps_link_register_and_upper_immediates_roundtrip(self):
  for asm in ("LUI x1, 0x12345","AUIPC x2, 0xABCDE","JAL x1, 20","JALR x1, 4(x2)"):
   with self.subTest(asm=asm):
    word=codec.encode(asm);self.assertEqual(codec.encode(codec.decode(word)),word)
if __name__=="__main__":unittest.main()
