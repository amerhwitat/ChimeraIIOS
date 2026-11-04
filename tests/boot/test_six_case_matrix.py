import hashlib, json, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/boot/verify-six-case-matrix.py"

def trace_for(target, firmware):
    return "\n".join([
        "[KRN ] KORONOS READY", f"BOOT FIRMWARE: {firmware.upper()}",
        f"USER INIT SYSCALL: target={target} init_pid=42",
        f"VFS ACCEPTANCE: ROOT MOUNTED target={target} path=/",
        f"VFS ACCEPTANCE: TMP WRITE-READ VERIFIED target={target} path=/tmp",
        f"USERSPACE READY: target={target} init_pid=42",
        "SMP CPU ONLINE: logical_id=0 apic_id=0", "SMP CPU ONLINE: logical_id=1 apic_id=1",
        "SMP OVERLAP VERIFIED: cpu_a=0 cpu_b=1 overlap_ticks=12"]) + "\n"

class SixCaseMatrixTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.iso = self.root / "canonical.iso"; self.iso.write_bytes(b"immutable-canonical-iso-fixture")
        self.evidence = self.root / "evidence"; self.evidence.mkdir()
        digest = hashlib.sha256(self.iso.read_bytes()).hexdigest(); cases = []
        for target in ("live", "installer", "recovery"):
            for firmware in ("bios", "uefi"):
                trace_name = f"{target}-{firmware}.log"
                (self.evidence / trace_name).write_text(trace_for(target, firmware))
                case = {"target": target, "firmware": firmware, "iso_sha256": digest,
                        "trace": trace_name, "qemu_exit_code": 124}
                if target == "live":
                    desktops = {}
                    for profile in ("aurora", "marine"):
                        name = f"{target}-{firmware}-{profile}.log"
                        (self.evidence / name).write_text(f"DESKTOP READY: profile={profile} pid=90\n")
                        desktops[profile] = name
                    case["desktop_traces"] = desktops
                elif target == "installer":
                    name = f"{target}-{firmware}-persistence.log"
                    (self.evidence / name).write_text("INSTALLER WRITE COMMITTED: token=install-1\nINSTALLER COLD-BOOT PERSISTENCE VERIFIED: token=install-1\n")
                    case["postcondition_trace"] = name
                else:
                    name = f"{target}-{firmware}-repair.log"
                    (self.evidence / name).write_text("RECOVERY REPAIR STARTED: transaction=repair-1\nRECOVERY POSTCONDITION VERIFIED: transaction=repair-1\n")
                    case["postcondition_trace"] = name
                cases.append(case)
        self.manifest = {"schema": "koronos-six-case-evidence-v1", "iso_sha256": digest, "cases": cases}
        self.write_manifest()

    def tearDown(self): self.tmp.cleanup()
    def write_manifest(self): (self.evidence / "matrix.json").write_text(json.dumps(self.manifest, indent=2))
    def run_verifier(self):
        return subprocess.run([sys.executable, str(SCRIPT), "--iso", str(self.iso), "--evidence-dir", str(self.evidence)], capture_output=True, text=True)

    def test_complete_six_case_evidence_passes(self):
        result = self.run_verifier(); self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"status": "PASS"', result.stdout)
    def test_missing_firmware_case_is_blocked(self):
        self.manifest["cases"].pop(); self.write_manifest(); self.assertEqual(self.run_verifier().returncode, 1)
    def test_mismatched_iso_hash_is_blocked(self):
        self.manifest["cases"][0]["iso_sha256"] = "0" * 64; self.write_manifest()
        self.assertEqual(self.run_verifier().returncode, 1)
    def test_pid_mismatch_is_blocked(self):
        p = self.evidence / self.manifest["cases"][0]["trace"]
        p.write_text(p.read_text().replace("init_pid=42", "init_pid=43", 1))
        self.assertEqual(self.run_verifier().returncode, 1)
    def test_exit_78_is_blocked(self):
        p = self.evidence / self.manifest["cases"][0]["trace"]; p.write_text(p.read_text() + "NATIVE INIT BLOCKED: exit=78\n")
        self.assertEqual(self.run_verifier().returncode, 1)
    def test_missing_smp_overlap_is_blocked(self):
        p = self.evidence / self.manifest["cases"][0]["trace"]
        p.write_text("\n".join(x for x in p.read_text().splitlines() if "SMP OVERLAP" not in x))
        self.assertEqual(self.run_verifier().returncode, 1)
    def test_installer_persistence_requires_same_token(self):
        c = next(x for x in self.manifest["cases"] if x["target"] == "installer")
        (self.evidence / c["postcondition_trace"]).write_text("INSTALLER WRITE COMMITTED: token=a\nINSTALLER COLD-BOOT PERSISTENCE VERIFIED: token=b\n")
        self.assertEqual(self.run_verifier().returncode, 1)
    def test_recovery_requires_matching_postcondition(self):
        c = next(x for x in self.manifest["cases"] if x["target"] == "recovery")
        (self.evidence / c["postcondition_trace"]).write_text("RECOVERY REPAIR STARTED: transaction=a\nRECOVERY POSTCONDITION VERIFIED: transaction=b\n")
        self.assertEqual(self.run_verifier().returncode, 1)

    def test_trace_path_cannot_escape_evidence_directory(self):
        self.manifest["cases"][0]["trace"] = "../outside.log"
        self.write_manifest()
        self.assertEqual(self.run_verifier().returncode, 1)

    def test_duplicate_case_is_blocked(self):
        self.manifest["cases"].append(dict(self.manifest["cases"][0]))
        self.write_manifest()
        self.assertEqual(self.run_verifier().returncode, 1)

    def test_non_object_manifest_is_blocked(self):
        (self.evidence / "matrix.json").write_text("[]")
        self.assertEqual(self.run_verifier().returncode, 1)

if __name__ == "__main__": unittest.main()
