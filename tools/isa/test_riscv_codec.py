import importlib.util
import pathlib
import unittest

path = pathlib.Path(__file__).with_name("riscv_codec.py")
spec = importlib.util.spec_from_file_location("riscv_codec", path)
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)


class CodecTests(unittest.TestCase):
    def test_roundtrip_arithmetic(self):
        for asm in ("ADD x1, x2, x3", "SUB x5, x6, x7", "AND x1, x2, x3",
                    "ADDI x1, x2, -12", "LW x3, 8(x4)", "SW x3, -8(x4)",
                    "BEQ x1, x2, 16", "JAL x1, 20", "ECALL", "EBREAK"):
            with self.subTest(asm=asm):
                self.assertEqual(codec.encode(codec.decode(codec.encode(asm))), codec.encode(asm))

    def test_known_add_word(self):
        self.assertEqual(codec.encode("ADD x1, x2, x3"), 0x003100B3)
        self.assertEqual(codec.decode(0x003100B3), "ADD x1, x2, x3")

    def test_execute_arithmetic(self):
        program = [codec.encode("ADDI x1, x0, 7"),
                   codec.encode("ADDI x2, x0, 5"),
                   codec.encode("ADD x3, x1, x2"),
                   codec.encode("ECALL")]
        state = codec.execute(program)
        self.assertEqual(state["registers"][3], 12)
        self.assertEqual(state["registers"][0], 0)

    def test_all_base_instruction_families_roundtrip(self):
        cases = ("LUI x1, 0x12345", "AUIPC x2, 0xABCDE", "JALR x1, 4(x2)",
                 "SLLI x1, x2, 31", "SRLI x1, x2, 3", "SRAI x1, x2, 4",
                 "ORI x1, x2, 255", "FENCE 15, 3")
        for asm in cases:
            with self.subTest(asm=asm):
                self.assertEqual(codec.encode(codec.decode(codec.encode(asm))), codec.encode(asm))

    def test_reserved_shift_encoding_rejected(self):
        # SLLI with a non-zero funct7 is reserved in RV32I.
        with self.assertRaises(ValueError):
            codec.decode(0xFE009093)
        with self.assertRaises(ValueError):
            codec.encode("SLLI x1, x2, 32")

    def test_execution_uses_shared_machine(self):
        state = codec.execute([codec.encode("ADDI x1, x0, 7"),
                               codec.encode("ORI x2, x1, 16"),
                               codec.encode("EBREAK")])
        self.assertEqual(state["engine"], "RV32Machine")
        self.assertEqual(state["registers"][2], 23)

    def test_reject_bad_register_and_range(self):
        with self.assertRaises(ValueError):
            codec.encode("ADD x32, x1, x2")
        with self.assertRaises(ValueError):
            codec.encode("ADDI x1, x2, 4096")


if __name__ == "__main__":
    unittest.main()
