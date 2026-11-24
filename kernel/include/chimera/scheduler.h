#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef void (*chimera_task_fn)(void*);
enum { CHIMERA_TASK_READY=0, CHIMERA_TASK_RUNNING=1, CHIMERA_TASK_BLOCKED=2, CHIMERA_TASK_EXITED=3 };
typedef struct {
    uint32_t id; uint32_t cpu; uint32_t state; uint32_t priority;
    uint64_t affinity_mask; uint64_t runs; uint64_t ticks;
    uint64_t total_ticks; uint32_t ticks_remaining; uint32_t preemptions;
} chimera_task_info;

/* Assembly loads this target after the interrupt frame has been saved. */
typedef struct {
    void *ctx;
    uint64_t cr3;
} chimera_switch_target;

void chimera_sched_init(uint32_t cpu_count);
uint32_t chimera_sched_cpu_count(void);
int chimera_sched_submit(chimera_task_fn fn,void* arg,uint32_t priority);
int chimera_sched_set_affinity(uint32_t task_id,uint64_t affinity_mask);
int chimera_sched_set_task_cr3(uint32_t task_id,uint64_t cr3);
uint64_t chimera_sched_task_cr3(uint32_t task_id);
uint32_t chimera_sched_run_once(uint32_t cpu);
/* Cooperative serial stepping only; retained for explicit legacy callers. */
uint32_t chimera_sched_run_serial_range(uint32_t first_cpu,uint32_t cpu_count);
/* Runs scheduler-submitted tasks on real APs; returns the AP task count. */
uint32_t chimera_sched_run_parallel(uint32_t first_cpu,uint32_t cpu_count);
/* Normal runtime path: preemptive, time-sliced, per-CPU scheduler entry. */
uint32_t chimera_sched_run_preemptive(uint32_t cpu);
int chimera_sched_preemptive_init(uint32_t cpu_count);
int chimera_sched_preemptive_ready(void);
void *chimera_sched_irq_handler(uint64_t vector);
void *chimera_sched_cpu_state(uint32_t cpu);
void chimera_sched_set_cpu_online(uint32_t cpu,uint32_t apic_id);
uint32_t chimera_sched_cpu_online(uint32_t cpu);
uint32_t chimera_sched_apic_id(uint32_t cpu);
uint32_t chimera_sched_preemptive_dispatches(uint32_t cpu);
uint32_t chimera_sched_preemptive_switches(uint32_t cpu);
uint32_t chimera_sched_preemptive_ticks(uint32_t cpu);
uint32_t chimera_sched_preemptive_preemptions(uint32_t cpu);
uint32_t chimera_sched_guard_failures(void);
uint64_t chimera_sched_total_context_switches(void);
uint64_t chimera_sched_total_preemptions(void);
uint64_t chimera_sched_total_timer_ticks(void);
uint32_t chimera_sched_parallel_overlap(void);
uint32_t chimera_sched_parallel_cpu_tasks(uint32_t cpu);
uint64_t chimera_sched_parallel_cpu_work(uint32_t cpu);
void chimera_sched_parallel_timestamps(uint64_t *bsp_start,uint64_t *ap_start,
                                       uint64_t *bsp_end,uint64_t *ap_end);
void chimera_sched_yield(void);
void chimera_sched_block(void);
void chimera_sched_wake(uint32_t task_id);
void chimera_sched_exit(void);
uint32_t chimera_sched_snapshot(chimera_task_info* out,uint32_t capacity);
uint32_t chimera_sched_runnable_count(void);
#ifdef __cplusplus
}
#endif
