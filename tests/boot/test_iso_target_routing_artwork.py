#!/usr/bin/env python3
"""Static regressions for the x86-64 ISO menu routing and offline artwork contract."""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[2]
GRUB = (ROOT / "boot/iso/grub.cfg").read_text()
INSTALL = (ROOT / "boot/jasper/install.cfg").read_text()
RECOVERY = (ROOT / "boot/jasper/recovery.cfg").read_text()
FULL_BUILDER = (ROOT / "tools/build-full-iso.sh").read_text()
LIVE_BUILDER = (ROOT / "iso/chimera-live-iso.sh").read_text()


class IsoTargetRoutingTests(unittest.TestCase):
    def test_installer_menu_passes_installer_modules_to_koronos(self):
        start = GRUB.index('--id install {')
        end = GRUB.index('\n}', start)
        entry = GRUB[start:end]
        self.assertIn("multiboot2 /boot/koronos/koronos.elf", entry)
        self.assertIn("module2 /install/installer/installation.img chimera-installation-image", entry)
        self.assertIn("module2 /install/installer/installation-manifest.json chimera-installation-manifest", entry)
        self.assertIn("module2 /install/installer/installer-contract.json chimera-installer-contract", entry)
        self.assertNotIn("chimera-live-initramfs.img", entry)
        self.assertIn("--id installer", INSTALL)
        self.assertIn("/install/installer/installation.img", INSTALL)

    def test_recovery_menu_routes_to_recovery_config(self):
        start = GRUB.index('--id recovery {')
        end = GRUB.index('\n}', start)
        entry = GRUB[start:end]
        self.assertIn("configfile /boot/jasper/recovery.cfg", entry)
        self.assertIn("/boot/recovery/chimera-recovery-initramfs.img", RECOVERY)

    def test_static_recovery_manifest_selects_the_built_production_initramfs(self):
        manifest = json.loads((ROOT / "boot/recovery/recovery-manifest.json").read_text())
        self.assertEqual(manifest.get("schema"), "CHM-RECOVERY-BOOT-2")
        self.assertEqual(
            manifest.get("initramfs"),
            "/boot/recovery/chimera-recovery-initramfs.img",
        )
        self.assertEqual(manifest.get("kernel"), "/boot/koronos/koronos.elf")
        # The full ISO builder copies this static directory after generated
        # artifacts, so the source manifest must retain the runtime selector.
        self.assertIn('cp -a "$ROOT/boot/recovery/." "$STAGE/boot/recovery/"', FULL_BUILDER)

    def test_mobile_target_fails_closed_on_x86_64_iso(self):
        start = GRUB.index('--id mobile {')
        end = GRUB.index('\n}', start)
        entry = GRUB[start:end]
        self.assertIn("not supported by this x86-64 ISO build", entry)
        self.assertNotIn("multiboot2", entry)

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

    def test_production_native_init_elves_are_staged_and_hashed(self):
        builder = (ROOT / "tools/build-live-boot-binaries.sh").read_text()
        for target in ("live", "installer", "recovery"):
            self.assertIn(f"native-init-{target}.elf", builder)
            self.assertIn(f"native-init-{target}.elf.sha256", builder)
        self.assertIn("production native init ELF missing", builder)
        self.assertIn('readelf -lW "$native_init"', builder)
        self.assertIn('"$OUT/boot/koronos/native-init-$target.elf"', builder)

    def test_misleading_live_readiness_label_removed(self):
        self.assertNotIn("[100% path ready]", GRUB)

    def test_generated_live_and_recovery_userspace_emit_distinct_handoff_markers(self):
        builder = (ROOT / "tools/build-live-boot-binaries.sh").read_text()
        self.assertIn("USERSPACE READY: target=live init_pid=%s", builder)
        self.assertIn("USERSPACE READY: target=recovery init_pid=%s", builder)
        self.assertIn("exec /bin/sh -i", builder)
        self.assertIn("exec /bin/chimera-recovery-console.sh", builder)
        # A shell handoff is not evidence that the Aurora desktop is ready.
        self.assertIn("Aurora desktop readiness is separate", builder)


if __name__ == "__main__":
    unittest.main(verbosity=2)
