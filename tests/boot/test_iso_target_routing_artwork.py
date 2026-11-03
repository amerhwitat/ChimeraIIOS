#!/usr/bin/env python3
"""Static regressions for GRUB2 -> Spit Fire -> Gates -> Jasper routing."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
GRUB = (ROOT / "boot/iso/grub.cfg").read_text()
SPITFIRE = (ROOT / "boot/spitfire/spitfire-menu.cfg").read_text()
GATES = (ROOT / "boot/gates/gates-menu.cfg").read_text()
JASPER = (ROOT / "boot/jasper/live-image.cfg").read_text()
INSTALL = (ROOT / "boot/jasper/install.cfg").read_text()
RECOVERY = (ROOT / "boot/jasper/recovery.cfg").read_text()
FULL_BUILDER = (ROOT / "tools/build-full-iso.sh").read_text()
LIVE_BUILDER = (ROOT / "iso/chimera-live-iso.sh").read_text()


class IsoTargetRoutingTests(unittest.TestCase):
    def test_firmware_grub_spitfire_gates_jasper_handoff_is_explicit(self):
        self.assertIn("configfile /boot/spitfire/spitfire-menu.cfg", GRUB)
        self.assertIn("configfile /boot/gates/gates-menu.cfg", SPITFIRE)
        self.assertIn("configfile /boot/jasper/live-image.cfg", GATES)
        self.assertIn("menuentry", JASPER)
        for config in (GRUB, SPITFIRE, GATES, JASPER):
            self.assertIn("gfxpayload=keep", config)

    def test_jasper_offers_linux_live_and_separate_linux_rescue(self):
        self.assertIn("--id live-linux", JASPER)
        self.assertIn("--id linux-rescue", JASPER)
        self.assertIn("chimera.mode=recovery", JASPER)
        self.assertIn("/live/vmlinuz", JASPER)
        self.assertIn("/live/initrd.img", JASPER)

    def test_native_installer_requires_its_own_certified_runtime(self):
        self.assertIn("native-installer-runtime.ready", INSTALL)
        self.assertIn("/boot/candidates/installer/installer-initrd.img", INSTALL)
        self.assertIn("/boot/candidates/installer/installation.img", INSTALL)
        self.assertIn("Native Koronos Installer runtime incomplete", INSTALL)
        self.assertNotIn("/install/installer/installation.img", INSTALL)

    def test_native_recovery_requires_its_own_certified_runtime(self):
        self.assertIn("native-recovery-runtime.ready", RECOVERY)
        self.assertIn("/boot/candidates/recovery/chimera-recovery-initramfs.img", RECOVERY)
        self.assertIn("Native Koronos Recovery runtime incomplete", RECOVERY)
        self.assertNotIn("/boot/recovery/chimera-recovery-initramfs.img", RECOVERY)

    def test_prototype_archives_never_activate_native_handoffs(self):
        for builder in (FULL_BUILDER, LIVE_BUILDER):
            self.assertIn("prototype-built-not-native-koronos-runtime", builder)
            self.assertIn("bootable_by_koronos", builder)
            self.assertIn("/boot/candidates/installer", builder)
            self.assertIn("/boot/candidates/recovery", builder)

    def test_boot_artwork_is_staged_offline_by_both_builders(self):
        for builder in (FULL_BUILDER, LIVE_BUILDER):
            self.assertTrue(
                'base64 -d "$ROOT/boot/visual/$art"' in builder
                or 'base64 -d "$ROOT/boot/visual/aurora-wayland-glass.jpg.b64"' in builder
                or 'aurora-wayland-glass.jpg' in builder,
                "builder must stage the Aurora background"
            )
            self.assertIn('"$STAGE/boot/grub/Init.mp4"', builder)
            self.assertIn("library-artwork-manifest.json", builder)

    def test_original_chimera_wallpaper_and_manifest_are_staged(self):
        art = ROOT / "desktop/aurora/assets/chimera-infinite-research-horizon.svg"
        manifest = ROOT / "desktop/aurora/assets/chimera-artwork-manifest.json"
        self.assertTrue(art.is_file() and art.stat().st_size > 500)
        self.assertTrue(manifest.is_file())
        self.assertIn("chimera-infinite-research-horizon.svg", FULL_BUILDER)
        self.assertIn("chimera-infinite-research-horizon.svg", LIVE_BUILDER)
        self.assertIn("chimera-artwork-manifest.json", FULL_BUILDER)
        self.assertIn("chimera-artwork-manifest.json", LIVE_BUILDER)

    def test_no_synthetic_boot_progress_percentages(self):
        for path in ("boot/iso/grub.cfg", "boot/spitfire/spitfire-menu.cfg",
                     "boot/gates/gates-menu.cfg", "boot/jasper/live-image.cfg",
                     "boot/jasper/install.cfg", "boot/jasper/recovery.cfg"):
            self.assertNotRegex((ROOT / path).read_text(), r"\b(?:25|40|50|60|75|90|100)%")

    def test_generated_live_and_recovery_userspace_emit_distinct_handoff_markers(self):
        builder = (ROOT / "tools/build-live-boot-binaries.sh").read_text()
        self.assertIn("USERSPACE READY: target=live init_pid=%s", builder)
        self.assertIn("USERSPACE READY: target=recovery init_pid=%s", builder)
        self.assertIn("exec /bin/sh -i", builder)
        self.assertIn("exec /bin/chimera-recovery-console.sh", builder)
        self.assertIn("Aurora desktop readiness is separate", builder)


if __name__ == "__main__":
    unittest.main(verbosity=2)
