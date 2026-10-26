import contextlib
import importlib.util
import io
import pathlib
import tempfile
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

    def test_accepts_complete_final_record_without_trailing_newline(self):
        log = (
            "[VALIDATION RUN] command=validator kernel.elf\n"
            "[VALIDATION PASS] exit=0 command=validator kernel.elf"
        )
        result = MODULE.parse_validation_log(log, ("kernel.elf",))
        self.assertEqual(result["passed"], ["validator kernel.elf"])

    def test_accepts_crlf_records(self):
        log = (
            "[VALIDATION RUN] command=validator kernel.elf\r\n"
            "[VALIDATION PASS] exit=0 command=validator kernel.elf\r\n"
        )
        self.assertEqual(MODULE.parse_validation_log(log)["records"], 2)

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

    def test_rejects_truncated_validation_prefix(self):
        for line in ("[VALIDATION", "[VALIDATION RUN]", "[VALIDATION PASS]"):
            with self.subTest(line=line):
                with self.assertRaisesRegex(MODULE.LogValidationError, "malformed"):
                    MODULE.parse_validation_log(line)

    def test_rejects_truncated_result_at_end_of_log(self):
        with self.assertRaisesRegex(MODULE.LogValidationError, "malformed"):
            MODULE.parse_validation_log(
                "[VALIDATION RUN] command=validator kernel.elf\n"
                "[VALIDATION PASS] exit="
            )

    def test_rejects_result_for_different_command(self):
        with self.assertRaisesRegex(MODULE.LogValidationError, "orphan"):
            MODULE.parse_validation_log(
                "[VALIDATION RUN] command=validator kernel.elf\n"
                "[VALIDATION PASS] exit=0 command=validator other.elf\n"
            )

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

    def test_rejects_exit_code_outside_shell_status_range(self):
        for code in ("256", "999", "9" * 5000):
            with self.subTest(code_length=len(code)):
                with self.assertRaisesRegex(MODULE.LogValidationError, "exit code out of range"):
                    MODULE.parse_validation_log(
                        "[VALIDATION RUN] command=validator kernel.elf\n"
                        f"[VALIDATION FAIL] exit={code} command=validator kernel.elf\n"
                    )

    def test_cli_fails_closed_on_invalid_utf8_bytes(self):
        with tempfile.NamedTemporaryFile() as log_file:
            log_file.write(b"[VALIDATION RUN] command=validator\xff\n")
            log_file.flush()
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                result = MODULE.main([log_file.name])
        self.assertEqual(result, 1)
        self.assertIn("[VALIDATION LOG FAIL]", stderr.getvalue())

    def test_rejects_missing_required_successful_artifact(self):
        with self.assertRaisesRegex(MODULE.LogValidationError, "required successful"):
            MODULE.parse_validation_log(
                "[VALIDATION RUN] command=validator kernel.elf\n"
                "[VALIDATION PASS] exit=0 command=validator kernel.elf\n",
                ("BOOTX64.EFI",),
            )


if __name__ == "__main__":
    unittest.main()
