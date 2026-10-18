import unittest
from pathlib import Path
from tools.boot.assert_production_runtime import validate_log

class ProductionRuntimeAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.live = """KORONOS READY
CHM_TARGET_SELECTED target=live
USERSPACE READY: init pid=4
USERSPACE IO READY
LIVE READY
AURORA READY
SMP READY cpus=2
"""
    def test_live_requires_ordered_userspace_and_aurora_markers(self):
        self.assertEqual(validate_log(self.live, "live"), [])
    def test_kernel_banner_alone_does_not_pass(self):
        errors = validate_log("KORONOS READY\nRuntime supervisor alive; awaiting a supported userspace handoff\n", "live")
        self.assertTrue(any("stall/failure" in error for error in errors))
        self.assertTrue(any("userspace-originated" in error for error in errors))
        self.assertTrue(any("Aurora-ready" in error for error in errors))
    def test_wrong_target_marker_fails(self):
        log = self.live.replace("target=live", "target=installer").replace("LIVE READY", "INSTALLER READY")
        self.assertTrue(any("live target-selection" in error for error in validate_log(log, "live")))
    def test_installer_requires_installer_ready(self):
        log = """KORONOS READY
CHM_TARGET_SELECTED target=installer
USERSPACE READY: init pid=5
USERSPACE IO READY
INSTALLER READY
"""
        self.assertEqual(validate_log(log, "installer"), [])
    def test_smp_gate_rejects_single_cpu(self):
        log = self.live.replace("cpus=2", "cpus=1")
        self.assertTrue(any("at least two CPUs" in error for error in validate_log(log, "live", True)))
    def test_grub_installer_routes_to_installer_menu_and_mobile_fails_closed(self):
        grub = Path("boot/iso/grub.cfg").read_text(encoding="utf-8")
        install = grub.split('--id install {', 1)[1].split('\n}', 1)[0]
        self.assertIn("configfile /boot/jasper/install.cfg", install)
        self.assertNotIn("chimera-live-initramfs.img", install)
        mobile = grub.split('--id mobile {', 1)[1].split('\n}', 1)[0]
        self.assertIn("not available in this x86_64 ISO", mobile)
        self.assertNotIn("multiboot2", mobile)
        self.assertNotIn("100% path ready", grub)

if __name__ == "__main__":
    unittest.main()
