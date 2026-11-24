#include "init_common.h"

/* Native Installer target readiness probe. The real partition/format/journal
 * work runs in kernel mode when mode=installer is selected; this ring-3
 * payload only proves the CPL3 syscall handshake for the selected target. */
__attribute__((noreturn, used)) void _start(void) {
    init_int80();

    const long pid = init_getpid();
    if (pid <= 0) init_exit(1);

    init_emit_readiness(pid);

    init_writestr("INSTALLER: ring-3 probe active\n");
    init_writestr("INSTALLER: kernel-side GPT/KoronosFS installer selected by mode=installer\n");
    init_writestr("INSTALLER: payload does not write disk directly\n");

    init_yield();
    init_writestr("INSTALLER: scheduler yield returned\n");

    init_exit(0);
}
