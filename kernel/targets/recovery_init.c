#include "init_common.h"

__attribute__((noreturn, used)) void _start(void) {
    init_int80();
    const long pid = init_getpid();
    if (pid <= 0) init_exit(1);
    init_emit_readiness(pid);
    init_writestr("RECOVERY: pid=");
    init_write_uint((unsigned long)pid);
    init_writestr("\n");
    init_writestr("RECOVERY: native Koronos recovery console\n");
    init_writestr("RECOVERY: diagnostics are read-only; filesystem repair awaits VFS and block drivers\n");
    char line[128];
    for (;;) {
        init_writestr("recovery> ");
        const long length = init_read_line(line, (long)sizeof(line));
        if (length <= 0) {
            init_writestr("RECOVERY: stdin reached EOF; no keyboard/TTY input provider is registered\n");
            init_exit(0);
        }
        if (init_command_common(line, pid)) {
            init_yield();
            continue;
        }
        if (init_text_equal(line, "help")) {
            init_writestr("help        show commands\nstatus      show recovery backend status\ncheck       run the available ABI self-check\nrepair      report repair capability\nexit        return to the boot monitor\n");
        } else if (init_text_equal(line, "status")) {
            init_writestr("RECOVERY: console and syscall ABI available; VFS/block-device repair backends are not registered\n");
        } else if (init_text_equal(line, "check")) {
            init_writestr("RECOVERY: ring-3 process and read/write syscall paths are active\n");
            init_writestr("RECOVERY: filesystem and storage integrity checks are not yet implemented\n");
        } else if (init_text_equal(line, "repair")) {
            init_writestr("RECOVERY: repair not available; no filesystem or block-device writes will be attempted\n");
        } else if (init_text_starts_with(line, "repair ")) {
            init_writestr("RECOVERY: repair requests are disabled until storage and filesystem backends exist\n");
        } else if (init_text_equal(line, "exit")) {
            init_writestr("RECOVERY: leaving safe console\n");
            init_exit(0);
        } else if (length) {
            init_writestr("RECOVERY: unknown command\n");
        }
        init_yield();
    }
}
