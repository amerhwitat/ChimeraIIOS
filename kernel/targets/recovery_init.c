#include "init_common.h"

/* Native Recovery target: a diagnostics report from ring 3. This payload only
 * inspects the syscall ABI and reports its own state; it repairs nothing. */
__attribute__((noreturn, used)) void _start(void) {
    init_int80();

    const long pid = init_getpid();
    if (pid <= 0) init_exit(1);

    init_emit_readiness(pid);

    init_writestr("RECOVERY: diagnostics report\n");
    init_writestr("RECOVERY: ring-3 syscall ABI self-check complete\n");

    /* YIELD remains fail-closed until the process scheduler can switch
     * saved frames, kernel stacks, and address spaces. */
    init_yield();
    init_writestr("RECOVERY: scheduler tick count=");
    init_write_uint((unsigned long)init_time_ticks());
    init_writestr("\n");

    init_exit(0);
}
