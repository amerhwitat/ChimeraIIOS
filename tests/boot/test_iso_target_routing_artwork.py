#!/usr/bin/env python3
"""Static regressions for the x86-64 ISO menu routing and offline artwork contract."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
GRUB = (ROOT / "boot/iso/grub.cfg").read_text()
INSTALL = (ROOT / "boot/jasper/install.cfg").read_text()
RECOVERY = (ROOT / "boot/jasper/recovery.cfg").read_text()
FULL_BUILDER = (ROOT / "tools/build-full-iso.sh").read_text()
LIVE_BUILDER = (ROOT / "iso/chimera-live-iso.sh").read_text()
CANONICAL_BUILDER = (ROOT / "build-chimera-iso.sh").read_text()


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


    def test_full_iso_builder_stages_all_target_init_elf_modules(self):
        self.assertIn("for target in live installer recovery; do", FULL_BUILDER)
        self.assertIn('target_elf="$TARGET_INIT_DIR/target-init-$target.elf"', FULL_BUILDER)
        for target, config in (("live", GRUB), ("installer", INSTALL), ("recovery", RECOVERY)):
            self.assertIn(f"target={target}", config)
        self.assertIn('TARGET_INIT_DIR="$ROOT/build/koronos/x86_64"', FULL_BUILDER)
        self.assertIn('cp -f "$target_elf" "$STAGE/boot/targets/"', FULL_BUILDER)
        self.assertIn('cp -f "$ROOT/boot/iso/grub.cfg" "$STAGE/boot/grub/grub.cfg"', FULL_BUILDER)
        self.assertIn('cp -f "$ROOT/boot/loader-menu.cfg" "$STAGE/boot/loader-menu.cfg"', FULL_BUILDER)


    def test_canonical_clean_iso_builder_stages_and_verifies_target_init_elfs(self):
        start = CANONICAL_BUILDER.index("create_boot_menu(){")
        end = CANONICAL_BUILDER.index("\\nprepare_branding(){", start)
        boot_stage = CANONICAL_BUILDER[start:end]
        self.assertIn('target_init_dir="$SCRIPT_DIR/build/koronos/x86_64"', boot_stage)
        self.assertIn('target_stage="$ISO_DIR/boot/targets"', boot_stage)
        self.assertIn('target-init-$target.elf', boot_stage)
        self.assertIn('generate-target-init-manifest.py', boot_stage)
        verify_start = CANONICAL_BUILDER.index("verify_iso(){")
        verify_end = CANONICAL_BUILDER.index("\\nreport_build(){", verify_start)
        verify_stage = CANONICAL_BUILDER[verify_start:verify_end]
        for target in ("live", "installer", "recovery"):
            self.assertIn(f"/boot/targets/target-init-{target}.elf", verify_stage)
            self.assertIn(f"/boot/targets/target-init-{target}.manifest.json", verify_stage)
        self.assertIn("target-init checksum/status mismatch", verify_stage)

    def test_live_iso_fallback_builds_and_stages_target_init_elfs(self):
        self.assertIn('TARGET_INIT_DIR="$ROOT/build/koronos/x86_64"', LIVE_BUILDER)
        self.assertIn('bash "$ROOT/kernel/build-koronos.sh"', LIVE_BUILDER)
        self.assertIn("for target in live installer recovery; do", LIVE_BUILDER)
        self.assertIn('target_elf="$TARGET_INIT_DIR/target-init-$target.elf"', LIVE_BUILDER)
        for target, config in (("live", GRUB), ("installer", INSTALL), ("recovery", RECOVERY)):
            self.assertIn(f"target={target}", config)
        self.assertIn('cp -f "$target_elf" "$STAGE/boot/targets/"', LIVE_BUILDER)

    def test_recovery_menu_routes_to_recovery_config(self):
        start = GRUB.index('--id recovery {')
        end = GRUB.index('\n}', start)
        entry = GRUB[start:end]
        self.assertIn("configfile /boot/jasper/recovery.cfg", entry)
        self.assertIn("/boot/recovery/chimera-recovery-initramfs.img", RECOVERY)


    def test_ring3_init_elf_is_dispatched_by_matching_target_service(self):
        source = (ROOT / "kernel/core/koronos.cpp").read_text()
        self.assertIn('find_target_init("live")', source)
        self.assertIn('find_target_init("installer")', source)
        self.assertIn('find_target_init("recovery")', source)
        self.assertLess(source.index('if (find_target_init("installer"))'), source.index('if (!image && !manifest && !contract && !phases && !profiles)'))
        self.assertIn("module_has_target(module, target)", source)
        self.assertIn("koronos_launch_selected_userspace()", source)
        self.assertNotIn('if (chimera_multiboot_find(CHIMERA_MODULE_USER_INIT_ELF))', source)
        self.assertIn('Recovery handoff withheld: no native recovery init ELF/runtime', source)
        self.assertIn('Installer handoff withheld: production payload has no supported native init ELF/runtime', source)

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
