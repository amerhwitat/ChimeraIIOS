#!/usr/bin/env python3
"""Tests for fail-closed production evidence collection."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "collect-production-closeout-evidence.py"
SPEC = importlib.util.spec_from_file_location("closeout_collector", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class CollectorTests(unittest.TestCase):
    def test_collects_hash_and_six_not_run_cases_without_promoting_smoke(self):
        import hashlib
        import json
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "out"
            traces = root / "candidate-traces"
            traces.mkdir()
            iso = output / "chimera-ii-os.iso"
            output.mkdir()
            iso.write_bytes(b"test production iso bytes")
            (traces / "live-debugcon.log").write_text(
                "[KRN ] KORONOS READY\nUSER INIT SYSCALL: target=live init_pid=7\n",
                encoding="utf-8")
            data = MODULE.collect(iso, output, traces)
            report = json.loads((output / "production-closeout-evidence.json").read_text())
            self.assertEqual(len(report["cases"]), 6)
            self.assertEqual(data["production_iso_sha256"], hashlib.sha256(iso.read_bytes()).hexdigest())
            self.assertTrue(report["candidate_smoke_substituted"])
            self.assertTrue(all(c["status"] == "NOT RUN" for c in report["cases"].values()))
            # A candidate smoke log may contain the syscall marker, but it is not production evidence.
            self.assertTrue(any(c["cpl3_syscall_ack"] for c in report["cases"].values()))
            self.assertFalse(any(c["candidate_trace_is_production_evidence"] for c in report["cases"].values()))
            self.assertEqual(report["cases"]["live-bios"]["raw_trace"], "closeout-traces/live-bios-candidate-smoke.log")
            self.assertFalse(report["cases"]["live-bios"]["candidate_trace_is_production_evidence"])
            self.assertEqual(report["smp"]["status"], "NOT RUN")
            self.assertFalse(report["installer_persistence"]["cold_reboot_verified"])

    def test_binds_actual_matrix_traces_to_same_iso_without_claiming_missing_gates(self):
        import hashlib
        import json
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "out"
            output.mkdir()
            traces = root / "candidate-traces"
            traces.mkdir()
            iso = output / "chimera-ii-os.iso"
            iso.write_bytes(b"immutable production iso fixture")
            digest = hashlib.sha256(iso.read_bytes()).hexdigest()
            matrix = output / "production-qemu-matrix"
            cases = []
            components = {"live": "aurora-session", "installer": "install-executor", "recovery": "recovery-runtime"}
            for target in ("live", "installer", "recovery"):
                for firmware in ("bios", "uefi"):
                    case_id = f"{target}-{firmware}"
                    case_dir = matrix / case_id
                    case_dir.mkdir(parents=True)
                    mount = (f"USERSPACE ROOTFS MOUNTED: target={target} root=read-only tmpfs=/tmp"
                             if target in ("live", "recovery")
                             else "USERSPACE INSTALLER STORAGE ROOT MOUNTED: target=installer")
                    trace = (
                        f"PRODUCTION ISO SHA-256: {digest}\\n"
                        f"[KRN ] KORONOS READY\\nUSER INIT SYSCALL: target={target} init_pid=7\\n"
                        f"NATIVE INIT PID: target={target} pid=7\\n{mount}\\n"
                        "NATIVE INIT VFS SELFTEST PASS\\n"
                        "USERSPACE ROOTFS FILE SELFTEST PASS: /etc/os-release OPEN READ CLOSE\\n"
                        "USERSPACE TMPFS MUTATION PASS: CREATE WRITE READ TRUNCATE\\n"
                        f"USERSPACE TARGET READY: {target} component={components[target]} init pid=7\\n"
                    )
                    (case_dir / "raw-trace.log").write_text(trace, encoding="utf-8")
                    cases.append({"case": case_id, "status": "BLOCKED", "qemu_started": True, "trace": f"{case_id}/raw-trace.log"})
            (matrix / "matrix-report.json").write_text(json.dumps({
                "schema": "CHM-PRODUCTION-ISO-QEMU-MATRIX-1",
                "iso_sha256": digest,
                "iso_sha256_after": digest,
                "cases": cases,
                "target_boot_matrix": "BLOCKED",
                "production_acceptance": "NOT ESTABLISHED BY THIS MATRIX",
            }), encoding="utf-8")
            data = MODULE.collect(iso, output, traces, matrix)
            report = json.loads((output / "production-closeout-evidence.json").read_text())
        self.assertFalse(report["candidate_smoke_substituted"])
        self.assertEqual(report["production_iso_sha256"], digest)
        self.assertTrue(all(case["candidate_trace_is_production_evidence"] for case in report["cases"].values()))
        self.assertTrue(all(case["raw_trace"].endswith("-production-iso.log") for case in report["cases"].values()))
        self.assertTrue(all(case["status"] == "BLOCKED" for case in report["cases"].values()))
        self.assertFalse(report["installer_persistence"]["cold_reboot_verified"])
        self.assertIn("independent display", report["collection_note"].lower())

    def test_requires_iso_next_to_report_for_hash_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            iso = root / "iso" / "production.iso"
            iso.parent.mkdir()
            iso.write_bytes(b"iso")
            with self.assertRaisesRegex(ValueError, "ISO must reside beside"):
                MODULE.collect(iso, root / "evidence", root / "traces")

    def test_collected_candidate_report_is_rejected_by_production_daps(self):
        import runpy
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            iso = root / "chimera-ii-os.iso"
            iso.write_bytes(b"test production iso bytes")
            data = MODULE.collect(iso, root, root / "no-candidate-traces")
            daps = runpy.run_path(str(ROOT / "tools" / "production-closeout-daps.py"), run_name="daps_test_module")
            errors = daps["check_evidence"](data)
        self.assertTrue(any("status must be PASS, got 'NOT RUN'" in error for error in errors))
        self.assertTrue(any("candidate smoke evidence cannot substitute" in error for error in errors))
        self.assertTrue(any("smp: status must be PASS" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
