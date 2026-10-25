#!/usr/bin/env python3
"""Source-contract checks for process-bound syscall user-memory access.

These tests detect regressions in the boundary wiring; they do not replace
native kernel execution, fault-injection, or QEMU runtime acceptance.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class UserCopyBoundaryContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.launch = (ROOT / "kernel/core/target_launch.cpp").read_text()
        cls.console = (ROOT / "kernel/core/koronos.cpp").read_text()
        cls.syscall = (ROOT / "kernel/core/syscall.cpp").read_text()
        cls.address_space = (ROOT / "kernel/core/address_space.cpp").read_text()
        cls.header = (ROOT / "kernel/include/chimera/target_launch.h").read_text()

    def test_shared_copy_api_is_exported_and_declared(self):
        for name in ("koronos_target_copy_from_user", "koronos_target_copy_to_user"):
            self.assertIn('extern "C" int ' + name, self.launch)
            self.assertIn("int " + name, self.header)

    def test_copy_primitives_validate_bounds_pin_validate_and_unpin(self):
        self.assertIn("length - 1u > UINT64_MAX - address", self.launch)
        for function in ("koronos_target_copy_from_user", "koronos_target_copy_to_user"):
            start = self.launch.index('extern "C" int ' + function)
            end = self.launch.find('\nextern "C" int ', start + 1)
            if end < 0:
                end = self.launch.find("\n/* Process-owned descriptors", start)
            body = self.launch[start:end]
            self.assertIn("user_range_bounds_valid", body)
            self.assertIn("koronos_address_space_root(active_address_space) != active_root", body)
            self.assertIn("koronos_address_space_pin", body)
            self.assertIn("koronos_address_space_validate_user_range", body)
            self.assertIn("koronos_address_space_unpin", body)

    def test_filesystem_backends_receive_kernel_owned_staging(self):
        self.assertIn("chimera_vfs_read(pid, static_cast<int64_t>(fd), kernel_buffer, count)", self.launch)
        self.assertIn("koronos_target_copy_to_user(user_buffer, kernel_buffer", self.launch)
        self.assertIn("koronos_target_copy_from_user(kernel_buffer, user_buffer, count)", self.launch)
        self.assertNotIn(
            "chimera_vfs_read(pid, static_cast<int64_t>(fd),\n        reinterpret_cast<void *>(static_cast<uintptr_t>(user_buffer))",
            self.launch,
        )
        self.assertNotIn(
            "chimera_vfs_write(pid, static_cast<int64_t>(fd),\n        reinterpret_cast<const void *>(static_cast<uintptr_t>(user_buffer))",
            self.launch,
        )

    def test_console_syscall_uses_kernel_buffer_before_inspection(self):
        start = self.console.index('extern "C" int64_t koronos_console_write_user')
        end = self.console.find('\nextern "C" void koronos_target_log', start)
        body = self.console[start:end]
        self.assertIn("koronos_target_copy_from_user(kernel_buffer, address, length)", body)
        self.assertIn("koronos_target_note_user_write(reinterpret_cast<const char *>(kernel_buffer)", body)
        self.assertIn("debugcon_write8(kernel_buffer[i])", body)
        self.assertNotIn("reinterpret_cast<const uint8_t *>(static_cast<uintptr_t>(address))", body)

    def test_address_space_regressions_cover_cross_page_and_overflow(self):
        self.assertIn("CHIMERA_ELF_USER_LIMIT - 1u, 2u, 0u", self.address_space)
        self.assertIn("0xFFFF800000000000ull, 1u, 0u", self.address_space)
        self.assertIn("KORONOS_USER_VIRTUAL_MIN + PAGE_SIZE - 1u, 2u, 0u", self.address_space)
        self.assertIn("0u, 0u, 0u) == 0", self.address_space)
        self.assertIn("write_access > 1u || root_physical == 0u", self.address_space)
        self.assertIn("space_for_root(root_physical)", self.address_space)
        self.assertIn("meta->owner_generation != space->generation", self.address_space)
        self.assertIn("lock_backend()", self.address_space)

    def test_syscall_write_routes_console_and_regular_files_separately(self):
        self.assertIn("koronos_console_write_user(address, length)", self.syscall)
        self.assertIn("koronos_target_fs_write(fd, address, length)", self.syscall)
        self.assertIn("if (length > 4096u)", self.syscall)

    def test_every_user_pointer_path_uses_the_shared_process_bound_copy(self):
        # OPEN consumes a path; READ writes to user memory; WRITE reads from it.
        open_start = self.launch.index('extern "C" int64_t koronos_target_fs_open')
        read_start = self.launch.index('extern "C" int64_t koronos_target_fs_read')
        write_start = self.launch.index('extern "C" int64_t koronos_target_fs_write')
        close_start = self.launch.index('extern "C" int64_t koronos_target_fs_close')
        open_body = self.launch[open_start:read_start]
        read_body = self.launch[read_start:write_start]
        write_body = self.launch[write_start:close_start]
        self.assertIn("copy_target_user_path(user_path, path)", open_body)
        self.assertIn("koronos_target_copy_to_user(user_buffer, kernel_buffer", read_body)
        self.assertLess(read_body.index("koronos_address_space_pin("),
                        read_body.index("chimera_vfs_read("))
        self.assertIn("koronos_target_copy_from_user(kernel_buffer, user_buffer, count)", write_body)
        for body in (open_body, read_body, write_body):
            self.assertIn("active_pid", body)
        self.assertNotIn("reinterpret_cast<void *>(static_cast<uintptr_t>(user_buffer))", read_body)
        self.assertNotIn("reinterpret_cast<const void *>(static_cast<uintptr_t>(user_buffer))", write_body)

    def test_address_space_range_check_uses_process_root_and_checks_each_page(self):
        start = self.address_space.index('extern "C" int koronos_address_space_validate_user_range')
        end = self.address_space.index('extern "C" int koronos_address_space_register_tlb_shootdown', start)
        body = self.address_space[start:end]
        self.assertIn("root_physical == 0u", body)
        self.assertIn("length > CHIMERA_ELF_USER_LIMIT - address", body)
        self.assertIn("while (page < end)", body)
        self.assertIn("user_page_access(root_physical, page, write_access != 0)", body)
        pin_start = self.address_space.index('extern "C" int koronos_address_space_pin')
        pin_end = self.address_space.index('extern "C" int koronos_address_space_unpin', pin_start)
        pin_body = self.address_space[pin_start:pin_end]
        self.assertIn("meta->pins == UINT16_MAX", pin_body)
        self.assertIn("(write_access && !(*pte & ENTRY_WRITE))", pin_body)
        self.assertIn("++meta->pins", pin_body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
