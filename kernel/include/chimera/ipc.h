#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_IPC_ABI_VERSION 1u
#define CHIMERA_IPC_MAX_ENDPOINTS 32u
#define CHIMERA_IPC_QUEUE_DEPTH 16u
#define CHIMERA_IPC_MAX_PAYLOAD 1024u

typedef int (*chimera_ipc_copy_from_user_fn)(void *context, uint32_t sender_pid,
                                              void *kernel_dst, const void *user_src,
                                              uint32_t bytes);
typedef int (*chimera_ipc_copy_to_user_fn)(void *context, uint32_t receiver_pid,
                                            void *user_dst, const void *kernel_src,
                                            uint32_t bytes);

typedef struct chimera_ipc_service_ops {
    void *context;
    chimera_ipc_copy_from_user_fn copy_from_user;
    chimera_ipc_copy_to_user_fn copy_to_user;
} chimera_ipc_service_ops;

typedef struct chimera_ipc_message_info {
    uint32_t sender_pid;
    uint32_t sender_mode_bits;
    uint32_t receiver_mode_bits;
    uint32_t payload_bits;
    uint32_t payload_bytes;
    uint64_t sequence;
} chimera_ipc_message_info;

/* Configure once during kernel service startup with address-space-aware callbacks. */
int chimera_ipc_service_init(const chimera_ipc_service_ops *ops);
/* capability is an unguessable endpoint capability minted by a trusted caller. */
int chimera_ipc_endpoint_bind(uint32_t owner_pid, uint32_t endpoint_id,
                              uint64_t capability);
int chimera_ipc_endpoint_unbind(uint32_t owner_pid, uint32_t endpoint_id,
                                uint64_t capability);
/* Payload pointers are user virtual addresses and are accessed only via callbacks. */
int chimera_ipc_send(uint32_t sender_pid, uint32_t endpoint_id, uint64_t capability,
                     const void *user_payload, uint32_t payload_bits, uint64_t sequence);
int chimera_ipc_receive(uint32_t receiver_pid, uint32_t endpoint_id, uint64_t capability,
                        void *user_buffer, uint32_t capacity, chimera_ipc_message_info *out);
int chimera_ipc_cancel(uint32_t sender_pid, uint32_t endpoint_id, uint64_t sequence);
/* Call before discarding a process; removes its endpoints and queued messages. */
void chimera_ipc_process_exit(uint32_t process_id);
uint32_t chimera_ipc_queued_messages(uint32_t endpoint_id);

#ifdef __cplusplus
}
#endif
