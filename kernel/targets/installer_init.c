#include "init_common.h"

/* Native Installer target: an explicitly non-destructive storage-plan report.
 * It does not select partitions, write a disk, install a bootloader or reboot. */
__attribute__((noreturn, used)) void _start(void) {
    init_int80();

    const long pid = init_getpid();
    if (pid <= 0) init_exit(1);

    init_emit_readiness(pid);
    init_writestr("INSTALLER: storage plan (dry run)\n");
    init_writestr("INSTALLER: no block-device write backend is available\n");
    init_writestr("INSTALLER: no disk will be modified; installation is not performed\n");
    init_exit(0);
}
