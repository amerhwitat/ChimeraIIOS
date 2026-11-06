#include "init_common.h"

/* Native Live target: a ring-3 text console session. This freestanding
 * bootstrap is not the graphical Aurora desktop or a complete init manager. */
__attribute__((noreturn, used)) void _start(void) {
    init_int80();

    const long pid = init_getpid();
    if (pid <= 0) init_exit(1);

    init_emit_readiness(pid);
    init_writestr("LIVE: native console session banner\n");
    init_writestr("LIVE: ring-3 text console active; graphical Aurora is not started\n");
    init_exit(0);
}
