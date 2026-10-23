#!/usr/bin/env python3
"""Regression tests for the fail-closed production acceptance evidence gate."""
from __future__ import annotations

import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GATE = runpy.run_path(str(ROOT / "tools" / "production-closeout-daps.py"), run_name="daps_test_module")
check_evidence = GATE["check_evidence"]


def valid_evidence():
    cases = {}
    for target in ("live", "installer", "recovery"):
        for firmware in ("bios", "uefi"):
            case_id = f"{target}-{firmware}"
            case = {
                "status": "PASS",
                "display_mode_verified": True,
                "display_mode": "1024x768",
                "display_mode_evidence": f"traces/{case_id}-display.log",
                "production_iso": f"koronos-{case_id}.iso",
                "iso_sha256": "a" * 64,
                "raw_trace": f"traces/{case_id}.log",
                "cpl3_syscall_ack": True,
                "process_visible_rootfs": True,
                "rootfs_file_syscalls_verified": True,
                "rootfs_file_syscalls_evidence": f"traces/{case_id}-vfs.log",
                "syscall_pid": 7,
                "readiness_pid": 7,
            }
            if target in ("live", "recovery"):
                case["tmpfs_mutation_verified"] = True
                case["tmpfs_mutation_evidence"] = f"traces/{case_id}-tmpfs.log"
            cases[case_id] = case
    return {
        "production_iso_sha256": "a" * 64,
        "cases": cases,
        "display": {
            "status": "PASS",
            "framebuffer_detected_verified": True,
            "highest_supported_mode_verified": True,
            "fallback_1024x768_verified": True,
            "fallback_640x480_verified": True,
            "aurora_compositor_handoff_verified": True,
            "selected_mode": "1920x1080",
            "evidence": "traces/display-modes.log",
        },
        "aurora_handoff": {"status": "PASS", "evidence": "traces/aurora.log"},
        "installer_persistence": {
            "status": "PASS", "write_verified": True, "cold_reboot_verified": True,
            "readback_verified": True, "evidence": "traces/installer-persistence.log",
        },
        "recovery_repair": {
            "status": "PASS", "repair_verified": True, "postcondition_verified": True,
            "evidence": "traces/recovery-repair.log",
        },
        "smp": {
            "status": "PASS", "ap_startup_verified": True,
            "overlapping_execution_verified": True, "cpu_ids": [0, 1],
            "evidence": "traces/smp-overlap.log",
        },
        "candidate_smoke_substituted": False,
    }


