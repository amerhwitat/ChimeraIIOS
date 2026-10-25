#pragma once
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Versioned contract for a real task-owned execution context.
 * This declaration does not itself schedule a task or transfer ownership.
 * The scheduler must not publish READY until every owned resource is valid. */
#define KORONOS_TASK_CONTEXT_ABI 1u
#define KORONOS_TASK_CONTROL_BLOCK_MAGIC 0x4B544342u /* "KTCB" */
#define KORONOS_TASK_CONTEXT_X86_64 0x8664u

enum koronos_task_flags {
    KORONOS_TASK_F_OWNS_ADDRESS_SPACE = 1u << 0,
    KORONOS_TASK_F_OWNS_KERNEL_STACK  = 1u << 1,
    KORONOS_TASK_F_OWNS_USER_STACK    = 1u << 2,
    KORONOS_TASK_F_CONTEXT_VALID      = 1u << 3,
    KORONOS_TASK_F_RESOURCES_RELEASED = 1u << 4
};

/* x86-64 cooperative switch ABI. The switch routine must preserve the SysV
 * callee-saved GPRs and resume at RIP with RSP. CR3 and flags are explicit so
 * a future implementation cannot accidentally treat a callback as a context.
 * This is NOT the user SYSCALL frame; see koronos_user_syscall_frame. */
typedef struct koronos_x86_64_switch_context {
    uint64_t r15;                 /* +0  */
    uint64_t r14;                 /* +8  */
    uint64_t r13;                 /* +16 */
    uint64_t r12;                 /* +24 */
    uint64_t rbx;                 /* +32 */
    uint64_t rbp;                 /* +40 */
    uint64_t rsp;                 /* +48 */
    uint64_t rip;                 /* +56 */
    uint64_t rflags;              /* +64 */
    uint64_t cr3;                 /* +72: physical page-table root */
    uint64_t fs_base;             /* +80: task TLS base, if supported */
    uint64_t user_gs_base;        /* +88: user GS base, if supported */
    uint64_t fx_state;            /* +96: owned/aligned FXSAVE area pointer */
} koronos_x86_64_switch_context;

/* Kernel-owned PCB. Pointers are opaque handles; only the owning subsystem
 * may destroy them. Do not copy this structure after publication. Mutations
 * require the process/scheduler lock, and terminal resources must be released
 * before the record can be reaped. Architecture backend owns arch_context. */
typedef struct koronos_task_control_block {
    uint32_t magic;
    uint16_t abi;
    uint16_t architecture;
    uint32_t pid;
    uint32_t parent_pid;
    uint32_t state;
    uint32_t flags;
    uint32_t running_cpu;         /* UINT32_MAX when not executing */
    int32_t exit_code;
    uint64_t affinity_mask;
    void *address_space;          /* opaque VM-owned handle */
    void *kernel_stack_base;
    uint64_t kernel_stack_size;
    uint64_t kernel_stack_top;
    uint64_t user_stack_top;
    uint64_t entry;
    void *arch_context;           /* points to arch-specific saved context */
    void *saved_trap_frame;       /* full interrupt frame, if preempted */
    void *wait_object;             /* opaque wait-queue/object reference */
    uint64_t run_count;
    uint64_t accounting_ticks;
} koronos_task_control_block;

#ifdef __cplusplus
}
static_assert(sizeof(koronos_x86_64_switch_context) == 104,
              "x86-64 switch context ABI size changed");
static_assert(offsetof(koronos_x86_64_switch_context, rsp) == 48,
              "x86-64 switch context RSP offset changed");
static_assert(offsetof(koronos_x86_64_switch_context, rip) == 56,
              "x86-64 switch context RIP offset changed");
static_assert(offsetof(koronos_x86_64_switch_context, cr3) == 72,
              "x86-64 switch context CR3 offset changed");
#endif
