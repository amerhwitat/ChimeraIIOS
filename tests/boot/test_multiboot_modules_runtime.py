from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[2]


def test_multiboot_runtime_classifies_recovery_and_diagnostics_modules():
    compiler = shutil.which("g++") or shutil.which("c++")
    assert compiler, "a C++ compiler is required for the Multiboot parser runtime test"
    harness = r"""
#include "chimera/multiboot_modules.h"
#include <cassert>
#include <cstdint>
#include <cstring>

static void put32(uint8_t *p, uint32_t v) { std::memcpy(p, &v, sizeof(v)); }
static uint32_t align8(uint32_t n) { return (n + 7u) & ~7u; }

static uint32_t add_tag(uint8_t *p, uint32_t off, uint32_t type,
                        const void *payload, uint32_t payload_size) {
    const uint32_t size = 8u + payload_size;
    put32(p + off, type);
    put32(p + off + 4, size);
    if (payload_size) std::memcpy(p + off + 8, payload, payload_size);
    return off + align8(size);
}

static uint32_t add_module(uint8_t *p, uint32_t off, uint32_t start,
                           uint32_t end, const char *cmd) {
    const uint32_t size = 16u + static_cast<uint32_t>(std::strlen(cmd)) + 1u;
    put32(p + off, 3);
    put32(p + off + 4, size);
    put32(p + off + 8, start);
    put32(p + off + 12, end);
    std::strcpy(reinterpret_cast<char *>(p + off + 16), cmd);
    return off + align8(size);
}

static uint32_t build_info(uint8_t *p, const char *cmdline, bool recovery) {
    std::memset(p, 0, 512);
    uint32_t off = 8;
    off = add_tag(p, off, 1, cmdline, static_cast<uint32_t>(std::strlen(cmdline)) + 1u);
    if (recovery) {
        off = add_module(p, off, 0x1000, 0x2000, "chimera-recovery-initramfs");
        off = add_module(p, off, 0x3000, 0x3100, "chimera-recovery-manifest");
        off = add_module(p, off, 0x4000, 0x4100, "aurora-diagnostics");
    } else if (std::strcmp(cmdline, "chm.mode=installer") == 0) {
        off = add_module(p, off, 0x1000, 0x2000, "chimera-installation-image");
        off = add_module(p, off, 0x3000, 0x3100, "chimera-installation-manifest");
        off = add_module(p, off, 0x4000, 0x4100, "chimera-installer-contract");
        off = add_module(p, off, 0x5000, 0x5100, "chimera-install-phases");
        off = add_module(p, off, 0x6000, 0x6100, "chimera-installer-profiles");
    } else {
        off = add_module(p, off, 0x1000, 0x2000, "chimera-live-initramfs");
        off = add_module(p, off, 0x3000, 0x3100, "chimera-live-manifest");
    }
    put32(p + off, 0);
    put32(p + off + 4, 8);
    off += 8;
    put32(p, off);
    put32(p + 4, 0);
    return off;
}

int main() {
    alignas(8) uint8_t info[512]{};
    build_info(info, "chm.mode=diagnostics", true);
    assert(chimera_multiboot_scan(reinterpret_cast<uint64_t>(info)) == 3);
    assert(chimera_multiboot_diagnostics_mode() == 1);
    assert(std::strcmp(chimera_multiboot_kernel_cmdline(), "chm.mode=diagnostics") == 0);
    assert(chimera_multiboot_find(CHIMERA_MODULE_RECOVERY_INITRAMFS));
    assert(chimera_multiboot_find(CHIMERA_MODULE_RECOVERY_MANIFEST));
    assert(chimera_multiboot_find(CHIMERA_MODULE_DIAGNOSTIC_BACKGROUND));

    build_info(info, "chm.mode=live", false);
    assert(chimera_multiboot_scan(reinterpret_cast<uint64_t>(info)) == 2);
    assert(chimera_multiboot_diagnostics_mode() == 0);
    assert(chimera_multiboot_find(CHIMERA_MODULE_LIVE_INITRAMFS));
    assert(chimera_multiboot_find(CHIMERA_MODULE_LIVE_MANIFEST));

    build_info(info, "chm.mode=installer", false);
    assert(chimera_multiboot_scan(reinterpret_cast<uint64_t>(info)) == 5);
    assert(chimera_multiboot_diagnostics_mode() == 0);
    assert(chimera_multiboot_find(CHIMERA_MODULE_INSTALL_IMAGE));
    assert(chimera_multiboot_find(CHIMERA_MODULE_INSTALL_MANIFEST));
    assert(chimera_multiboot_find(CHIMERA_MODULE_INSTALL_CONTRACT));
    assert(chimera_multiboot_find(CHIMERA_MODULE_INSTALL_PHASES));
    assert(chimera_multiboot_find(CHIMERA_MODULE_INSTALL_PROFILES));
    return 0;
}
"""
    with tempfile.TemporaryDirectory(prefix="chimera-multiboot-test-") as tmp:
        tmp_path = Path(tmp)
        source = tmp_path / "multiboot_runtime_test.cpp"
        binary = tmp_path / "multiboot_runtime_test"
        source.write_text(harness, encoding="utf-8")
        subprocess.run(
            [
                compiler,
                "-std=c++17",
                "-Wall",
                "-Wextra",
                "-I",
                str(ROOT / "kernel" / "include"),
                str(ROOT / "kernel" / "core" / "multiboot_modules.cpp"),
                str(source),
                "-o",
                str(binary),
            ],
            check=True,
            cwd=ROOT,
        )
        subprocess.run([str(binary)], check=True, cwd=ROOT)
