#include "init_common.h"

/* Native Installer target: a storage/plan dry-run report. This payload does
 * not touch any block device and does not perform a real installation. */
__attribute__((noreturn, used)) void _start(void) {
    init_int80();

    const long pid = init_getpid();
    if (pid <= 0) init_exit(1);

    init_emit_readiness(pid);

    init_writestr("INSTALLER: storage plan (dry run)\n");
    init_writestr("INSTALLER: no block-device backend present\n");
    init_writestr("INSTALLER: no disk will be written; this is a report-only dry run\n");

    /* YIELD remains fail-closed until the process scheduler can switch
     * saved frames, kernel stacks, and address spaces. */
    init_yield();
    init_writestr("INSTALLER: scheduler tick count=");
    init_write_uint((unsigned long)init_time_ticks());
    init_writestr("\n");

    init_exit(0);
}
