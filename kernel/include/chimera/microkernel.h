#pragma once

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef uint32_t chimera_cap_t;
typedef uint32_t chimera_endpoint_t;

typedef enum chimera_mk_status {
    CHIMERA_MK_OK = 0,
    CHIMERA_MK_INVALID = -1,
    CHIMERA_MK_DENIED = -2,
    CHIMERA_MK_BUSY = -3,
    CHIMERA_MK_EMPTY = -4
} chimera_mk_status_t;

typedef struct chimera_mk_message {
    uint32_t opcode;
    uint32_t flags;
    uint64_t arg0;
    uint64_t arg1;
    uint64_t arg2;
    uint64_t arg3;
} chimera_mk_message_t;

typedef int (*chimera_mk_endpoint_handler_t)(const chimera_mk_message_t* msg, chimera_mk_message_t* reply);

void chimera_mk_init(void);
chimera_cap_t chimera_mk_cap_grant(uint32_t owner, uint32_t rights);
int chimera_mk_cap_revoke(chimera_cap_t cap);
chimera_endpoint_t chimera_mk_endpoint_create(chimera_cap_t cap, chimera_mk_endpoint_handler_t handler);
int chimera_mk_endpoint_send(chimera_endpoint_t endpoint, chimera_cap_t cap, const chimera_mk_message_t* msg);
int chimera_mk_endpoint_receive(chimera_endpoint_t endpoint, chimera_cap_t cap, chimera_mk_message_t* msg);
int64_t chimera_mk_syscall(uint64_t number, uint64_t arg0, uint64_t arg1, uint64_t arg2, uint64_t arg3);

#ifdef __cplusplus
}
#endif
