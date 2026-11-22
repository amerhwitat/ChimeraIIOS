import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VERIFIER_PATH = REPO_ROOT / "tools" / "boot" / "verify-production-release.py"
SPEC = importlib.util.spec_from_file_location("verify_production_release", VERIFIER_PATH)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"cannot load production verifier: {VERIFIER_PATH}")
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)
AcceptanceError = VERIFIER.AcceptanceError
SCHEMA = VERIFIER.SCHEMA
verify = VERIFIER.verify

DIGEST = "a" * 64
TRACE = "b" * 64
EVIDENCE_BYTES = b"retained CI trace bytes for verifier unit test"


def valid_manifest(evidence_path: Path):
    evidence_path.write_bytes(EVIDENCE_BYTES)
    evidence_digest = hashlib.sha256(EVIDENCE_BYTES).hexdigest()
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
        "evidence": [{
            "uri": "https://github.com/example/project/actions/runs/123",
            "path": evidence_path.name, "sha256": evidence_digest,
        }],
    }


class ProductionReleaseVerifierTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.evidence = self.root / "ci-trace.log"
        self.manifest = valid_manifest(self.evidence)

    def tearDown(self):
        self.temp.cleanup()

    def test_accepts_complete_six_case_manifest_with_hashed_evidence(self):
        result = verify(self.manifest, evidence_root=self.root)
        self.assertEqual(result["cases"], 6)

    def test_rejects_missing_firmware_case(self):
        self.manifest["cases"].pop()
        with self.assertRaisesRegex(AcceptanceError, "exactly six"):
            verify(self.manifest, evidence_root=self.root)

    def test_rejects_mixed_iso_hashes(self):
        self.manifest["cases"][0]["iso_sha256"] = TRACE
        with self.assertRaisesRegex(AcceptanceError, "differs"):
            verify(self.manifest, evidence_root=self.root)

    def test_rejects_probe_only_or_missing_pid1(self):
        self.manifest["cases"][0]["matching_nonzero_pid1"] = False
        with self.assertRaisesRegex(AcceptanceError, "matching_nonzero_pid1"):
            verify(self.manifest, evidence_root=self.root)

    def test_rejects_unimplemented_scheduler_or_storage(self):
        for group, field in (("scheduler", "preemptive_context_switching"),
                             ("storage", "persistent_vfs"),
                             ("desktops", "aurora_native_session")):
            manifest = valid_manifest(self.evidence)
            manifest["system_gates"][group][field] = False
            with self.subTest(group=group, field=field):
                with self.assertRaises(AcceptanceError):
                    verify(manifest, evidence_root=self.root)

    def test_rejects_missing_evidence_artifact(self):
        self.evidence.unlink()
        with self.assertRaisesRegex(AcceptanceError, "evidence artifact is missing"):
            verify(self.manifest, evidence_root=self.root)

    def test_rejects_evidence_hash_mismatch(self):
        self.evidence.write_bytes(b"altered trace")
        with self.assertRaisesRegex(AcceptanceError, "SHA-256 does not match"):
            verify(self.manifest, evidence_root=self.root)

    def test_rejects_path_traversal(self):
        self.manifest["evidence"][0]["path"] = "../outside.log"
        with self.assertRaisesRegex(AcceptanceError, "cannot traverse"):
            verify(self.manifest, evidence_root=self.root)

    def test_checks_actual_iso_digest(self):
        iso = self.root / "candidate.iso"
        iso.write_bytes(b"diagnostic candidate")
        self.manifest["iso_sha256"] = hashlib.sha256(iso.read_bytes()).hexdigest()
        for case in self.manifest["cases"]:
            case["iso_sha256"] = self.manifest["iso_sha256"]
        self.assertEqual(verify(self.manifest, iso, self.root)["cases"], 6)
        iso.write_bytes(b"changed candidate")
        with self.assertRaisesRegex(AcceptanceError, "does not match"):
            verify(self.manifest, iso, self.root)


if __name__ == "__main__":
    unittest.main()
