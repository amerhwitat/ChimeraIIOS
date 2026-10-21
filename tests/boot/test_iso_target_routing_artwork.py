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
LIVE = (ROOT / "boot/jasper/live.cfg").read_text()
FULL_ISO_WORKFLOW = (ROOT / ".github/workflows/chimera-full-iso.yml").read_text()


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
        self.assertIn("chimera-user-init-elf target=installer", entry)
        self.assertIn("--id installer", INSTALL)
        self.assertIn("/install/installer/installation.img", INSTALL)

    def test_recovery_menu_routes_to_recovery_config(self):
        start = GRUB.index('--id recovery {')
        end = GRUB.index('\n}', start)
        entry = GRUB[start:end]
        self.assertIn("configfile /boot/jasper/recovery.cfg", entry)
        self.assertIn("/boot/recovery/chimera-recovery-initramfs.img", RECOVERY)
        self.assertIn("chimera-user-init-elf target=recovery", RECOVERY)

    def test_native_ring3_init_is_built_and_staged_without_fabricated_readiness(self):
        source = (ROOT / "kernel/userland/native_init.c").read_text()
        builder = (ROOT / "tools/build-live-boot-binaries.sh").read_text()
        self.assertIn("native-init.elf", builder)
        self.assertIn("chimera-user-init-elf target=live", GRUB)
        self.assertIn("chimera-user-init-elf target=installer", GRUB)
        self.assertIn("chimera-user-init-elf target=recovery", RECOVERY)
        self.assertIn('int $0x80', source)
        self.assertIn("SYS_GETPID", source)
        self.assertIn("SYS_EXIT,78", source)
        self.assertNotIn("USERSPACE READY:", source)

    def test_full_iso_gate_boots_real_native_init_not_a_candidate_probe(self):
        self.assertIn('extract /boot/koronos/native-init.elf "$tree/boot/koronos/native-init.elf"', FULL_ISO_WORKFLOW)
        self.assertIn('module2 /boot/koronos/native-init.elf chimera-user-init-elf target=$target', FULL_ISO_WORKFLOW)
        self.assertIn("CPL3 identity and RAM VFS create/write/seek/read/stat/chmod/chown/truncate/close/rename/unlink/mkdir/rmdir passed", FULL_ISO_WORKFLOW)
        self.assertIn("verify-userspace-handoff.py", FULL_ISO_WORKFLOW)
        self.assertIn("firmware: [bios, uefi]", FULL_ISO_WORKFLOW)
        self.assertIn('vars="$base/$target-vars.fd"', FULL_ISO_WORKFLOW)
        self.assertIn("FAIL: $FIRMWARE production handoff is NOT VERIFIED", FULL_ISO_WORKFLOW)

    def test_each_real_target_entry_stages_exactly_one_native_init_elf(self):
        def entry(source, marker):
            start = source.index(marker)
            end = source.index("\n}", start)
            return source[start:end]

        # A duplicate USER_INIT_ELF makes the kernel's fail-closed launch
        # selector reject the whole target; a missing one leaves no ring-3 init.
        live_entry = entry(LIVE, '--id aurora-live {')
        installer_entry = entry(INSTALL, '--id installer {')
        recovery_entry = entry(RECOVERY, '--id recovery-terminal {')
        recovery_safe_entry = entry(RECOVERY, '--id recovery-safe {')
        for name, target_entry, target in (
            ("Live", live_entry, "live"),
            ("Installer", installer_entry, "installer"),
            ("Recovery", recovery_entry, "recovery"),
            ("Safe Recovery", recovery_safe_entry, "recovery"),
        ):
            with self.subTest(target=name):
                lines = [
                    line for line in target_entry.splitlines()
                    if "module2 /boot/koronos/native-init.elf chimera-user-init-elf" in line
                ]
                self.assertEqual(len(lines), 1, f"{name} must stage exactly one USER_INIT_ELF")
                self.assertIn(f"target={target}", lines[0])

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

    def test_generated_live_and_recovery_initramfs_use_diagnostic_markers_only(self):
        builder = (ROOT / "tools/build-live-boot-binaries.sh").read_text()
        self.assertIn("INITRAMFS SHELL READY: target=live (payload diagnostic only)", builder)
        self.assertIn("INITRAMFS SHELL READY: target=recovery (payload diagnostic only)", builder)
        self.assertNotIn("printf 'USERSPACE READY: target=live", builder)
        self.assertNotIn("printf 'USERSPACE READY: target=recovery", builder)
        self.assertIn("exec /bin/sh -i", builder)
        self.assertIn("exec /bin/chimera-recovery-console.sh", builder)
        # An initramfs shell diagnostic is not proof of a kernel-managed
        # ring-3 process or a readiness marker from the canonical acceptance ABI.
        self.assertIn("shell as a kernel-managed process", builder)


if __name__ == "__main__":
    unittest.main(verbosity=2)
