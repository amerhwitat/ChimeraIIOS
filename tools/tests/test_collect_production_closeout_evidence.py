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
            self.assertFalse(any(c["cpl3_syscall_ack"] for c in report["cases"].values()))
            self.assertEqual(report["cases"]["live-bios"]["raw_trace"], "closeout-traces/live-bios-candidate-smoke.log")
            self.assertFalse(report["cases"]["live-bios"]["candidate_trace_is_production_evidence"])
            self.assertEqual(report["smp"]["status"], "NOT RUN")
            self.assertFalse(report["installer_persistence"]["cold_reboot_verified"])

    def test_requires_iso_next_to_report_for_hash_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            iso = root / "iso" / "production.iso"
            iso.parent.mkdir()
            iso.write_bytes(b"iso")
            with self.assertRaisesRegex(ValueError, "ISO must reside beside"):
                MODULE.collect(iso, root / "evidence", root / "traces")


if __name__ == "__main__":
    unittest.main()
