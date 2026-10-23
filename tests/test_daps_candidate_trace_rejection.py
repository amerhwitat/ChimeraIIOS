"""Regression test: candidate-only logs must never pass production closeout."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DAPS_PATH = ROOT / "tools" / "production-closeout-daps.py"
SPEC = importlib.util.spec_from_file_location("production_closeout_daps", DAPS_PATH)
assert SPEC is not None and SPEC.loader is not None
DAPS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DAPS)


class CandidateTraceRejectionTests(unittest.TestCase):
    def test_candidate_smoke_trace_is_rejected_even_if_report_claims_production(self):
        cases = {}
        for target in ("live", "installer", "recovery"):
            for firmware in ("bios", "uefi"):
                case_id = f"{target}-{firmware}"
                cases[case_id] = {
                    "status": "PASS",
                    "production_iso": "production.iso",
                    "iso_sha256": "a" * 64,
                    "raw_trace": f"traces/{case_id}-candidate-smoke.log",
                    "candidate_trace_is_production_evidence": True,
                }
        report = {
            "production_iso_sha256": "a" * 64,
            "candidate_smoke_substituted": False,
            "cases": cases,
        }

        errors = DAPS.check_evidence(report)
        self.assertTrue(any(
            "candidate smoke trace is not production acceptance evidence" in error
            for error in errors
        ))


if __name__ == "__main__":
    unittest.main()
