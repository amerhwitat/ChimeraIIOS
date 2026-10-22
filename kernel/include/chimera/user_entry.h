#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define KORONOS_USER_SYSCALL_EXIT_SENTINEL 0xFFFFFFFFFFFFFFF0ull

/* Install user selectors, a 64-bit TSS/RSP0, and the x86-64 SYSCALL MSRs.
   Call only after NX/address-space initialization has succeeded. */
int koronos_user_entry_init(void);

/* Arm a PIT IRQ0-backed, in-kernel user execution deadline. The IRQ path may
   abort a non-returning ring-3 task and resume its saved kernel continuation. */
int koronos_user_timeout_arm(uint32_t ticks);
void koronos_user_timeout_disarm(void);
int koronos_user_timeout_irq(void);

/* Enter a prepared user address space. Returns only after the user process exits
   through the native exit syscall; entry and stack must be validated user VAs. */
int koronos_arch_enter_user(uint64_t cr3, uint64_t entry, uint64_t user_stack_top);

/* Register layout produced by user_entry.asm; offsets are part of the ABI. */
typedef struct koronos_user_syscall_frame {
    uint64_t r15, r14, r13, r12, r11, r10, r9, r8;
    uint64_t rdi, rsi, rbp, rdx, rcx, rbx, rax;
} koronos_user_syscall_frame;

uint64_t koronos_syscall_user_dispatch(const koronos_user_syscall_frame *frame);
extern volatile uint64_t koronos_user_exit_code;

#ifdef __cplusplus
}
#endif
