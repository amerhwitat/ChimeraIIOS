#!/usr/bin/env python3
"""Static regressions for the x86-64 ISO menu routing and offline artwork contract."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
GRUB = (ROOT / "boot/iso/grub.cfg").read_text()
INSTALL = (ROOT / "boot/jasper/install.cfg").read_text()
INSTALL_MENU = (ROOT / "boot/installation/menu.cfg").read_text()
INSTALL_SERVICES = (ROOT / "boot/installation/services.cfg").read_text()
RECOVERY = (ROOT / "boot/jasper/recovery.cfg").read_text()
PREPARE_LAYOUT = (ROOT / "boot/iso/prepare-layout.sh").read_text()
NATIVE_BUILDER = (ROOT / "boot/iso/build-iso.sh").read_text()
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

    def test_full_iso_builder_stages_native_target_modules_and_canonical_menus(self):
        self.assertIn('TARGET_INIT_DIR="$ROOT/build/koronos/x86_64"', FULL_BUILDER)
        self.assertIn("for target in live installer recovery; do", FULL_BUILDER)
        self.assertIn('test -s "$target_elf"', FULL_BUILDER)
        self.assertIn("readelf -h", FULL_BUILDER)
        self.assertIn('cp -f "$target_elf" "$STAGE/boot/targets/"', FULL_BUILDER)
        self.assertIn('cp -f "$ROOT/boot/iso/grub.cfg" "$STAGE/boot/grub/grub.cfg"', FULL_BUILDER)
        self.assertIn('cp -f "$ROOT/boot/loader-menu.cfg" "$STAGE/boot/loader-menu.cfg"', FULL_BUILDER)


    def test_nested_target_menus_are_available_in_bios_and_uefi(self):
        firmware_branch = GRUB.rindex('if [ "$grub_platform" = efi ]; then')
        for entry in (
            'menuentry "Chimera II OS — Jasper Boot Manager / All Modes"',
            'menuentry "Chimera II OS — Installation Menu"',
            'menuentry "Chimera II OS — Recovery Menu"',
            'menuentry "Chimera II OS — Diagnostics Menu"',
            'menuentry "Chimera II OS — Retro / Emulator Center"',
            'menuentry "Chimera II OS — Spit Fire Native Menu"',
        ):
            self.assertLess(GRUB.index(entry), firmware_branch)

    def test_installer_services_submenu_is_reachable_staged_and_native(self):
        self.assertIn("configfile /boot/installation/services.cfg", INSTALL_MENU)
        self.assertIn("set timeout=120", INSTALL_SERVICES)
        self.assertIn("set timeout_style=menu", INSTALL_SERVICES)
        self.assertIn(
            "module2 /boot/targets/target-init-installer.elf chimera-user-init-elf target=installer firmware=$grub_platform",
            INSTALL_SERVICES,
        )
        self.assertIn(
            "module2 /install/installer/services/service-selection.json chimera-installer-services-contract",
            INSTALL_SERVICES,
        )
        self.assertTrue((ROOT / "installer/services/service-selection.json").is_file())
        self.assertIn('cp -a "$ROOT/boot/installation/services.cfg" "$STAGE/boot/installation/"', FULL_BUILDER)
        self.assertIn('cp -a "$ROOT/boot/installation/services.cfg" "$STAGE/boot/installation/"', LIVE_BUILDER)
        self.assertIn('cp "$ROOT/boot/installation/services.cfg" "$DIST/boot/installation/services.cfg"', PREPARE_LAYOUT)

    def test_prepared_recovery_menu_preserves_visible_canonical_policy(self):
        self.assertIn('cp -f "$ROOT/boot/jasper/recovery.cfg" "$DIST/boot/jasper/recovery.cfg"', PREPARE_LAYOUT)
        self.assertNotIn('cat > "$DIST/boot/jasper/recovery.cfg"', PREPARE_LAYOUT)
        self.assertNotIn("set timeout=5", PREPARE_LAYOUT)
        self.assertIn("set timeout=120", RECOVERY)
        self.assertIn("set timeout_style=menu", RECOVERY)


    def test_recovery_menu_routes_to_recovery_config(self):
        start = GRUB.index('--id recovery {')
        end = GRUB.index('\n}', start)
        entry = GRUB[start:end]
        self.assertIn("configfile /boot/jasper/recovery.cfg", entry)
        self.assertIn("/boot/recovery/chimera-recovery-initramfs.img", RECOVERY)

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


    def test_prepare_layout_stages_jasper_retro_submenu(self):
        self.assertIn("configfile /boot/jasper/retro.cfg", GRUB)
        self.assertTrue((ROOT / "boot/jasper/retro.cfg").is_file())
        self.assertIn('bash "$ISO_ROOT/prepare-layout.sh"', NATIVE_BUILDER)
        self.assertIn(
            'cp "$ROOT/boot/jasper/retro.cfg" "$DIST/boot/jasper/retro.cfg"',
            PREPARE_LAYOUT,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
