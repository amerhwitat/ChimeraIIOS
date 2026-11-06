#include "init_common.h"

static int shell_equals(const char *a, const char *b) {
    long i = 0;
    while (a[i] && b[i] && a[i] == b[i]) ++i;
    return a[i] == 0 && b[i] == 0;
}
static int shell_starts_with(const char *a, const char *prefix) {
    long i = 0;
    while (prefix[i]) { if (a[i] != prefix[i]) return 0; ++i; }
    return 1;
}
static void shell_help(void) {
    init_writestr("Koronos native ring-3 shell\n");
    init_writestr("Built-ins: help, echo TEXT, uname, id, uptime, status, clear, exit\n");
    init_writestr("Filesystem, package installation and repair commands are not enabled in this shell.\n");
}
__attribute__((noreturn, used)) void _start(void) {
    init_int80();
    const long pid = init_getpid();
    if (pid <= 0) init_exit(1);
    init_emit_readiness(pid);
    init_writestr("\nCHIMERA II OS — KORONOS INTERACTIVE CONSOLE\n");
    init_writestr("This is native Koronos ring-3 code, not a Linux BusyBox session.\n");
    shell_help();
    char line[128];
    for (;;) {
        init_writestr("\nkoronos> ");
        long n = init_read(0, line, (long)sizeof(line) - 1);
        if (n <= 0) {
            init_writestr("\n[console] input unavailable; retrying\n");
            init_yield();
            continue;
        }
        if (n >= (long)sizeof(line)) n = (long)sizeof(line) - 1;
        line[n] = 0;
        if (n > 0 && line[n - 1] == '\n') line[n - 1] = 0;
        if (shell_equals(line, "help") || shell_equals(line, "?")) {
            shell_help();
        } else if (shell_equals(line, "exit") || shell_equals(line, "quit")) {
            init_writestr("Leaving Koronos interactive console.\n");
            init_exit(0);
        } else if (shell_starts_with(line, "echo ")) {
            init_writestr(line + 5);
            init_writestr("\n");
        } else if (shell_equals(line, "uname")) {
            init_writestr("Koronos x86_64 (native Chimera syscall ABI)\n");
        } else if (shell_equals(line, "id")) {
            init_writestr("uid=0(root) pid=");
            init_write_uint((unsigned long)pid);
            init_writestr("\n");
        } else if (shell_equals(line, "uptime")) {
            init_writestr("kernel_ticks=");
            init_write_uint((unsigned long)init_time_ticks());
            init_writestr("\n");
        } else if (shell_equals(line, "status")) {
            init_writestr("Kernel: running; user ABI: Chimera; input: PS/2 polling; VFS: not mounted\n");
        } else if (shell_equals(line, "clear")) {
            init_writestr("\033[2J\033[H");
        } else if (line[0] == 0) {
            /* Empty command: redraw the prompt. */
        } else if (shell_equals(line, "ls") || shell_equals(line, "pwd") || shell_equals(line, "mount")) {
            init_writestr("VFS service is not connected to this native shell yet.\n");
        } else if (shell_equals(line, "install") || shell_equals(line, "repair")) {
            init_writestr("Disk-writing backend is not enabled; no storage was modified.\n");
        } else {
            init_writestr("Unknown built-in. Type help.\n");
        }
    }
}
