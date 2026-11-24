#include "init_common.h"

/* Native Live target: a ring-3 text console session. Disk access stays in the
 * kernel; the payload asks for a measured installed-root handoff token through
 * the translated SYSCALL ABI and prints what the kernel returned. */
__attribute__((noreturn, used)) void _start(void) {
    init_int80();

    const long pid = init_getpid();
    if (pid <= 0) init_exit(1);

    init_emit_readiness(pid);

    init_writestr("LIVE: native console session banner\n");
    init_writestr("LIVE: ring-3 text console active (no graphical session)\n");

    char token[128];
    long n = 0;
    for (long i = 0; i < 128; ++i) token[i] = 0;
    n = init_vfs_handoff(token, 128);
    if (n > 0) {
        init_writestr("[LIVE ] installed-root handoff from kernel: ");
        (void)init_write(1, token, n);
    } else {
        init_writestr("LIVE: installed-root handoff unavailable\n");
    }

    init_yield();
    init_writestr("LIVE: scheduler yield returned\n");

    init_exit(0);
}
