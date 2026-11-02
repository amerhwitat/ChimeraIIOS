#pragma once
#include <stdint.h>
#include "chimera/kernel_stack.h"
#ifdef __cplusplus
extern "C" {
#endif
/* Create/release the guarded kernel stack owned by a process record.
 * Release must only be called after the task is no longer executing. */
int chimera_process_create_kernel_stack(uint32_t pid);
int chimera_process_release_kernel_stack(uint32_t pid);
#ifdef __cplusplus
}
#endif
