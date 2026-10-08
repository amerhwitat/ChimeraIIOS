import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from chimera_nbit import ChimeraNBit, NBitTrap, OP_LI, OP_ADD, OP_STORE, OP_LOAD, OP_HALT, OP_JZ, OP_JMP

class NBitTests(unittest.TestCase):
    def test_arithmetic_and_zero_register(self):
        c=ChimeraNBit(32); c.load_program([c.encode(OP_LI,1,imm=7),c.encode(OP_LI,2,imm=9),c.encode(OP_ADD,3,1,2),c.encode(OP_HALT)])
        r=c.run(); self.assertTrue(r["halted"]); self.assertEqual(r["registers"][3],16); self.assertEqual(r["registers"][0],0)
    def test_width_wraps_for_negative_immediate(self):
        c=ChimeraNBit(64); c.load_program([c.encode(OP_LI,1,imm=-1),c.encode(OP_HALT)])
        c.run(); self.assertEqual(c.regs[1],(1<<64)-1)
    def test_store_load_round_trip(self):
        c=ChimeraNBit(32); c.regs[1]=512; c.regs[2]=0x12345678
        c.load_program([c.encode(OP_STORE,ra=1,rb=2),c.encode(OP_LOAD,rd=3,ra=1),c.encode(OP_HALT)])
        c.run(); self.assertEqual(c.regs[3],0x12345678)
    def test_invalid_opcode_traps(self):
        c=ChimeraNBit(); c.load_program([c.encode(0x7e)])
        with self.assertRaisesRegex(NBitTrap,"illegal-instruction"): c.run()
    def test_bad_address_traps(self):
        c=ChimeraNBit(); c.regs[1]=c.memory_size-1
        c.load_program([c.encode(OP_LOAD,rd=2,ra=1)])
        with self.assertRaisesRegex(NBitTrap,"load-access"): c.run()
    def test_jz_branch(self):
        c=ChimeraNBit(); c.load_program([c.encode(OP_LI,1,imm=0),c.encode(OP_JZ,ra=1,imm=2),c.encode(OP_LI,2,imm=4),c.encode(OP_LI,2,imm=5),c.encode(OP_HALT)])
        c.run(); self.assertEqual(c.regs[2],5)
    def test_rejects_invalid_width(self):
        with self.assertRaises(ValueError): ChimeraNBit(7)
        with self.assertRaises(ValueError): ChimeraNBit(0)

    def test_register_width_beyond_8192_bits(self):
        width = 16384
        c = ChimeraNBit(width)
        value = (1 << (width - 1)) | 0xA5
        c.regs[1] = value
        c.load_program([c.encode(OP_ADD, 2, 1, 1), c.encode(OP_HALT)])
        c.run()
        self.assertEqual(c.regs[2], (value * 2) & ((1 << width) - 1))
        self.assertEqual(c.nbits, width)

    def test_arbitrary_width_masks_results(self):
        width = 32768
        c = ChimeraNBit(width)
        c.regs[1] = (1 << width) - 1
        c.regs[2] = 1
        c.load_program([c.encode(OP_ADD, 3, 1, 2), c.encode(OP_HALT)])
        c.run()
        self.assertEqual(c.regs[3], 0)
    def test_step_limit(self):
        c=ChimeraNBit(); c.load_program([c.encode(OP_JMP,imm=0)])
        r=c.run(max_steps=5); self.assertEqual(r["steps"],5); self.assertFalse(r["halted"])

if __name__=="__main__": unittest.main()
