#!/usr/bin/env python3
"""Static regressions for the x86-64 ISO menu routing and offline artwork contract."""
from pathlib import Path
import unittest
import re

ROOT = Path(__file__).resolve().parents[2]
GRUB = (ROOT / "boot/iso/grub.cfg").read_text()
INSTALL = (ROOT / "boot/jasper/install.cfg").read_text()
RECOVERY = (ROOT / "boot/jasper/recovery.cfg").read_text()
FULL_BUILDER = (ROOT / "tools/build-full-iso.sh").read_text()
LIVE_BUILDER = (ROOT / "iso/chimera-live-iso.sh").read_text()
FULL_ISO_WORKFLOW = (ROOT / ".github/workflows/chimera-full-iso.yml").read_text()
PREPARE_LAYOUT = (ROOT / "boot/iso/prepare-layout.sh").read_text()
TARGET_INIT_BUILDER = (ROOT / "tools/build-live-boot-binaries.sh").read_text()


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
        # prepare-layout.sh overwrites the checked-in recovery menu while mastering the ISO.
        generated_start = PREPARE_LAYOUT.index('cat > "$DIST/boot/jasper/recovery.cfg"')
        generated_end = PREPARE_LAYOUT.index("\nEOF", generated_start)
        generated = PREPARE_LAYOUT[generated_start:generated_end]
        self.assertIn("module2 /boot/targets/target-init-recovery.elf chimera-user-init-elf target=recovery", generated)
        self.assertIn("module2 /boot/recovery/chimera-recovery-initramfs.img chimera-recovery-initramfs", generated)
        self.assertIn("  boot", generated)
        self.assertIn('"$LIVE_BOOT/boot/targets/target-init-$target.elf"', PREPARE_LAYOUT)
        self.assertIn('"$LIVE_BOOT/boot/recovery/$required"', PREPARE_LAYOUT)
        self.assertIn('mkdir -p "$DIST/boot/live" "$DIST/boot/targets" "$DIST/boot/recovery"', PREPARE_LAYOUT)

    def test_full_iso_injection_replaces_stale_base_grub_menu(self):
        self.assertIn('cp -f "$ROOT/boot/iso/grub.cfg" "$STAGE/boot/grub/grub.cfg"', FULL_BUILDER)

    def test_live_builder_stages_real_target_elfs_and_checksums(self):
        for target in ("live", "installer", "recovery"):
            self.assertIn('target_elf="$BUILD_DIR/koronos/x86_64/target-init-$target.elf"', TARGET_INIT_BUILDER)
            self.assertIn('chimera_copy_if_distinct "$target_elf" "$TARGETS_OUT/target-init-$target.elf"', TARGET_INIT_BUILDER)
            self.assertIn('sha256sum "target-init-$target.elf" > "target-init-$target.elf.sha256"', TARGET_INIT_BUILDER)
            self.assertIn('sha256sum --check "target-init-$target.elf.sha256"', TARGET_INIT_BUILDER)
        self.assertIn('TARGETS_OUT="$OUT/boot/targets"', TARGET_INIT_BUILDER)

    def test_full_iso_builder_builds_kernel_before_staging_live_targets(self):
        self.assertLess(FULL_BUILDER.index("koronos-x86_64"), FULL_BUILDER.index('"$ROOT/tools/build-live-boot-binaries.sh"'))

    def test_mobile_target_fails_closed_on_x86_64_iso(self):
        start = GRUB.index('--id mobile {')
        end = GRUB.index('\n}', start)
        entry = GRUB[start:end]
        self.assertIn("not supported by this x86-64 ISO build", entry)
        self.assertNotIn("multiboot2", entry)

    def test_firmware_matrix_selects_targets_by_ids_from_the_immutable_iso(self):
        self.assertIn("terminal_input console serial", GRUB)
        # The workflow extracts GRUB from the ISO under test and resolves each
        # target by its stable --id. This guards against stale positional offsets
        # when menu entries are inserted or firmware-specific entries change.
        ids = re.findall(r"(?m)^\s*menuentry\b.*?--id\s+([A-Za-z0-9_-]+)", GRUB)
        for target, menu_id in (("live", "aurora-live"), ("installer", "install"), ("recovery", "recovery")):
            self.assertIn(menu_id, ids)
        self.assertIn('actual_grub="$base/actual-grub.cfg"', FULL_ISO_WORKFLOW)
        self.assertIn('entries.index(wanted[target])', FULL_ISO_WORKFLOW)
        self.assertIn('for ((key=0; key<menu_index; key++))', FULL_ISO_WORKFLOW)
        self.assertIn("'sendkey home 250'", FULL_ISO_WORKFLOW)
        self.assertIn("'sendkey down 250'", FULL_ISO_WORKFLOW)
        self.assertNotIn("for _ in {1..5}", FULL_ISO_WORKFLOW)

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
