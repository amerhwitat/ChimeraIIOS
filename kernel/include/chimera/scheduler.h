#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

typedef void (*chimera_task_fn)(void*);
enum { CHIMERA_TASK_READY=0, CHIMERA_TASK_RUNNING=1, CHIMERA_TASK_BLOCKED=2, CHIMERA_TASK_EXITED=3 };
typedef struct {
    uint32_t id;
    uint32_t cpu;
    uint32_t state;
    uint32_t priority;
    uint64_t affinity_mask;
    uint64_t runs;
    uint64_t ticks;
} chimera_task_info;
void chimera_sched_init(uint32_t cpu_count);
uint32_t chimera_sched_cpu_count(void);
int chimera_sched_submit(chimera_task_fn fn,void* arg,uint32_t priority);
int chimera_sched_set_affinity(uint32_t task_id,uint64_t affinity_mask);
uint32_t chimera_sched_run_once(uint32_t cpu);
uint32_t chimera_sched_run_parallel(uint32_t first_cpu,uint32_t cpu_count);
uint32_t chimera_sched_snapshot(chimera_task_info* out,uint32_t capacity);
void chimera_sched_yield(void);
void chimera_sched_block(void);
void chimera_sched_wake(uint32_t task_id);
void chimera_sched_exit(void);
uint32_t chimera_sched_runnable_count(void);
#ifdef __cplusplus
}
#endif