class ProductionCloseoutDapsTest(unittest.TestCase):
    def test_complete_evidence_passes(self):
        self.assertEqual(check_evidence(valid_evidence()), [])

    def test_missing_top_level_iso_digest_blocks_closeout(self):
        data = valid_evidence()
        data.pop("production_iso_sha256")
        errors = check_evidence(data)
        self.assertTrue(any("production_iso_sha256 must be a required" in e for e in errors))
        self.assertTrue(any("cannot bind case ISO to a missing/invalid top-level" in e for e in errors))

    def test_live_and_recovery_require_mutation_trace(self):
        data = valid_evidence()
        for case_id in ("live-bios", "live-uefi", "recovery-bios", "recovery-uefi"):
            data["cases"][case_id].pop("tmpfs_mutation_verified")
            data["cases"][case_id].pop("tmpfs_mutation_evidence")
        errors = check_evidence(data)
        self.assertEqual(sum("writable tmpfs create/write/read/truncate was not verified" in e for e in errors), 4)
        self.assertEqual(sum("missing raw evidence for writable tmpfs operations" in e for e in errors), 4)

    def test_pointer_only_rootfs_does_not_pass(self):
        data = valid_evidence()
        data["cases"]["live-bios"]["rootfs_file_syscalls_verified"] = False
        data["cases"]["live-bios"]["rootfs_file_syscalls_evidence"] = ""
        errors = check_evidence(data)
        self.assertTrue(any("OPEN/READ/CLOSE was not verified" in e for e in errors))
        self.assertTrue(any("missing raw evidence for rootfs OPEN/READ/CLOSE" in e for e in errors))

    def test_missing_display_evidence_blocks_closeout(self):
        data = valid_evidence()
        data.pop("display")
        data["cases"]["live-bios"].pop("display_mode_evidence")
        errors = check_evidence(data)
        self.assertTrue(any("display: missing evidence object" in e for e in errors))
        self.assertTrue(any("missing raw framebuffer/display evidence" in e for e in errors))

    def test_cli_artifact_validation_rejects_missing_files(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            errors = GATE["check_evidence"](valid_evidence(), Path(tmp))
        self.assertTrue(any("production_iso: artifact file does not exist" in e for e in errors))
        self.assertTrue(any("raw_trace: artifact file does not exist" in e for e in errors))

    def test_iso_sha256_is_checked_without_loading_whole_file(self):
        import tempfile
        import hashlib
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            iso = root / "koronos-live-bios.iso"
            iso.write_bytes(b"sample-iso-payload")
            data = valid_evidence()
            data["cases"]["live-bios"]["production_iso"] = iso.name
            data["cases"]["live-bios"]["iso_sha256"] = hashlib.sha256(b"wrong-payload").hexdigest()
            errors = GATE["check_evidence"](data, root)
        self.assertTrue(any("live-bios: production_iso: SHA-256 does not match artifact contents" in e for e in errors))

    def test_artifact_path_traversal_is_rejected(self):
        import tempfile
        from pathlib import Path
        data = valid_evidence()
        data["cases"]["live-bios"]["raw_trace"] = "../outside.log"
        with tempfile.TemporaryDirectory() as tmp:
            errors = GATE["check_evidence"](data, Path(tmp))
        self.assertTrue(any("artifact path escapes the evidence directory" in e for e in errors))

    def test_claimed_readiness_must_exist_in_raw_trace(self):
        import tempfile
        from pathlib import Path
        data = valid_evidence()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "traces" / "live-bios.log"
            trace.parent.mkdir()
            trace.write_text("[KRN ] KORONOS READY\\nUSERSPACE READY: target=live init_pid=7\\n", encoding="utf-8")
            data["cases"]["live-bios"]["raw_trace"] = "traces/live-bios.log"
            errors = GATE["check_evidence"](data, root)
        self.assertTrue(any("trace is missing required runtime marker 'USER INIT SYSCALL:'" in e for e in errors))
        self.assertTrue(any("raw_trace lacks a target-matched user-originated syscall" in e for e in errors))

    def test_raw_trace_rejects_mismatched_target_or_pid(self):
        import tempfile
        from pathlib import Path
        data = valid_evidence()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "traces" / "live-bios.log"
            trace.parent.mkdir()
            trace.write_text(
                "[KRN ] KORONOS READY\\n"
                "USER INIT SYSCALL: target=live init_pid=7\\n"
                "USERSPACE TARGET READY: live component=aurora-session init pid=8\\n",
                encoding="utf-8",
            )
            data["cases"]["live-bios"]["raw_trace"] = "traces/live-bios.log"
            errors = GATE["check_evidence"](data, root)
        self.assertTrue(any("raw_trace syscall/readiness PIDs do not match" in e for e in errors))

    def test_accepts_real_production_target_ready_marker(self):
        import tempfile
        from pathlib import Path
        data = valid_evidence()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "traces" / "live-bios.log"
            trace.parent.mkdir()
            trace.write_text(
                "[KRN ] KORONOS READY\\n"
                "USER INIT SYSCALL: target=live init_pid=7\\n"
                "USERSPACE TARGET READY: live component=aurora-session init pid=7\\n",
                encoding="utf-8",
            )
            data["cases"]["live-bios"]["raw_trace"] = "traces/live-bios.log"
            errors = GATE["check_evidence"](data, root)
        self.assertFalse(any("raw_trace lacks a target-matched userspace readiness marker" in e for e in errors))
        self.assertFalse(any("raw_trace syscall/readiness PIDs do not match" in e for e in errors))

    def test_legacy_probe_marker_cannot_satisfy_production_closeout(self):
        import tempfile
        from pathlib import Path
        data = valid_evidence()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "traces" / "live-bios.log"
            trace.parent.mkdir()
            trace.write_text(
                "[KRN ] KORONOS READY\\n"
                "USER INIT SYSCALL: target=live init_pid=7\\n"
                "USERSPACE READY: target=live init_pid=7\\n",
                encoding="utf-8",
            )
            data["cases"]["live-bios"]["raw_trace"] = "traces/live-bios.log"
            errors = GATE["check_evidence"](data, root)
        self.assertTrue(any("raw_trace lacks a target-matched userspace readiness marker" in e for e in errors))

    def test_rejects_production_ready_marker_for_wrong_component(self):
        import tempfile
        from pathlib import Path
        data = valid_evidence()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "traces" / "live-bios.log"
            trace.parent.mkdir()
            trace.write_text(
                "[KRN ] KORONOS READY\\n"
                "USER INIT SYSCALL: target=live init_pid=7\\n"
                "USERSPACE TARGET READY: live component=recovery-runtime init pid=7\\n",
                encoding="utf-8",
            )
            data["cases"]["live-bios"]["raw_trace"] = "traces/live-bios.log"
            errors = GATE["check_evidence"](data, root)
        self.assertTrue(any("raw_trace lacks a target-matched userspace readiness marker" in e for e in errors))

    def test_candidate_smoke_cannot_replace_production(self):
        data = valid_evidence()
        data["candidate_smoke_substituted"] = True
        self.assertTrue(any("candidate smoke evidence cannot substitute" in e for e in check_evidence(data)))


if __name__ == "__main__":
    unittest.main()
