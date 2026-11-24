#include <cassert>
#include <cstdint>
#include <cstring>
#include "chimera/multiboot_modules.h"

namespace {
alignas(8) uint8_t info[512];
uint32_t align8(uint32_t n) { return (n + 7u) & ~7u; }
uint32_t append_module(uint32_t off, uint32_t start, uint32_t end, const char *cmd) {
    const uint32_t size = 16u + static_cast<uint32_t>(std::strlen(cmd)) + 1u;
    const uint32_t type = 3u;
    std::memcpy(info + off, &type, 4);
    std::memcpy(info + off + 4, &size, 4);
    std::memcpy(info + off + 8, &start, 4);
    std::memcpy(info + off + 12, &end, 4);
    std::memcpy(info + off + 16, cmd, std::strlen(cmd) + 1u);
    return off + align8(size);
}
}
int main() {
    std::memset(info, 0, sizeof(info));
    uint32_t total = 0, reserved = 0;
    std::memcpy(info, &total, 4);
    std::memcpy(info + 4, &reserved, 4);
    uint32_t off = 8;
    off = append_module(off, 0x100000, 0x101000, "chimera-recovery-initramfs");
    off = append_module(off, 0x102000, 0x102400, "chimera-recovery-manifest");
    off = append_module(off, 0x103000, 0x104000, "chimera-live-initramfs");
    off = append_module(off, 0x105000, 0x106000, "chimera-user-init-elf target=live");
    off = append_module(off, 0x107000, 0x108000, "chimera-user-init-elf target=installer");
    off = append_module(off, 0x109000, 0x10A000, "chimera-user-init-elf target=recovery");
    const uint32_t end_type = 0, end_size = 8;
    std::memcpy(info + off, &end_type, 4);
    std::memcpy(info + off + 4, &end_size, 4);
    off += 8;
    total = off;
    std::memcpy(info, &total, 4);
    assert(chimera_multiboot_scan(reinterpret_cast<uint64_t>(info)) == 6);
    assert(chimera_multiboot_find(CHIMERA_MODULE_RECOVERY_INITRAMFS) != nullptr);
    assert(chimera_multiboot_find(CHIMERA_MODULE_RECOVERY_MANIFEST) != nullptr);
    assert(chimera_multiboot_find(CHIMERA_MODULE_LIVE_INITRAMFS) != nullptr);
    assert(chimera_multiboot_find(CHIMERA_MODULE_INSTALL_IMAGE) == nullptr);
    assert(chimera_multiboot_find(CHIMERA_MODULE_USER_INIT_ELF) != nullptr);

    // A module command line must terminate inside its own tag. Bytes in the
    // alignment padding must never extend a truncated command into a trusted
    // USER_INIT_ELF classification.
    std::memset(info, 0, sizeof(info));
    total = 56;
    const uint32_t module_type = 3u, truncated_size = 34u;
    const uint32_t module_start = 0x200000u, module_end = 0x201000u;
    std::memcpy(info, &total, 4);
    std::memcpy(info + 8, &module_type, 4);
    std::memcpy(info + 12, &truncated_size, 4);
    std::memcpy(info + 16, &module_start, 4);
    std::memcpy(info + 20, &module_end, 4);
    std::memcpy(info + 24, "chimera-user-init-", sizeof("chimera-user-init-") - 1u);
    std::memcpy(info + 42, "elf", sizeof("elf"));
    std::memcpy(info + 48, &end_type, 4);
    std::memcpy(info + 52, &end_size, 4);
    assert(chimera_multiboot_scan(reinterpret_cast<uint64_t>(info)) == 0);
    assert(chimera_multiboot_module_count() == 0);
    assert(chimera_multiboot_find(CHIMERA_MODULE_USER_INIT_ELF) == nullptr);

    // Reject a tag whose 32-bit size wraps off + size. The previous parser
    // accepted this value, parsed the malformed module, and wrapped its
    // aligned cursor back to the start of the Multiboot information block.
    std::memset(info, 0, sizeof(info));
    total = 16;
    const uint32_t overflowing_size = 0xfffffff8u;
    std::memcpy(info, &total, 4);
    std::memcpy(info + 8, &module_type, 4);
    std::memcpy(info + 12, &overflowing_size, 4);
    assert(chimera_multiboot_scan(reinterpret_cast<uint64_t>(info)) == 0);
    assert(chimera_multiboot_module_count() == 0);
    return 0;
}
