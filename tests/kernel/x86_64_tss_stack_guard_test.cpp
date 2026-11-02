#include "chimera/x86_64_cpu.h"
#include <assert.h>
#include <stdio.h>

int main() {
    assert(chimera_x86_64_tss_update_allowed(0x2ull) == 1);
    assert(chimera_x86_64_tss_update_allowed(0x202ull) == 0);
    assert(chimera_x86_64_tss_update_allowed(0x246ull) == 0);
    assert(chimera_x86_64_tss_update_allowed(0x2ull | (1ull << 10)) == 1);
    puts("x86_64 TSS stack guard: updates require IF clear");
    return 0;
}
