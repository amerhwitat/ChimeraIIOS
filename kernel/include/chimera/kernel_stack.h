#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define KORONOS_KERNEL_STACK_ABI 1u
#define KORONOS_KERNEL_STACK_SLOT_COUNT 32u

typedef struct koronos_kernel_stack {
    uint32_t slot;
    uint32_t generation;
    uint64_t base;
    uint64_t top;
} koronos_kernel_stack;

/* Allocates eight supervisor RW/NX pages with an unmapped guard page below.
 * Mappings live in a shared supervisor subtree copied into every new root.
 * Mapping mutation is BSP-only until AP TLB shootdowns are implemented. */
int koronos_kernel_stack_allocate(koronos_kernel_stack *out_stack);
/* Refuses to release a stack currently installed as any initialized CPU's
 * TSS.RSP0. The caller must also ensure the task is no longer executing on it. */
int koronos_kernel_stack_release(const koronos_kernel_stack *stack);
int koronos_kernel_stack_self_test(void);

#ifdef __cplusplus
}
#endif
