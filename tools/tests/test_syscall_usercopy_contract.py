#!/usr/bin/env python3
"""Source contract tests for user-memory safety at syscall boundaries.

These tests guard the wiring contract only. Native kernel build and ring-3
runtime tests are still required to establish fault handling and lifecycle safety.
"""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class SyscallUserCopyContract(unittest.TestCase):
    def test_every_implemented_user_pointer_path_uses_copy_helpers(self):
        launch = (ROOT / "kernel/core/target_launch.cpp").read_text()
        console = (ROOT / "kernel/core/koronos.cpp").read_text()
        syscall = (ROOT / "kernel/core/syscall.cpp").read_text()

        self.assertIn("koronos_target_copy_from_user(&c, user_path + length, 1u)", launch)
        self.assertIn("koronos_target_copy_from_user(kernel_buffer, user_buffer, count)", launch)
        self.assertIn("koronos_target_copy_to_user(user_buffer, kernel_buffer", launch)
        self.assertIn("koronos_target_copy_from_user(kernel_buffer, address, length)", console)
        self.assertIn("koronos_target_fs_open(frame->rdi, frame->rsi)", syscall)
        self.assertIn("koronos_target_fs_read(frame->rdi, frame->rsi, frame->rdx)", syscall)
        self.assertIn("koronos_target_fs_write(fd, address, length)", syscall)

    def test_read_pins_writable_destination_before_vfs_side_effect(self):
        launch = (ROOT / "kernel/core/target_launch.cpp").read_text()
        start = launch.index('extern "C" int64_t koronos_target_fs_read(')
        end = launch.index('extern "C" int64_t koronos_target_fs_write(', start)
        read_impl = launch[start:end]
        self.assertLess(read_impl.index("koronos_address_space_pin("),
                        read_impl.index("chimera_vfs_read("))
        self.assertIn("koronos_address_space_unpin(", read_impl)
        self.assertIn("uint8_t kernel_buffer[4096]", read_impl)

    def test_write_copies_to_kernel_memory_before_backend(self):
        launch = (ROOT / "kernel/core/target_launch.cpp").read_text()
        start = launch.index('extern "C" int64_t koronos_target_fs_write(')
        end = launch.index('extern "C" int64_t koronos_target_fs_close(', start)
        write_impl = launch[start:end]
        self.assertLess(write_impl.index("koronos_target_copy_from_user("),
                        write_impl.index("chimera_vfs_write("))
        self.assertIn("uint8_t kernel_buffer[4096]", write_impl)

    def test_validator_resolves_a_live_space_and_checks_owned_page_metadata(self):
        vm = (ROOT / "kernel/core/address_space.cpp").read_text()
        start = vm.index('extern "C" int koronos_address_space_validate_user_range(')
        end = vm.index('extern "C" int koronos_address_space_register_tlb_shootdown(', start)
        validator = vm[start:end]
        self.assertIn("space_for_root(root_physical)", validator)
        self.assertIn("lock_backend()", validator)
        self.assertIn("meta->owner_generation != space->generation", validator)
        self.assertIn("(*pte & ENTRY_USER)", validator)
        self.assertIn("write_access && !(*pte & ENTRY_WRITE)", validator)

    def test_release_build_fails_closed_when_exact_session_wallpapers_are_missing(self):
        builder = (ROOT / "build-chimera-iso.sh").read_text()
        embedder = (ROOT / "tools/wallpapers/embed_wallpapers.py").read_text()
        self.assertIn('CHIMERA_REQUIRE_SESSION_BRANDING:-1', builder)
        self.assertIn('expected_sha256', embedder)
        self.assertIn('SHA-256 mismatch', embedder)

    def test_offline_wallpapers_do_not_enable_remote_sources_by_default(self):
        config = json.loads((ROOT / "desktop/aurora/wallpaper-service.json").read_text())
        service = (ROOT / "desktop/aurora/wallpaper-service.py").read_text()
        self.assertIs(config.get("remote_sources_opt_in"), False)
        self.assertIn('"remote_sources_opt_in",False', service)
        self.assertIn('"session_branding_css":"/usr/share/chimera/aurora/assets/dual-os-brand-wallpapers.css"', service)


if __name__ == "__main__":
    unittest.main(verbosity=2)
