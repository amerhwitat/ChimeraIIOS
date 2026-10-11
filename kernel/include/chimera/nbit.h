#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_NBIT_CONTEXT_VERSION 3u
#define CHIMERA_NBIT_MAX_PROCESS_MODES 1024u
#define CHIMERA_NBIT_MODE_MIN_BITS 1u
/* Width is policy/resource bounded, not a power-of-two whitelist. */
#define CHIMERA_NBIT_MODE_MAX_BITS UINT32_MAX

typedef enum chimera_nbit_execution_class {
    CHIMERA_EXEC_NATIVE = 0,          /* Physical CPU native word width only. */
    CHIMERA_EXEC_EMULATED = 1,        /* Guest compatibility/reference execution. */
    CHIMERA_EXEC_COMPATIBILITY = 2,   /* OS/ABI personality layered over a backend. */
    CHIMERA_EXEC_CHIMERA_VIRTUAL = 3  /* Chimera N-bit ABI; not a physical CPU claim. */
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

typedef struct chimera_nbit_registry_snapshot {
    uint32_t abi_version;
    uint32_t registered_processes;
    uint32_t capacity;
    uint32_t default_mode_bits;
} chimera_nbit_registry_snapshot;

typedef struct chimera_nbit_capabilities {
    uint32_t native_hardware_bits;
    uint32_t default_mode_bits;
    uint32_t minimum_virtual_bits;
    uint32_t maximum_virtual_bits;
    uint32_t registered_process_capacity;
    uint32_t flags;
} chimera_nbit_capabilities;

enum { CHIMERA_NBIT_CAP_ARBITRARY_WIDTH = 1u << 0,
       CHIMERA_NBIT_CAP_CHIMERA_VIRTUAL_ABI = 1u << 1,
       CHIMERA_NBIT_CAP_PHYSICAL_NATIVE_IS_HARDWARE_ONLY = 1u << 2 };

int chimera_nbit_init(void);
int chimera_nbit_get_default(uint32_t *bits);
int chimera_nbit_set_default(uint32_t bits);
int chimera_nbit_validate(uint32_t bits);
int chimera_nbit_get_capabilities(chimera_nbit_capabilities *out);
int chimera_nbit_process_init(chimera_nbit_process_context *ctx, uint32_t process_id, uint32_t requested_bits, uint32_t compatibility_target);
/* Explicit user-selected Chimera N-bit virtual ABI; requested width may be any positive uint32_t. */
int chimera_nbit_process_init_chimera(chimera_nbit_process_context *ctx, uint32_t process_id, uint32_t requested_bits);
/* Rejects any width except the probed physical CPU native word width. */
int chimera_nbit_process_init_physical_native(chimera_nbit_process_context *ctx, uint32_t process_id, uint32_t requested_bits);
int chimera_nbit_process_set_mode(chimera_nbit_process_context *ctx, uint32_t bits);
int chimera_nbit_process_set_compatibility(chimera_nbit_process_context *ctx, uint32_t target);
int chimera_nbit_process_unregister(uint32_t process_id);
int chimera_nbit_process_get(uint32_t process_id, chimera_nbit_process_context *out);
uint32_t chimera_nbit_process_snapshot(chimera_nbit_process_context *out, uint32_t capacity);
int chimera_nbit_registry_get_snapshot(chimera_nbit_registry_snapshot *out);
int chimera_nbit_ipc_prepare(uint32_t sender_id, uint32_t receiver_id, const void *payload, uint32_t payload_bits, uint64_t sequence, chimera_ipc_wire *out);
int chimera_nbit_ipc_validate(const chimera_ipc_wire *wire);
int chimera_nbit_ipc_copy_payload(const chimera_ipc_wire *wire, void *receiver_buffer, uint32_t receiver_capacity);

#ifdef __cplusplus
}
#endif
