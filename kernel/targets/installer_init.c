#include "init_common.h"

__attribute__((noreturn, used)) void _start(void) {
    init_int80();
    const long pid = init_getpid();
    if (pid <= 0) init_exit(1);
    init_emit_readiness(pid);
    init_writestr("INSTALLER: pid=");
    init_write_uint((unsigned long)pid);
    init_writestr("\n");
    init_writestr("INSTALLER: native Koronos installer console\n");
    init_writestr("INSTALLER: disk operations remain disabled until block-device and VFS backends pass acceptance\n");
    char line[128];
    for (;;) {
        init_writestr("installer> ");
        const long length = init_read_line(line, (long)sizeof(line));
        if (length < 0) { init_writestr("INSTALLER: input error\n"); init_yield(); continue; }
        if (init_text_equal(line, "help")) {
            init_writestr("help    show commands\nstatus  show available install backends\nplan    print the non-writing installation plan\nexit    return to the boot monitor\n");
        } else if (init_text_equal(line, "status")) {
            init_writestr("INSTALLER: no block-device or filesystem backend is registered; no disks are writable\n");
        } else if (init_text_equal(line, "plan")) {
            init_writestr("PLAN 1: enumerate disks (not available)\nPLAN 2: validate partition layout (not available)\nPLAN 3: create filesystems (not available)\nPLAN 4: install Koronos and boot files (not available)\nPLAN 5: verify boot entries (not available)\nPLAN STATUS: report-only; no disk writes performed\n");
        } else if (init_text_starts_with(line, "plan ")) {
            init_writestr("INSTALLER: usage is plan; no disk operation is available\n");
        } else if (init_text_equal(line, "exit")) {
            init_writestr("INSTALLER: leaving safe console\n");
            init_exit(0);
        } else if (length) {
            init_writestr("INSTALLER: command unavailable; no destructive action is exposed\n");
        }
        init_yield();
    }
}
