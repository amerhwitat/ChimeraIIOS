#pragma once
#include <stdint.h>
#include "chimera/scheduler.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef uint32_t chimera_thread_id;

typedef struct {
    chimera_thread_id id;
    uint32_t priority;
    uint32_t cpu;
    uint32_t state;
    uint32_t affinity_mask;
    uint64_t runs;
    uint64_t ticks;
    void *argument;
} chimera_thread_info;

int chimera_thread_create(chimera_task_fn entry, void *argument,
                          uint32_t priority, uint32_t affinity_mask,
                          chimera_thread_id *out_id);
int chimera_thread_exit(void);
int chimera_thread_yield(void);
int chimera_thread_block(void);
int chimera_thread_wake(chimera_thread_id id);
int chimera_thread_current(chimera_thread_id *out_id);
uint32_t chimera_thread_snapshot(chimera_thread_info *out, uint32_t capacity);

#ifdef __cplusplus
}
#endif
