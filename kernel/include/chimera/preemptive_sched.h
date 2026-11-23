#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

/* One-CPU preemptive kernel-task runtime. This is deliberately separate from
 * the cooperative chimera_sched_* API until the assembly context switch and
 * timer preemption gates pass independently. */
int koronos_preemptive_selftest(void);
uint32_t koronos_preemptive_switch_count(void);
uint32_t koronos_preemptive_timer_count(void);
uint32_t koronos_preemptive_guard_failures(void);
uint32_t koronos_preemptive_interleavings(void);

#ifdef __cplusplus
}
#endif
