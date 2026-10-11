#include "chimera/nbit.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>

int main() {
    assert(chimera_nbit_init() == 0);

    chimera_nbit_capabilities caps{};
    assert(chimera_nbit_get_capabilities(&caps) == 0);
    assert(caps.minimum_virtual_bits == 1u && caps.maximum_virtual_bits == UINT32_MAX);
    assert((caps.flags & CHIMERA_NBIT_CAP_ARBITRARY_WIDTH) != 0);
    assert(chimera_nbit_validate(13u) == 0);
    assert(chimera_nbit_validate(8193u) == 0);
    assert(chimera_nbit_set_default(13u) == 0);
    assert(chimera_nbit_set_default(64u) == 0);

    chimera_nbit_process_context p32{}, p128{}, compat{}, virtual_nbit{}, physical{};
    assert(chimera_nbit_process_init(&p32, 101u, 32u, 0u) == 0);
    assert(chimera_nbit_process_init(&p128, 202u, 128u, 0u) == 0);
    assert(p32.execution_class == CHIMERA_EXEC_EMULATED);
    assert(p128.execution_class == CHIMERA_EXEC_EMULATED);

    chimera_nbit_process_context found{};
    assert(chimera_nbit_process_get(101u, &found) == 0);
    assert(found.mode_bits == 32u && found.process_id == 101u);

    chimera_nbit_process_context snapshot[8]{};
    assert(chimera_nbit_process_snapshot(snapshot, 8u) == 2u);
    chimera_nbit_registry_snapshot registry{};
    assert(chimera_nbit_registry_get_snapshot(&registry) == 0);
    assert(registry.registered_processes == 2u);
    assert(registry.capacity == CHIMERA_NBIT_MAX_PROCESS_MODES);

    /* A fixed byte-stream is transportable across N-bit modes; raw pointers
       are never converted or dereferenced by the receiving process. */
    const uint8_t payload[] = {0x43, 0x48};
    chimera_ipc_wire wire{};
    assert(chimera_nbit_ipc_prepare(101u, 202u, payload, 13u, 7u, &wire) == 0);
    assert(wire.sender_mode_bits == 32u);
    assert(wire.receiver_mode_bits == 128u);
    assert(wire.payload_bytes == 2u);
    assert(wire.sequence == 7u);
    assert(chimera_nbit_ipc_validate(&wire) == 0);
    uint8_t receiver_copy[2] = {};
    assert(chimera_nbit_ipc_copy_payload(&wire, receiver_copy, sizeof(receiver_copy)) == 2);
    assert(receiver_copy[0] == payload[0] && receiver_copy[1] == payload[1]);
    assert(chimera_nbit_ipc_copy_payload(&wire, receiver_copy, 1u) < 0);

    chimera_ipc_wire malformed = wire;
    malformed.payload_bytes = 1u;
    assert(chimera_nbit_ipc_validate(&malformed) != 0);

    assert(chimera_nbit_process_init_physical_native(&physical, 505u, 13u) == -6);
    assert(chimera_nbit_process_init_physical_native(&physical, 505u, caps.native_hardware_bits) == 0);
    assert(physical.execution_class == CHIMERA_EXEC_NATIVE);

    assert(chimera_nbit_process_init_chimera(&virtual_nbit, 404u, 8193u) == 0);
    assert(virtual_nbit.execution_class == CHIMERA_EXEC_CHIMERA_VIRTUAL);
    assert(chimera_nbit_process_set_mode(&virtual_nbit, 100003u) == 0);
    assert(virtual_nbit.mode_bits == 100003u);
    assert(virtual_nbit.execution_class == CHIMERA_EXEC_CHIMERA_VIRTUAL);
    assert(chimera_nbit_process_get(404u, &found) == 0 && found.mode_bits == 100003u);

    assert(chimera_nbit_process_init(&compat, 303u, 64u, CHIMERA_COMPAT_LINUX) == 0);
    assert(compat.execution_class == CHIMERA_EXEC_COMPATIBILITY);
    assert(chimera_nbit_process_set_mode(&compat, 32u) == 0);
    assert(compat.execution_class == CHIMERA_EXEC_COMPATIBILITY);
    assert(chimera_nbit_process_unregister(101u) == 0);
    assert(chimera_nbit_process_get(101u, &found) != 0);
    assert(chimera_nbit_process_unregister(202u) == 0);
    assert(chimera_nbit_process_unregister(303u) == 0);
    assert(chimera_nbit_process_unregister(404u) == 0);
    assert(chimera_nbit_process_unregister(505u) == 0);

    puts("N-bit process registry and cross-width IPC contracts passed.");
    return 0;
}
