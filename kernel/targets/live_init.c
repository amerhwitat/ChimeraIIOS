#include "init_common.h"

/* Native Live target: a ring-3 text console session. This is a freestanding
 * init payload, not a desktop shell; no graphical session is started. */
__attribute__((noreturn, used)) void _start(void) {
    init_int80();

    const long pid = init_getpid();
    if (pid <= 0) init_exit(1);

    init_emit_readiness(pid);

    init_writestr("LIVE: native console session banner\n");
    init_writestr("LIVE: ring-3 text console active (no graphical session)\n");

    /* Probe the yield ABI. Until saved-frame/stack/CR3 switching exists,
     * YIELD is expected to return ENOSYS; this is not scheduler readiness. */
    init_yield();
    init_writestr("LIVE: scheduler tick count=");
    init_write_uint((unsigned long)init_time_ticks());
    init_writestr("\n");

    init_exit(0);
}
