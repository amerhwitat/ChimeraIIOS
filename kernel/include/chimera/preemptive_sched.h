#pragma once
#include <stdint.h>
#include "chimera/scheduler.h"
#ifdef __cplusplus
extern "C" {
#endif

#define KORONOS_TIMER_VECTOR_PIT      32u
#define KORONOS_TIMER_VECTOR_YIELD    33u
#define KORONOS_TIMER_VECTOR_AP_TICK  49u
#define KORONOS_TIMER_VECTOR_AP_WORK  50u

/* Compatibility counters. The runtime now measures real scheduler work. */
int koronos_preemptive_selftest(void);
uint32_t koronos_preemptive_switch_count(void);
uint32_t koronos_preemptive_timer_count(void);
uint32_t koronos_preemptive_guard_failures(void);
uint32_t koronos_preemptive_interleavings(void);

/* Unified PIT + x2APIC IPI tick ownership and per-CPU setup. */
int koronos_preemptive_init(uint32_t cpu_count);
int koronos_preemptive_cpu_init(uint32_t cpu,uint32_t apic_id);
int koronos_preemptive_apic_init(void);
uint32_t koronos_preemptive_current_cpu(void);
uint32_t koronos_preemptive_current_apic_id(void);
int koronos_preemptive_send_ipi(uint32_t cpu,uint32_t vector);
int koronos_preemptive_arm_user_timeout(uint32_t ticks);
void koronos_preemptive_disarm_user_timeout(void);
int koronos_preemptive_user_timeout_irq(void);
void koronos_preemptive_dump_measurements(void);

/* Backend entry used by arch/x86_64/interrupts.asm. */
chimera_switch_target *koronos_preempt_irq_handler(uint64_t vector);

#ifdef __cplusplus
}
#endif
