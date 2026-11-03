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


class IsoTargetRoutingTests(unittest.TestCase):
    def test_grub_menu_waits_30_seconds_for_user_selection(self):
        self.assertIn("set timeout_style=menu", GRUB)
        self.assertIn("set timeout=30", GRUB)
        self.assertIn("set default=0", GRUB)

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
            self.assertIn("for boot_stage in visual spitfire jasper grub; do", builder)
            self.assertIn('install -D -m 0644 "$INIT_VIDEO_SOURCE" "$STAGE/boot/$boot_stage/Init.mp4"', builder)
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

    def test_initramfs_shells_never_emit_native_userspace_ready_markers(self):
        builder = (ROOT / "tools/build-live-boot-binaries.sh").read_text()
        self.assertNotIn("USERSPACE READY: target=live", builder)
        self.assertNotIn("USERSPACE READY: target=recovery", builder)
        self.assertIn("INITRAMFS DIAGNOSTIC SHELL", builder)
        self.assertIn("Koronos userspace handoff NOT VERIFIED", builder)
        self.assertIn("exec /bin/sh -i", builder)
        self.assertIn("exec /bin/chimera-recovery-console.sh", builder)
        # A shell handoff is not evidence that the Aurora desktop is ready.
        self.assertIn("Aurora desktop readiness is separate", builder)

    def test_installer_loader_fails_closed_without_executable_init_context(self):
        kernel = (ROOT / "kernel/core/koronos.cpp").read_text()
        installer = (ROOT / "tools/chimera-stage-installer-media.sh").read_text()
        full_builder = (ROOT / "build-chimera-iso.sh").read_text()
        runtime = (ROOT / "tools/chimera-installer-runtime.sh").read_text()
        process_api = (ROOT / "kernel/include/chimera/process.h").read_text()
        self.assertIn("CHIMERA_MODULE_USER_INIT_ELF", kernel)
        self.assertIn("KORONOS INSTALLER LOADER BLOCKED", kernel)
        self.assertIn("no executable installer init ELF module was supplied", kernel)
        self.assertIn("INITRAMFS DIAGNOSTIC SHELL READY", installer)
        self.assertIn("USERSPACE HANDOFF NOT VERIFIED", installer)
        self.assertIn("INITRAMFS DIAGNOSTIC SHELL READY", full_builder)
        self.assertIn("USERSPACE HANDOFF NOT VERIFIED", full_builder)
        self.assertIn("No Koronos CPL3 installer process", full_builder)
        self.assertIn("No Koronos CPL3 installer process", runtime)
        self.assertIn("CHIMERA_PROCESS_LOAD_PLAN_ONLY", process_api)

    def test_init_video_is_started_after_wayland_and_uses_existing_asset(self):
        desktop_init = (ROOT / "desktop/aurora/aurora-desktop-init.sh").read_text()
        labwc_autostart = (ROOT / "desktop/aurora/labwc/autostart").read_text()
        splash = (ROOT / "desktop/aurora/aurora-init-splash.sh").read_text()
        runtime_stage = (ROOT / "tools/stage-chimera-runtime.sh").read_text()
        self.assertIn("exec /usr/share/chimera/aurora/aurora-desktop-init.sh", labwc_autostart)
        self.assertIn('CHIMERA_INIT_VIDEO="${CHIMERA_INIT_VIDEO:-$AURORA/assets/Init.mp4}"', desktop_init)
        self.assertIn("export CHIMERA_INIT_VIDEO CHIMERA_PROGRESS_FILE", desktop_init)
        self.assertIn('bash "$AURORA/aurora-init-splash.sh"', desktop_init)
        self.assertIn("mpv --fs", splash)
        self.assertIn("ffplay -fs", splash)
        self.assertIn('"$DEST/usr/share/chimera/aurora/assets/"', runtime_stage)


if __name__ == "__main__":
    unittest.main(verbosity=2)
