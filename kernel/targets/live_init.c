#include "init_common.h"

/* Native Koronos live target: a real ring-3 interactive text console.
 * It currently provides built-in commands only; external ELF execution,
 * VFS-backed files and graphical desktop services remain separate targets. */
static int text_equal(const char *a, const char *b) {
    long i = 0;
    while (a[i] && b[i] && a[i] == b[i]) ++i;
    return a[i] == 0 && b[i] == 0;
}

static int text_starts_with(const char *text, const char *prefix) {
    long i = 0;
    while (prefix[i]) {
        if (text[i] != prefix[i]) return 0;
        ++i;
    }
    return 1;
}

__attribute__((noreturn, used)) void _start(void) {
    init_int80();

    const long pid = init_getpid();
    if (pid <= 0) init_exit(1);

    init_emit_readiness(pid);
    init_writestr("LIVE: native Koronos ring-3 console ready\n");
    init_writestr("LIVE: builtins are help, uname, pid, ticks, echo, clear, exit\n");

    char line[128];
    for (;;) {
        init_writestr("chimera> ");
        long length = init_read(0, line, (long)sizeof(line) - 1);
        if (length <= 0) {
            init_writestr("LIVE: console input unavailable; retrying\n");
            init_yield();
            continue;
        }
        if (line[length - 1] == '\n' || line[length - 1] == '\r') --length;
        line[length] = 0;

        if (text_equal(line, "help")) {
            init_writestr("help       show built-in commands\n");
            init_writestr("uname      show kernel and architecture\n");
            init_writestr("pid        show current process id\n");
            init_writestr("ticks      show kernel timer ticks\n");
            init_writestr("echo TEXT  print TEXT\n");
            init_writestr("clear      clear the text console\n");
            init_writestr("exit       return to the Koronos boot monitor\n");
        } else if (text_equal(line, "uname")) {
            init_writestr("Koronos x86_64 — Chimera II OS\n");
        } else if (text_equal(line, "pid")) {
            init_writestr("pid=");
            init_write_uint((unsigned long)pid);
            init_writestr("\n");
        } else if (text_equal(line, "ticks")) {
            init_writestr("ticks=");
            init_write_uint((unsigned long)init_time_ticks());
            init_writestr("\n");
        } else if (text_starts_with(line, "echo ")) {
            const long n = init_strlen(line + 5);
            (void)init_write(1, line + 5, n);
            init_writestr("\n");
        } else if (text_equal(line, "clear")) {
            for (int i = 0; i < 28; ++i) init_writestr("\n");
        } else if (text_equal(line, "exit")) {
            init_writestr("LIVE: leaving interactive console\n");
            init_exit(0);
        } else if (line[0]) {
            init_writestr("LIVE: command not found (this target currently exposes built-ins only)\n");
        }
        init_yield();
    }
}
