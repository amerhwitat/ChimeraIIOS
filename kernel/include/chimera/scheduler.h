#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef void (*chimera_task_fn)(void*);
typedef struct { uint32_t id,cpu,state,priority; uint64_t runs,ticks; } chimera_task_info;
void chimera_sched_init(uint32_t cpu_count);
uint32_t chimera_sched_cpu_count(void);
int chimera_sched_submit(chimera_task_fn fn,void* arg,uint32_t priority);
uint32_t chimera_sched_run_once(uint32_t cpu);
uint32_t chimera_sched_snapshot(chimera_task_info* out,uint32_t capacity);
#ifdef __cplusplus
}
#endif