#include "../../kernel/include/chimera/process.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>

static void put16(uint8_t *p, uint16_t v) {
    p[0] = static_cast<uint8_t>(v);
    p[1] = static_cast<uint8_t>(v >> 8);
}
static void put32(uint8_t *p, uint32_t v) {
    for (int i = 0; i < 4; ++i) p[i] = static_cast<uint8_t>(v >> (8 * i));
}
static void put64(uint8_t *p, uint64_t v) {
    for (int i = 0; i < 8; ++i) p[i] = static_cast<uint8_t>(v >> (8 * i));
}
static void build_elf(uint8_t *b, size_t n) {
    for (size_t i = 0; i < n; ++i) b[i] = 0;
    b[0] = 0x7f; b[1] = 'E'; b[2] = 'L'; b[3] = 'F';
    b[4] = 2; b[5] = 1; b[6] = 1;
    put16(b + 16, KORONOS_ET_EXEC);
    put16(b + 18, KORONOS_EM_X86_64);
    put32(b + 20, 1);
    put64(b + 24, 0x400100);
    put64(b + 32, 64);
    put16(b + 52, 64);
    put16(b + 54, 56);
    put16(b + 56, 1);
    put32(b + 64, 1);       // PT_LOAD
    put32(b + 68, 5);       // PF_R | PF_X
    put64(b + 72, 0x100);   // file offset
    put64(b + 80, 0x400100);
    put64(b + 96, 4);
    put64(b + 104, 4096);
    put64(b + 112, 4096);
    b[0x100] = 0x90; b[0x101] = 0x90; b[0x102] = 0x90; b[0x103] = 0xc3;
}
int main() {
    uint8_t elf[512];
    build_elf(elf, sizeof(elf));
    assert(koronos_elf64_validate(elf, sizeof(elf), KORONOS_EM_X86_64) == 1);

    // Attacker-controlled offsets and counts must never wrap the bounds check.
    put64(elf + 32, UINT64_MAX - 7);
    assert(koronos_elf64_validate(elf, sizeof(elf), KORONOS_EM_X86_64) == 0);
    build_elf(elf, sizeof(elf));
    put16(elf + 56, UINT16_MAX);
    assert(koronos_elf64_validate(elf, sizeof(elf), KORONOS_EM_X86_64) == 0);

    build_elf(elf, sizeof(elf));
    chimera_process_image admitted{};
    assert(chimera_process_init() == 0);
    int pid = chimera_process_admit_elf(elf, sizeof(elf), KORONOS_EM_X86_64,
                                        0x700000, &admitted);
    assert(pid > 0 && admitted.pid == static_cast<uint32_t>(pid));
    assert(admitted.state == CHIMERA_PROCESS_ADMITTED);
    assert(admitted.segment_count == 1 && admitted.entry == 0x400100);

    // An entry point in a non-executable PT_LOAD is not a runnable ELF image.
    put32(elf + 68, 6); // PF_R | PF_W
    chimera_process_image rejected{};
    assert(chimera_process_admit_elf(elf, sizeof(elf), KORONOS_EM_X86_64,
                                     0x700000, &rejected) < 0);
    puts("ELF64 validation/admission: bounds and executable-entry checks passed");
    return 0;
}
