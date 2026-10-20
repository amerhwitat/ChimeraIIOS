#include "chimera/hardware.h"
#include <assert.h>
#include <stdio.h>
int main() {
    chimera_hardware_profile p{};
    assert(chimera_hardware_probe(nullptr) == -1);
    assert(chimera_hardware_probe(&p) == 0);
    assert(p.version == CHIMERA_HW_PROFILE_VERSION);
    assert(p.logical_cpus >= 1 && p.physical_cores >= 1 && p.logical_per_core >= 1);
    assert(p.native_pointer_bits == 32 || p.native_pointer_bits == 64);
    assert(p.native_nbit_mode == 32 || p.native_nbit_mode == 64);
    assert(p.best_nbit_mode == 32 || p.best_nbit_mode == 64);
    assert(p.maximum_emulated_nbit == CHIMERA_NBIT_8192);
    assert((p.compatibility_mask & CHIMERA_COMPAT_NATIVE) != 0);
    assert((p.compatibility_mask & CHIMERA_COMPAT_LINUX) == 0);
    assert(!chimera_hardware_supports_mode(&p, 8192));
    assert(!chimera_hardware_supports_mode(&p, 0));
    assert(chimera_hardware_best_mode(&p) == (int)p.best_nbit_mode);
    puts("CPU topology/profile regression tests: PASS");
    return 0;
}
