#include "chimera/x86_64_cpu.h"
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>


int main() {
    assert(chimera_x86_64_tss_update_allowed(0x2ull) == 1);
    assert(chimera_x86_64_tss_update_allowed(0x202ull) == 0);
    assert(chimera_x86_64_tss_update_allowed(0x246ull) == 0);
    assert(chimera_x86_64_tss_update_allowed(0x2ull | (1ull << 10)) == 1);
    return 0;
}
