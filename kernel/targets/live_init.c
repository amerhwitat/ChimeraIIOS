#include "init_common.h"

__attribute__((noreturn, used)) void _start(void) {
    init_int80();
    const long pid = init_getpid();
    if (pid <= 0) init_exit(1);
    init_emit_readiness(pid);
    init_writestr("LIVE: native Koronos ring-3 console ready\n");
    init_writestr("LIVE: built-ins only; VFS, external ELF execution and graphics are not yet enabled\n");
    init_yield();
    init_writestr("LIVE: scheduler yield returned\n");

    char line[128];
    for (;;) {
        init_writestr("chimera> ");
        const long length = init_read_line(line, (long)sizeof(line));
        if (length < 0) {
            init_writestr("LIVE: console read failed\n");
            init_yield();
            continue;
        }
        if (init_command_common(line, pid)) {
            init_yield();
            continue;
        }
        if (init_text_equal(line, "help")) {
            init_writestr("help       list built-in commands\n");
            init_writestr("uname      show kernel identity\n");
            init_writestr("pid        show active process id\n");
            init_writestr("echo TEXT  print TEXT\n");
            init_writestr("clear      clear the text display\n");
            init_writestr("exit       leave the live console\n");
        } else if (init_text_equal(line, "uname")) {
            init_writestr("Koronos x86_64 — Chimera II OS\n");
        } else if (init_text_equal(line, "pid")) {
            init_writestr("pid=");
            init_write_uint((unsigned long)pid);
            init_writestr("\n");
        } else if (init_text_starts_with(line, "echo ")) {
            (void)init_write(1, line + 5, init_strlen(line + 5));
            init_writestr("\n");
        } else if (init_text_equal(line, "clear")) {
            for (int i = 0; i < 25; ++i) init_writestr("\n");
        } else if (init_text_equal(line, "exit")) {
            init_writestr("LIVE: console exit requested\n");
            init_exit(0);
        } else if (length) {
            init_writestr("LIVE: command unavailable; only the documented built-ins execute here\n");
        }
        init_yield();
    }
}
