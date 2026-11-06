#include "init_common.h"

/* Native Recovery target: a ring-3 diagnostic report only.
 * It does not mount repair media or modify filesystem state. */
__attribute__((noreturn, used)) void _start(void) {
    init_int80();

    const long pid = init_getpid();
    if (pid <= 0) init_exit(1);

    init_emit_readiness(pid);
    init_writestr("RECOVERY: diagnostics report\n");
    init_writestr("RECOVERY: ring-3 syscall ABI self-check complete\n");
    init_exit(0);
}
