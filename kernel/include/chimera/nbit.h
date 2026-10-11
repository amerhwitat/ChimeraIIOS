#pragma once
#include <stdint.h>
#include "chimera/hardware.h"
#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_NBIT_CONTEXT_VERSION 4u
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

typedef enum chimera_nbit_guest_isa {
    CHIMERA_GUEST_ISA_AUTO = 0,
    CHIMERA_GUEST_ISA_CHIMERA_NBIT = 1,
    CHIMERA_GUEST_ISA_X86_16 = 2,
    CHIMERA_GUEST_ISA_X86_32 = 3,
    CHIMERA_GUEST_ISA_X86_64 = 4,
    CHIMERA_GUEST_ISA_AARCH64 = 5,
    CHIMERA_GUEST_ISA_ARM32 = 6,
    CHIMERA_GUEST_ISA_ARM32_THUMB = 7,
    CHIMERA_GUEST_ISA_RISCV32 = 8,
    CHIMERA_GUEST_ISA_RISCV64 = 9,
    CHIMERA_GUEST_ISA_RISCV128 = 10,
    CHIMERA_GUEST_ISA_MIPS32 = 11,
    CHIMERA_GUEST_ISA_MIPS64 = 12,
    CHIMERA_GUEST_ISA_POWERPC = 13,
    CHIMERA_GUEST_ISA_PPC64 = 14,
    CHIMERA_GUEST_ISA_LOONGARCH32 = 15,
    CHIMERA_GUEST_ISA_LOONGARCH64 = 16,
    CHIMERA_GUEST_ISA_S390X = 17,
    CHIMERA_GUEST_ISA_SPARC_V9 = 18,
    CHIMERA_GUEST_ISA_WASM32 = 19,
    CHIMERA_GUEST_ISA_WASM64 = 20
} chimera_nbit_guest_isa;

typedef struct chimera_nbit_process_context {
    uint32_t process_id;
    uint32_t mode_bits;
    uint32_t guest_isa;
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
    uint32_t default_backend;
    uint32_t default_compatibility_target;
    uint32_t default_guest_isa;
} chimera_nbit_capabilities;

typedef enum chimera_nbit_backend {
    CHIMERA_NBIT_BACKEND_AUTO = 0,
    CHIMERA_NBIT_BACKEND_CHIMERA_VIRTUAL = 1,
    CHIMERA_NBIT_BACKEND_PHYSICAL_NATIVE = 2,
    CHIMERA_NBIT_BACKEND_COMPATIBILITY = 3
} chimera_nbit_backend;

enum { CHIMERA_NBIT_PROCESS_FLAG_CHIMERA_VIRTUAL = 1u << 0 };

enum { CHIMERA_NBIT_CAP_ARBITRARY_WIDTH = 1u << 0,
       CHIMERA_NBIT_CAP_CHIMERA_VIRTUAL_ABI = 1u << 1,
       CHIMERA_NBIT_CAP_PHYSICAL_NATIVE_IS_HARDWARE_ONLY = 1u << 2 };

int chimera_nbit_init(void);
int chimera_nbit_get_default(uint32_t *bits);
int chimera_nbit_set_default(uint32_t bits);
int chimera_nbit_set_default_profile(uint32_t bits, chimera_nbit_backend backend, uint32_t compatibility_target);
int chimera_nbit_set_default_profile_ex(uint32_t bits, chimera_nbit_backend backend, uint32_t compatibility_target, chimera_nbit_guest_isa guest_isa);
int chimera_nbit_validate(uint32_t bits);
int chimera_nbit_get_capabilities(chimera_nbit_capabilities *out);
int chimera_nbit_process_init(chimera_nbit_process_context *ctx, uint32_t process_id, uint32_t requested_bits, uint32_t compatibility_target);
int chimera_nbit_process_init_default(chimera_nbit_process_context *ctx, uint32_t process_id, uint32_t requested_bits);
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
