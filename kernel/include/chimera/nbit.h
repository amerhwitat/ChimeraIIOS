#pragma once
#include <stdint.h>
#include "chimera/hardware.h"

#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_NBIT_CONTEXT_VERSION 2u
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

/* Registry view: snapshots expose metadata only, never another process's pointers. */
typedef struct chimera_nbit_registry_snapshot {
    uint32_t abi_version;
    uint32_t registered_processes;
    uint32_t capacity;
    uint32_t default_mode_bits;
} chimera_nbit_registry_snapshot;

int chimera_nbit_init(void);
int chimera_nbit_get_default(uint32_t *bits);
int chimera_nbit_set_default(uint32_t bits);
int chimera_nbit_validate(uint32_t bits);
int chimera_nbit_process_init(chimera_nbit_process_context *ctx, uint32_t process_id, uint32_t requested_bits, uint32_t compatibility_target);
int chimera_nbit_process_set_mode(chimera_nbit_process_context *ctx, uint32_t bits);
int chimera_nbit_process_set_compatibility(chimera_nbit_process_context *ctx, uint32_t target);
/* Register/unregister/query process execution-mode metadata. */
int chimera_nbit_process_unregister(uint32_t process_id);
int chimera_nbit_process_get(uint32_t process_id, chimera_nbit_process_context *out);
uint32_t chimera_nbit_process_snapshot(chimera_nbit_process_context *out, uint32_t capacity);
int chimera_nbit_registry_get_snapshot(chimera_nbit_registry_snapshot *out);
/* Canonical byte-stream IPC permits different N-bit modes without sharing pointers. */
int chimera_nbit_ipc_prepare(uint32_t sender_id, uint32_t receiver_id,
                             const void *payload, uint32_t payload_bits,
                             uint64_t sequence, chimera_ipc_wire *out);
int chimera_nbit_ipc_validate(const chimera_ipc_wire *wire);
/* Kernel-side copy into a receiver-owned buffer; never pass sender pointers across address spaces. */
int chimera_nbit_ipc_copy_payload(const chimera_ipc_wire *wire, void *receiver_buffer, uint32_t receiver_capacity);

#ifdef __cplusplus
}
#endif
