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


    def test_all_supported_rv32i_base_mnemonics_roundtrip(self):
        # These are the explicitly supported RV32I codec forms. Passing this
        # test means encode/decode round-trip only, not architectural conformance.
        cases = (
            "ADD x1, x2, x3", "SUB x1, x2, x3", "SLL x1, x2, x3",
            "SLT x1, x2, x3", "SLTU x1, x2, x3", "XOR x1, x2, x3",
            "SRL x1, x2, x3", "SRA x1, x2, x3", "OR x1, x2, x3", "AND x1, x2, x3",
            "ADDI x1, x2, -12", "SLTI x1, x2, -1", "SLTIU x1, x2, 7",
            "XORI x1, x2, 15", "ORI x1, x2, 255", "ANDI x1, x2, 31",
            "SLLI x1, x2, 31", "SRLI x1, x2, 3", "SRAI x1, x2, 4",
            "LB x1, 8(x2)", "LH x1, 8(x2)", "LW x1, 8(x2)",
            "LBU x1, 8(x2)", "LHU x1, 8(x2)",
            "SB x1, 8(x2)", "SH x1, 8(x2)", "SW x1, 8(x2)",
            "BEQ x1, x2, 16", "BNE x1, x2, 16", "BLT x1, x2, 16",
            "BGE x1, x2, 16", "BLTU x1, x2, 16", "BGEU x1, x2, 16",
            "LUI x1, 0x12345", "AUIPC x1, 0x12345",
            "JAL x1, 20", "JALR x1, 4(x2)", "FENCE 15, 3", "ECALL", "EBREAK"
        )
        for asm in cases:
            with self.subTest(asm=asm):
                word = codec.encode(asm)
                self.assertEqual(codec.encode(codec.decode(word)), word)

    def test_execute_all_integer_register_alu_families(self):
        cases = (
            ("ADD x3, x1, x2", 8), ("SUB x3, x1, x2", 2),
            ("SLL x3, x2, x2", 24), ("SLT x3, x2, x1", 1),
            ("SLTU x3, x1, x2", 0), ("XOR x3, x1, x2", 6),
            ("SRL x3, x1, x2", 0), ("SRA x3, x1, x2", 0),
            ("OR x3, x1, x2", 7), ("AND x3, x1, x2", 1),
            ("ADDI x3, x1, -2", 3), ("SLTI x3, x1, 8", 1),
            ("SLTIU x3, x1, 8", 1), ("XORI x3, x1, 3", 6),
            ("ORI x3, x1, 2", 7), ("ANDI x3, x1, 3", 1),
            ("SLLI x3, x2, 2", 12), ("SRLI x3, x1, 1", 2),
        )
        for asm, expected in cases:
            with self.subTest(asm=asm):
                state = codec.execute([codec.encode("ADDI x1, x0, 5"),
                                       codec.encode("ADDI x2, x0, 3"),
                                       codec.encode(asm), codec.encode("EBREAK")])
                self.assertEqual(state["registers"][3], expected)
                self.assertEqual(state["registers"][0], 0)

    def test_execute_arithmetic_right_shift_sign_extends(self):
        state = codec.execute([codec.encode("ADDI x1, x0, -8"),
                               codec.encode("SRAI x3, x1, 1"),
                               codec.encode("EBREAK")])
        self.assertEqual(state["registers"][3], 0xFFFFFFFC)

    def test_execute_load_store_signed_and_unsigned_byte(self):
        program = [
            codec.encode("ADDI x1, x0, 128"),
            codec.encode("ADDI x2, x0, -1"),
            codec.encode("SW x2, 0(x1)"),
            codec.encode("LW x3, 0(x1)"),
            codec.encode("SB x2, 4(x1)"),
            codec.encode("LB x4, 4(x1)"),
            codec.encode("LBU x5, 4(x1)"),
            codec.encode("EBREAK"),
        ]
        state = codec.execute(program)
        self.assertEqual(state["registers"][3], 0xFFFFFFFF)
        self.assertEqual(state["registers"][4], 0xFFFFFFFF)
        self.assertEqual(state["registers"][5], 255)

    def test_execute_taken_and_untaken_branches(self):
        taken = ("BEQ x1, x1, 8", "BNE x1, x2, 8", "BLT x2, x1, 8",
                 "BGE x1, x2, 8", "BLTU x2, x1, 8", "BGEU x1, x2, 8")
        for asm in taken:
            with self.subTest(asm=asm):
                state = codec.execute([codec.encode("ADDI x1, x0, 5"),
                                       codec.encode("ADDI x2, x0, 3"),
                                       codec.encode(asm),
                                       codec.encode("ADDI x3, x0, 1"),
                                       codec.encode("ADDI x3, x0, 2"),
                                       codec.encode("EBREAK")])
                self.assertEqual(state["registers"][3], 2)
        state = codec.execute([codec.encode("ADDI x1, x0, 5"),
                               codec.encode("ADDI x2, x0, 3"),
                               codec.encode("BEQ x1, x2, 8"),
                               codec.encode("ADDI x3, x0, 1"),
                               codec.encode("EBREAK")])
        self.assertEqual(state["registers"][3], 1)

    def test_execute_jumps_and_upper_immediates(self):
        state = codec.execute([codec.encode("LUI x1, 0x12345"),
                               codec.encode("AUIPC x2, 0"),
                               codec.encode("JAL x3, 8"),
                               codec.encode("ADDI x4, x0, 1"),
                               codec.encode("ADDI x4, x0, 2"),
                               codec.encode("EBREAK")])
        self.assertEqual(state["registers"][1], 0x12345000)
        self.assertEqual(state["registers"][2], 4)
        self.assertEqual(state["registers"][3], 12)
        self.assertEqual(state["registers"][4], 2)
        state = codec.execute([codec.encode("ADDI x2, x0, 8"),
                               codec.encode("ADDI x3, x0, 7"),
                               codec.encode("JALR x1, 4(x2)"),
                               codec.encode("EBREAK")])
        self.assertEqual(state["registers"][1], 12)
        self.assertEqual(state["registers"][3], 7)

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
