import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name("chimera-hypervisor.py")
SPEC = importlib.util.spec_from_file_location("chimera_hypervisor", MODULE)
hv = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hv)


class HypervisorTests(unittest.TestCase):
    def setUp(self):
        self.registry = {
            "schema": "CHM-HYPERVISOR-BACKENDS-1",
            "backends": [
                {"id": "x86", "family": "x86-64", "binary": "qemu-system-x86_64",
                 "accelerators": ["kvm", "tcg"], "enabled": True},
                {"id": "riscv32", "family": "RV32", "binary": "qemu-system-riscv32",
                 "accelerators": ["tcg"], "enabled": True},
                {"id": "nbit", "family": "Chimera N-bit", "binary": None,
                 "accelerators": [], "enabled": False, "reason": "not implemented"}
            ]
        }
        self.which = lambda name: "/usr/bin/" + name

    def test_auto_selects_kvm_when_available(self):
        args = hv.build_command("x86", registry=self.registry, which=self.which,
                                 kvm_path=Path("/dev/null"))
        self.assertIn("kvm", args)

    def test_auto_uses_tcg_when_kvm_missing(self):
        args = hv.build_command("x86", registry=self.registry, which=self.which,
                                 kvm_path=Path("/definitely/missing"))
        self.assertIn("tcg", args)

    def test_rv32_tcg_backend(self):
        args = hv.build_command("riscv32", registry=self.registry, which=self.which,
                                 kvm_path=Path("/dev/null"))
        self.assertIn("tcg", args)

    def test_rejects_unimplemented_native_architecture(self):
        with self.assertRaisesRegex(ValueError, "not implemented"):
            hv.build_command("nbit", registry=self.registry, which=self.which)

    def test_rejects_unknown_backend(self):
        with self.assertRaisesRegex(ValueError, "unknown backend"):
            hv.build_command("made-up", registry=self.registry, which=self.which)

    def test_rejects_unsupported_accelerator(self):
        with self.assertRaisesRegex(RuntimeError, "KVM unavailable"):
            hv.build_command("riscv32", accelerator="kvm", registry=self.registry,
                             which=self.which, kvm_path=Path("/dev/null"))

    def test_command_is_argument_vector_not_shell(self):
        args = hv.build_command("x86", registry=self.registry, which=self.which,
                                kvm_path=Path("/definitely/missing"))
        self.assertIsInstance(args, list)
        self.assertNotIn("shell", args)

    def test_memory_limit_rejects_oversized_request(self):
        with self.assertRaisesRegex(ValueError, "memory must be"):
            hv.build_command("x86", memory="4096M", registry=self.registry,
                             which=self.which, kvm_path=Path("/definitely/missing"))

    def test_profile_applies_machine_cpu_and_devices(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"profiles.json"
            path.write_text(json.dumps({"profiles":[{"id":"test-profile","backend":"x86","machine":"q35","cpu":"max","devices":["virtio-net-pci"],"firmware":None}]}))
            args=hv.build_command("x86", registry=self.registry, which=self.which,
                                  kvm_path=Path("/definitely/missing"),
                                  profile="test-profile", profiles_path=path, vcpus=2)
            self.assertIn("q35",args); self.assertIn("max",args)
            self.assertIn("virtio-net-pci",args); self.assertIn("2",args)

    def test_registry_has_unique_ids_and_native_nbit_gated(self):
        ids = [b["id"] for b in self.registry["backends"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertFalse(next(b for b in self.registry["backends"] if b["id"] == "nbit")["enabled"])


if __name__ == "__main__":
    unittest.main()
