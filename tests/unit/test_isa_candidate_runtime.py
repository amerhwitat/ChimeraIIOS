#!/usr/bin/env python3
"""Focused tests for the Chimera ISA candidate reference interpreter."""
import importlib.util
import pathlib
import unittest
from types import SimpleNamespace

ROOT=pathlib.Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location("chimera_isa_candidate",ROOT/"tools/isa/chimera_isa_candidate.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)

class CandidateRuntimeTests(unittest.TestCase):
    def test_candidate_inventory_covers_every_architecture(self):
        db=MOD.load_db()
        rows=MOD.build_candidates(db)
        self.assertGreaterEqual(len(rows),len(db["architectures"]))
        self.assertEqual({a[0] for a in db["architectures"]},{r["architecture"] for r in rows})

    def test_supported_add_mapping(self):
        db=MOD.load_db()
        candidates=MOD.build_candidates(db)
        row=next(r for r in candidates if r["architecture"]=="riscv64" and r.get("mnemonic")=="ADD")
        self.assertEqual(row["semantic_operation"],"add")
        self.assertEqual(row["native_mode"]["status"],"reference-micro-op")

    def test_unsupported_candidate_is_not_claimed_executable(self):
        db=MOD.load_db()
        rows=MOD.build_candidates(db)
        row=next(r for r in rows if r["architecture"]=="riscv64" and r.get("mnemonic")=="FENCE")
        self.assertEqual(row["compatibility_mode"]["status"],"unsupported")

    def test_8192_bit_mask(self):
        value=(1<<8192)+7
        self.assertEqual(value & ((1<<8192)-1),7)

    def test_reference_interpreter_executes_catalogued_add(self):
        result=MOD.execute(SimpleNamespace(arch="riscv64",mnemonic="ADD",lhs=12,rhs=30,mode="compatibility"))
        self.assertEqual(result["result"],42)
        self.assertTrue(result["compatibility"]["executed"])

    def test_native_mode_reports_mapping_without_claiming_execution(self):
        result=MOD.execute(SimpleNamespace(arch="riscv64",mnemonic="ADD",lhs=12,rhs=30,mode="native"))
        self.assertEqual(result["mode"],"native-mapping")
        self.assertFalse(result["executed"])

    def test_reference_interpreter_rejects_unsupported_instruction(self):
        with self.assertRaises(NotImplementedError):
            MOD.execute(SimpleNamespace(arch="riscv64",mnemonic="FENCE",lhs=0,rhs=0,mode="compatibility"))

    def test_reference_interpreter_rejects_uncatalogued_instruction(self):
        with self.assertRaises(NotImplementedError):
            MOD.execute(SimpleNamespace(arch="riscv64",mnemonic="BOGUS",lhs=1,rhs=2,mode="compatibility"))

    def test_rv32i_word_decoder_executes_add(self):
        # add x1, x1, x2; x1=12, x2=30 => x1=42
        regs=[0]*32; regs[1]=12; regs[2]=30
        result=MOD.step_rv32i(0x002080b3,regs)
        self.assertEqual(result["registers"][1],42)
        self.assertEqual(result["decoded"]["mnemonic"],"ADD")
        self.assertTrue(result["executed"])

    def test_rv32i_sign_extends_addi_immediate(self):
        # addi x3, x1, -1
        regs=[0]*32; regs[1]=0
        result=MOD.step_rv32i(0xfff08193,regs)
        self.assertEqual(result["registers"][3],0xffffffff)

    def test_rv32i_keeps_zero_register_immutable(self):
        # addi x0, x1, 5
        regs=[0]*32; regs[1]=10
        result=MOD.step_rv32i(0x00508013,regs)
        self.assertEqual(result["registers"][0],0)
        self.assertEqual(result["rd_value"],0)

    def test_rv32i_rejects_reserved_shift_immediate(self):
        with self.assertRaises(ValueError):
            MOD.decode_rv32i(0x02009093)

    def test_rv32i_rejects_instruction_outside_subset(self):
        with self.assertRaises(ValueError):
            MOD.decode_rv32i(0x00000063)  # branch encoding not implemented yet

    def test_formats_include_project_binary(self):
        self.assertIn("ncb",MOD.FORMATS)

if __name__=="__main__": unittest.main()
