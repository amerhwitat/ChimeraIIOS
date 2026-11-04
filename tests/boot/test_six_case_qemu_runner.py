import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[2] / "tools/boot/run-six-case-qemu.py"
SPEC = importlib.util.spec_from_file_location("six_case_qemu_runner", SCRIPT)
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class SixCaseQemuRunnerTests(unittest.TestCase):
    def test_main_menu_selection_is_stable(self):
        self.assertEqual(RUNNER.MAIN_MENU_INDEX, {
            "live": 0, "installer": 2, "recovery": 5
        })
        self.assertEqual(RUNNER.RECOVERY_MENU_INDEX, 0)

    def test_firmware_and_target_order(self):
        self.assertEqual(RUNNER.TARGETS, ("live", "installer", "recovery"))
        self.assertEqual(RUNNER.FIRMWARES, ("bios", "uefi"))

    def test_firmware_identity_is_passed_by_real_grub_handoff(self):
        root = SCRIPT.parents[2]
        main_grub = (root / "boot/iso/grub.cfg").read_text(encoding="utf-8")
        recovery_grub = (root / "boot/jasper/recovery.cfg").read_text(encoding="utf-8")
        kernel = (root / "kernel/core/target_launch.cpp").read_text(encoding="utf-8")
        self.assertIn("firmware=$grub_platform", main_grub)
        self.assertIn("firmware=$grub_platform", recovery_grub)
        self.assertIn('koronos_target_log("BOOT FIRMWARE: UEFI")', kernel)
        self.assertIn('koronos_target_log("BOOT FIRMWARE: BIOS")', kernel)

    def test_production_target_modules_are_built_into_canonical_boot_path(self):
        root = SCRIPT.parents[2]
        main_grub = (root / "boot/iso/grub.cfg").read_text(encoding="utf-8")
        for target in ("live", "installer", "recovery"):
            self.assertIn(f"/boot/targets/target-init-{target}.elf", main_grub)
        builder = (root / "iso/chimera-live-iso.sh").read_text(encoding="utf-8")
        self.assertIn("target-init-$target.elf", builder)
        self.assertIn('install -m 0644 "$artifact" "$STAGE/boot/targets/target-init-$target.elf"', builder)

    def test_runner_never_adds_acceptance_markers_to_raw_trace(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for marker in (
            "USER INIT SYSCALL:", "USERSPACE READY:", "VFS ACCEPTANCE:",
            "SMP CPU ONLINE:", "SMP OVERLAP VERIFIED:", "DESKTOP READY:",
            "INSTALLER COLD-BOOT PERSISTENCE VERIFIED:",
            "RECOVERY POSTCONDITION VERIFIED:",
        ):
            self.assertNotIn(marker, source)

    def test_case_binds_raw_trace_to_unchanged_iso(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            iso = root / "canonical.iso"
            iso.write_bytes(b"immutable-iso")
            evidence = root / "evidence"
            fake_qemu = root / "fake-qemu"
            fake_qemu.write_text(
                "#!/usr/bin/env python3\n"
                "import pathlib, sys\n"
                "for i, arg in enumerate(sys.argv[:-1]):\n"
                "    if arg == '-debugcon': pathlib.Path(sys.argv[i+1][5:]).write_text('raw qemu trace')\n"
                "    if arg == '-serial': pathlib.Path(sys.argv[i+1][5:]).write_text('raw serial trace')\n",
                encoding="utf-8",
            )
            fake_qemu.chmod(0o755)
            with patch.object(RUNNER, "select_grub_target", side_effect=RuntimeError("mock monitor")):
                result = RUNNER.run_case(iso, evidence, "live", "bios",
                                         str(fake_qemu), 5, None)
            self.assertEqual(result["iso_sha256"], RUNNER.sha256(iso))
            self.assertEqual(result["qemu_exit_code"], 0)
            self.assertIn("mock monitor", result["selection_error"])
            raw = (evidence / result["trace"]).read_text(encoding="utf-8")
            self.assertEqual(raw, "raw qemu trace")
            self.assertNotIn("USERSPACE READY", raw)


if __name__ == "__main__":
    unittest.main()
