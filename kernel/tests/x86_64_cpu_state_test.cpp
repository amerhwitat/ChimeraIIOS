#include "chimera/x86_64_cpu.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>

int main() {
    static_assert(sizeof(chimera_x86_64_tss) == 104, "architectural TSS size");
    static_assert(CHIMERA_X86_64_USER_CODE_SELECTOR == 0x1B, "user code selector RPL3");
    static_assert(CHIMERA_X86_64_USER_DATA_SELECTOR == 0x23, "user data selector RPL3");
    static_assert(CHIMERA_X86_64_TSS_SELECTOR == 0x28, "TSS selector");

    uint64_t low = 0, high = 0;
    const uint64_t base = 0x123456789ABCull;
    const uint32_t limit = sizeof(chimera_x86_64_tss) - 1u;
    chimera_x86_64_encode_tss_descriptor(base, limit, &low, &high);
    assert((low & 0xFFFFu) == limit);
    assert(((low >> 40) & 0xFFu) == 0x89u); /* present, available 64-bit TSS */
    assert(((low >> 16) & 0xFFFFFFu) == (base & 0xFFFFFFu));
    assert(((low >> 56) & 0xFFu) == ((base >> 24) & 0xFFu));
    assert(high == (base >> 32));

    puts("Koronos x86_64 TSS/GDT descriptor layout tests passed");
    return 0;
}
