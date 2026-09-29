#pragma once
#include <stdint.h>
#include "chimera/thread.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef void (*chimera_apc_callback)(chimera_thread_id thread_id, void *context);

#define CHIMERA_APC_MAX_PER_THREAD 64u

typedef struct {
    chimera_apc_callback callback;
    void *context;
    uint32_t queued;
    uint32_t alertable;
} chimera_apc_record;

int chimera_apc_queue(chimera_thread_id thread_id, chimera_apc_callback callback, void *context);
uint32_t chimera_apc_pending(chimera_thread_id thread_id);
uint32_t chimera_apc_deliver(chimera_thread_id thread_id, uint32_t alertable, uint32_t budget);
int chimera_apc_cancel_thread(chimera_thread_id thread_id);

#ifdef __cplusplus
}
#endif
