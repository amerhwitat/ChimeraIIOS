#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define KORONOS_KERNEL_STACK_ABI 1u

typedef struct koronos_kernel_stack {
    uint32_t slot;
    uint32_t generation;
    uint64_t base;
    uint64_t top;
} koronos_kernel_stack;

/* Eight supervisor RW/NX pages with an unmapped guard page below. Mappings
 * are shared by every process root. Mutations are BSP-only until AP TLB
 * shootdown acknowledgements are implemented. */
int koronos_kernel_stack_allocate(koronos_kernel_stack *out_stack);
/* Refuses release while the stack is installed as any initialized CPU's
 * TSS.RSP0. The caller must also ensure the task is no longer executing on it. */
int koronos_kernel_stack_release(const koronos_kernel_stack *stack);
int koronos_kernel_stack_self_test(void);

#ifdef __cplusplus
}
#endif
