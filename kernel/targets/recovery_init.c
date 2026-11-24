#include "init_common.h"

/* Native Recovery target readiness probe. Kernel-mode recovery reads the
 * on-disk journal, verifies checksums and rolls back pending writes; this
 * ring-3 payload only proves the CPL3 syscall handshake. */
__attribute__((noreturn, used)) void _start(void) {
    init_int80();

    const long pid = init_getpid();
    if (pid <= 0) init_exit(1);

    init_emit_readiness(pid);

    init_writestr("RECOVERY: ring-3 probe active\n");
    init_writestr("RECOVERY: kernel-side journal replay selected by mode=recovery\n");
    init_writestr("RECOVERY: payload does not modify disk directly\n");

    init_yield();
    init_writestr("RECOVERY: scheduler yield returned\n");

    init_exit(0);
}
