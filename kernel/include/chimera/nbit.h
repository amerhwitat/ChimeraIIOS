#pragma once
#include <stdint.h>
#include "chimera/hardware.h"

#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_NBIT_CONTEXT_VERSION 1u
#define CHIMERA_NBIT_MAX_PROCESS_MODES 1024u

typedef enum chimera_nbit_execution_class {
    CHIMERA_EXEC_NATIVE = 0,
    CHIMERA_EXEC_EMULATED = 1,
    CHIMERA_EXEC_COMPATIBILITY = 2
} chimera_nbit_execution_class;

typedef struct chimera_nbit_process_context {
    uint32_t process_id;
    uint32_t mode_bits;
    chimera_nbit_execution_class execution_class;
    uint32_t compatibility_target;
    uint32_t abi_version;
    uint32_t flags;
} chimera_nbit_process_context;

typedef struct chimera_ipc_wire {
    uint32_t version;
    uint32_t sender_mode_bits;
    uint32_t receiver_mode_bits;
    uint32_t payload_bits;
    uint32_t payload_bytes;
    uint64_t sequence;
    const void *payload;
} chimera_ipc_wire;

int chimera_nbit_init(void);
int chimera_nbit_get_default(uint32_t *bits);
int chimera_nbit_set_default(uint32_t bits);
int chimera_nbit_validate(uint32_t bits);
int chimera_nbit_process_init(chimera_nbit_process_context *ctx, uint32_t process_id, uint32_t requested_bits, uint32_t compatibility_target);
int chimera_nbit_process_set_mode(chimera_nbit_process_context *ctx, uint32_t bits);
int chimera_nbit_process_set_compatibility(chimera_nbit_process_context *ctx, uint32_t target);
int chimera_nbit_ipc_validate(const chimera_ipc_wire *wire);

#ifdef __cplusplus
}
#endif
