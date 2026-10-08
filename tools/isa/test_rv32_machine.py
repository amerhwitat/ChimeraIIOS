import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from rv32_machine import RV32Machine, Trap


def enc_i(imm, rs1, f3, rd, op=0x13):
    return ((imm & 0xfff)<<20)|(rs1<<15)|(f3<<12)|(rd<<7)|op

def enc_s(imm, rs2, rs1, f3=2):
    u=imm&0xfff
    return ((u>>5)<<25)|(rs2<<20)|(rs1<<15)|(f3<<12)|((u&31)<<7)|0x23


class MachineTests(unittest.TestCase):
    def machine(self, words):
        m=RV32Machine(memory_size=256)
        m.load(0,b''.join(w.to_bytes(4,'little') for w in words))
        return m

    def test_load_store_and_signed_load(self):
        m=self.machine([enc_i(128,0,0,1),enc_i(-1,0,0,2),enc_s(0,2,1,0),
                        enc_i(0,1,0,3,0x03),enc_i(0,1,4,4,0x03),0x00100073])
        out=m.run()
        self.assertEqual(out['registers'][3],0xffffffff)
        self.assertEqual(out['registers'][4],255)

    def test_store_and_load_word(self):
        m=self.machine([enc_i(64,0,0,1),enc_i(123,0,0,2),enc_s(0,2,1),
                        enc_i(0,1,2,3,0x03),0x00100073])
        out=m.run()
        self.assertEqual(out['registers'][3],123)

    def test_illegal_instruction_traps(self):
        m=self.machine([0xffffffff])
        out=m.run()
        self.assertTrue(out['halted'])
        self.assertEqual(out['mcause'],2)
        self.assertEqual(out['mepc'],0)
        self.assertEqual(out['mtval'],0xffffffff)

    def test_load_misalignment_traps(self):
        m=self.machine([enc_i(1,0,0,1),enc_i(0,1,2,2,0x03)])
        out=m.run()
        self.assertEqual(out['mcause'],4)
        self.assertEqual(out['mepc'],4)

    def test_ori_uses_bitwise_or(self):
        m=self.machine([enc_i(0x100,0,0,1), enc_i(0x10,1,6,2), 0x00100073])
        out=m.run()
        self.assertEqual(out['registers'][2],0x110)

    def test_fence_base_encoding_and_illegal_fence_i(self):
        m=self.machine([0x0ff0000f, 0x00100073])
        self.assertTrue(m.run()['halted'])
        bad=self.machine([0x0000100f])
        out=bad.run()
        self.assertEqual(out['mcause'],2)
        self.assertEqual(out['mtval'],0x0000100f)

    def test_trapping_instructions_count_toward_step_limit(self):
        m=self.machine([0x00100073, 0xffffffff])
        m.mtvec=4
        out=m.run(max_steps=5)
        self.assertEqual(out['steps'],5)
        self.assertFalse(out['halted'])

    def test_x0_is_hardwired(self):
        m=self.machine([enc_i(7,0,0,0),0x00100073])
        self.assertEqual(m.run()['registers'][0],0)


if __name__ == '__main__':
    unittest.main()
