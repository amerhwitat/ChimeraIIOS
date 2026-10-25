import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "validate_build_log", ROOT / "tools" / "validate_build_log.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BuildValidationLogTests(unittest.TestCase):
    def test_accepts_complete_successful_records_and_noise(self):
        log = """build started
[VALIDATION RUN] command=python3 validate_elf.py kernel.elf
validator output
[VALIDATION PASS] exit=0 command=python3 validate_elf.py kernel.elf
[VALIDATION RUN] command=python3 validate_pe.py BOOTX64.EFI
[VALIDATION PASS] exit=0 command=python3 validate_pe.py BOOTX64.EFI
"""
        result = MODULE.parse_validation_log(log, ("kernel.elf", "BOOTX64.EFI"))
        self.assertEqual(result["records"], 4)
        self.assertEqual(len(result["passed"]), 2)

    def test_rejects_empty_log(self):
        with self.assertRaisesRegex(MODULE.LogValidationError, "no validation records"):
            MODULE.parse_validation_log("builder output only\n")

    def test_rejects_missing_result(self):
        with self.assertRaisesRegex(MODULE.LogValidationError, "missing result"):
            MODULE.parse_validation_log(
                "[VALIDATION RUN] command=validator kernel.elf\n"
            )

    def test_rejects_orphan_result(self):
        with self.assertRaisesRegex(MODULE.LogValidationError, "orphan"):
            MODULE.parse_validation_log(
                "[VALIDATION PASS] exit=0 command=validator kernel.elf\n"
            )

    def test_rejects_malformed_validation_record(self):
        with self.assertRaisesRegex(MODULE.LogValidationError, "malformed"):
            MODULE.parse_validation_log("[VALIDATION PASS] command=validator\n")

    def test_rejects_duplicate_run_before_result(self):
        with self.assertRaisesRegex(MODULE.LogValidationError, "duplicate RUN"):
            MODULE.parse_validation_log(
                "[VALIDATION RUN] command=validator kernel.elf\n"
                "[VALIDATION RUN] command=validator kernel.elf\n"
            )

    def test_rejects_fail_even_when_other_record_passes(self):
        with self.assertRaisesRegex(MODULE.LogValidationError, "exited 7"):
            MODULE.parse_validation_log(
                "[VALIDATION RUN] command=validator kernel.elf\n"
                "[VALIDATION PASS] exit=0 command=validator kernel.elf\n"
                "[VALIDATION RUN] command=validator staged.elf\n"
                "[VALIDATION FAIL] exit=7 command=validator staged.elf\n"
            )

    def test_rejects_pass_with_nonzero_exit(self):
        with self.assertRaisesRegex(MODULE.LogValidationError, "PASS requires exit=0"):
            MODULE.parse_validation_log(
                "[VALIDATION RUN] command=validator kernel.elf\n"
                "[VALIDATION PASS] exit=2 command=validator kernel.elf\n"
            )

    def test_rejects_fail_with_zero_exit(self):
        with self.assertRaisesRegex(MODULE.LogValidationError, "FAIL requires nonzero"):
            MODULE.parse_validation_log(
                "[VALIDATION RUN] command=validator kernel.elf\n"
                "[VALIDATION FAIL] exit=0 command=validator kernel.elf\n"
            )

    def test_rejects_missing_required_successful_artifact(self):
        with self.assertRaisesRegex(MODULE.LogValidationError, "required successful"):
            MODULE.parse_validation_log(
                "[VALIDATION RUN] command=validator kernel.elf\n"
                "[VALIDATION PASS] exit=0 command=validator kernel.elf\n",
                ("BOOTX64.EFI",),
            )


if __name__ == "__main__":
    unittest.main()
