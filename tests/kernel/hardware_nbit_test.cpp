#include "chimera/hardware.h"
#include "chimera/nbit.h"
#include <assert.h>
#include <stdio.h>

int main() {
    chimera_hardware_profile p{};
    assert(chimera_hardware_probe(&p) == 0);
    assert(p.version == CHIMERA_HW_PROFILE_VERSION);
    assert(p.logical_cpus >= 1);
    assert(chimera_hardware_supports_mode(&p, p.native_nbit_mode) == 1);
    assert(chimera_hardware_supports_mode(&p, 8192) == 0);
    assert(chimera_nbit_init() == 0);

    uint32_t best = 0;
    assert(chimera_nbit_get_default(&best) == 0);
    assert(chimera_nbit_validate(best) == 0);

    chimera_nbit_process_context low{}, high{};
    assert(chimera_nbit_process_init(&low, 1, p.native_nbit_mode, CHIMERA_COMPAT_NATIVE) == 0);
    assert(chimera_nbit_process_init(&high, 2, 64, CHIMERA_COMPAT_NATIVE) == 0);
    assert(low.mode_bits == p.native_nbit_mode);
    assert(high.mode_bits == 64);

    const char payload[] = "mixed-width IPC";
    chimera_ipc_wire wire{CHIMERA_NBIT_CONTEXT_VERSION, low.mode_bits, high.mode_bits,
                          8u * (uint32_t)(sizeof(payload) - 1), (uint32_t)(sizeof(payload) - 1), 1, payload};
    assert(chimera_nbit_ipc_validate(&wire) == 0);

    assert(chimera_nbit_process_set_mode(&low, p.native_nbit_mode) == 0);
    const uint32_t previous_target = low.compatibility_target;
    assert(chimera_nbit_process_set_compatibility(&low, CHIMERA_COMPAT_WINDOWS) == -1);
    assert(low.compatibility_target == previous_target);
    assert(low.execution_class != CHIMERA_EXEC_COMPATIBILITY);
    assert(chimera_nbit_process_init(&high, 3, 64, CHIMERA_COMPAT_LINUX) == -4);
    assert(chimera_nbit_process_init(&high, 4, 8192, CHIMERA_COMPAT_NATIVE) == -3);

    puts("chimera hardware/N-bit tests passed");
    return 0;
}
