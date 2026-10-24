#!/usr/bin/env python3
"""Regression tests for the fail-closed production DAPS evidence contract."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import production_acceptance_gate as gate


def live_evidence() -> dict:
    return {
        "target": "live",
        "firmware": "bios",
        "iso_sha256": "a" * 64,
        "ring3_init_syscall_ack": True,
        "syscall_ack_origin": "ring3-user-init",
        "userspace_pid": 1,
        "userspace_pid_origin": "kernel-owned-process-table",
        "kernel_emitted_readiness_marker": False,
        "candidate_probe_only": False,
        "target_service_health": True,
        "service_manager_pid": 1,
        "service_manager_pid_origin": "kernel-owned-process-table",
        "service_manager_state": "running",
        "service_manager_address_space_owned": True,
        "service_health_origin": "userspace-service-manager",
        "filesystem_rw_probe": True,
        "filesystem_rw_probe_origin": "ring3-user-process",
        "mounts": ["/proc", "/sys", "/dev", "/run", "/tmp"],
        "services": {
            "device-manager": "healthy",
            "filesystem": "healthy",
            "network": "healthy",
            "logging": "healthy",
            "process-supervisor": "healthy",
            "session-manager": "healthy",
        },
        "aurora_native_session": True,
    }


class ProductionAcceptanceGateTests(unittest.TestCase):
    def check(self, evidence: dict) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "live-bios.json"
            path.write_text(json.dumps(evidence), encoding="utf-8")
            gate.check_case(path, "live", "bios", "a" * 64)

    def test_complete_persistent_service_evidence_passes_case_contract(self) -> None:
        self.check(live_evidence())

    def test_missing_service_manager_lifecycle_is_rejected(self) -> None:
        evidence = live_evidence()
        evidence.pop("service_manager_state")
        with self.assertRaisesRegex(gate.GateError, "remain running"):
            self.check(evidence)

    def test_filesystem_probe_must_originate_in_ring3(self) -> None:
        evidence = live_evidence()
        evidence["filesystem_rw_probe_origin"] = "kernel"
        with self.assertRaisesRegex(gate.GateError, "did not originate"):
            self.check(evidence)

    def test_service_health_must_come_from_userspace_manager(self) -> None:
        evidence = live_evidence()
        evidence["service_health_origin"] = "kernel"
        with self.assertRaisesRegex(gate.GateError, "not reported by the userspace"):
            self.check(evidence)


if __name__ == "__main__":
    unittest.main(verbosity=2)
