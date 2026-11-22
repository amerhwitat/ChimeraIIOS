import hashlib
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools" / "boot"))
from verify_production_release import AcceptanceError, SCHEMA, verify

DIGEST = "a" * 64
TRACE = "b" * 64


def valid_manifest():
    cases = []
    for target in ("live", "installer", "recovery"):
        for firmware in ("bios", "uefi"):
            cases.append({
                "target": target, "firmware": firmware, "iso_sha256": DIGEST,
                "firmware_trace_sha256": TRACE, "kernel_ready": True,
                "cpl3_init_ack": True, "matching_nonzero_pid1": True,
                "persistent_runtime": True, "target_postcondition": True,
            })
    groups = {
        "scheduler": ["preemptive_context_switching", "two_cpu_overlap"],
        "storage": ["block_device_io", "persistent_vfs"],
        "installed_root": ["validated_mount_and_handoff"],
        "installer": ["partition_format_and_persistent_install"],
        "recovery": ["filesystem_repair_postcondition"],
        "services": ["supervised_pid1"],
        "desktops": ["aurora_native_session", "marine_native_session",
                     "freexp_native_session", "freewin11_native_session"],
        "catalogues": ["all_command_providers_verified", "all_claimed_isa_backends_conformant"],
    }
    return {
        "schema": SCHEMA, "iso_sha256": DIGEST, "cases": cases,
        "system_gates": {group: {field: True for field in fields}
                         for group, fields in groups.items()},
        "evidence": [{"uri": "https://example.invalid/ci-trace", "sha256": TRACE}],
    }


class ProductionReleaseVerifierTests(unittest.TestCase):
    def test_accepts_complete_six_case_manifest(self):
        result = verify(valid_manifest())
        self.assertEqual(result["cases"], 6)

    def test_rejects_missing_firmware_case(self):
        manifest = valid_manifest()
        manifest["cases"].pop()
        with self.assertRaisesRegex(AcceptanceError, "exactly six"):
            verify(manifest)

    def test_rejects_mixed_iso_hashes(self):
        manifest = valid_manifest()
        manifest["cases"][0]["iso_sha256"] = TRACE
        with self.assertRaisesRegex(AcceptanceError, "differs"):
            verify(manifest)

    def test_rejects_probe_only_or_missing_pid1(self):
        manifest = valid_manifest()
        manifest["cases"][0]["matching_nonzero_pid1"] = False
        with self.assertRaisesRegex(AcceptanceError, "matching_nonzero_pid1"):
            verify(manifest)

    def test_rejects_unimplemented_scheduler_or_storage(self):
        for group, field in (("scheduler", "preemptive_context_switching"),
                             ("storage", "persistent_vfs"),
                             ("desktops", "aurora_native_session")):
            manifest = valid_manifest()
            manifest["system_gates"][group][field] = False
            with self.subTest(group=group, field=field):
                with self.assertRaises(AcceptanceError):
                    verify(manifest)

    def test_checks_actual_iso_digest(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as directory:
            iso = Path(directory) / "candidate.iso"
            iso.write_bytes(b"diagnostic candidate")
            manifest = valid_manifest()
            manifest["iso_sha256"] = hashlib.sha256(iso.read_bytes()).hexdigest()
            for case in manifest["cases"]:
                case["iso_sha256"] = manifest["iso_sha256"]
            self.assertEqual(verify(manifest, iso)["cases"], 6)
            iso.write_bytes(b"changed candidate")
            with self.assertRaisesRegex(AcceptanceError, "does not match"):
                verify(manifest, iso)


if __name__ == "__main__":
    unittest.main()
