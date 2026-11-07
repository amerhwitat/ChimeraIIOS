#pragma once
/* Freestanding ring-3 init payload helpers for native Koronos targets.
 *
 * These payloads enter through the Linux x86-64 SYSCALL compatibility ABI:
 *   getpid=39, write=1, sched_yield=24, exit=60.
 * Do not pass Chimera's semantic syscall IDs directly to SYSCALL: that entry
 * translates Linux syscall numbers before dispatch. No libc, CRT or stack
 * protector is linked into these freestanding payloads.
 *
 * The DPL3 INT 0x80 gate is entered first so the kernel can prove the call
 * originated at CPL 3 from the saved CS.RPL; the readiness line itself is
 * emitted from user code, never from the kernel.
 */

#ifndef CHIMERA_TARGET_NAME
#error "CHIMERA_TARGET_NAME must be defined (live|installer|recovery)"
#endif

#define LINUX_X86_64_SYS_READ 0
#define LINUX_X86_64_SYS_WRITE 1
#define LINUX_X86_64_SYS_GETPID 39
#define LINUX_X86_64_SYS_YIELD 24
#define LINUX_X86_64_SYS_EXIT 60

static void init_int80(void) {
    __asm__ volatile("int $0x80" ::: "memory");
}

static long init_syscall1(long number) {
    register long rax __asm__("rax") = number;
    __asm__ volatile("syscall"
                     : "+a"(rax)
                     :
                     : "rcx", "r11", "memory");
    return rax;
}

static long init_syscall3(long number, long arg1, long arg2, long arg3) {
    register long rax __asm__("rax") = number;
    register long rdi __asm__("rdi") = arg1;
    register long rsi __asm__("rsi") = arg2;
    register long rdx __asm__("rdx") = arg3;
    __asm__ volatile("syscall"
                     : "+a"(rax)
                     : "D"(rdi), "S"(rsi), "d"(rdx)
                     : "rcx", "r11", "memory");
    return rax;
}

static long init_getpid(void) {
    return init_syscall1(LINUX_X86_64_SYS_GETPID);
}
static void init_yield(void) {
    (void)init_syscall1(LINUX_X86_64_SYS_YIELD);
    __asm__ volatile("pause" ::: "memory");
}
static long init_read(long fd, char *buffer, long length) {
    return init_syscall3(LINUX_X86_64_SYS_READ, fd, (long)buffer, length);
}
static long init_write(long fd, const char *buffer, long length) {
    return init_syscall3(LINUX_X86_64_SYS_WRITE, fd, (long)buffer, length);
}
static void init_write_uint(unsigned long value) {
    char reversed[24];
    char forward[24];
    long digits = 0;
    long used = 0;
    if (value == 0) reversed[digits++] = '0';
    else while (value && digits < (long)sizeof(reversed)) {
        reversed[digits++] = (char)('0' + (value % 10u));
        value /= 10u;
    }
    while (digits) forward[used++] = reversed[--digits];
    (void)init_write(1, forward, used);
}
static int init_text_equal(const char *a, const char *b) {
    long i = 0;
    while (a[i] && b[i] && a[i] == b[i]) ++i;
    return a[i] == 0 && b[i] == 0;
}
static int init_text_starts_with(const char *text, const char *prefix) {
    long i = 0;
    while (prefix[i]) {
        if (text[i] != prefix[i]) return 0;
        ++i;
    }
    return 1;
}
static long init_read_line(char *buffer, long capacity) {
    if (!buffer || capacity < 2) return -22;
    long n = init_read(0, buffer, capacity - 1);
    if (n <= 0) return n;
    while (n > 0 && (buffer[n - 1] == '\n' || buffer[n - 1] == '\r')) --n;
    buffer[n] = 0;
    return n;
}

__attribute__((noreturn)) static void init_exit(long code) {
    register long rax __asm__("rax") = LINUX_X86_64_SYS_EXIT;
    register long rdi __asm__("rdi") = code;
    __asm__ volatile("syscall" : "+a"(rax) : "D"(rdi) : "rcx", "r11", "memory");
    /* The exit syscall must not return to ring 3. */
    for (;;) __asm__ volatile("pause" ::: "memory");
}

static long init_strlen(const char *s) {
    long n = 0;
    while (s[n]) ++n;
    return n;
}

static void init_writestr(const char *s) {
    (void)init_write(1, s, init_strlen(s));
}

static void init_emit_readiness(long pid) {
    char message[96];
    long used = 0;
    long i;
    const char *p = "USERSPACE READY: target=";
    for (i = 0; p[i]; ++i) message[used++] = p[i];
    for (i = 0; CHIMERA_TARGET_NAME[i]; ++i) message[used++] = CHIMERA_TARGET_NAME[i];
    p = " init_pid=";
    for (i = 0; p[i]; ++i) message[used++] = p[i];

    char reversed[20];
    long digits = 0;
    unsigned long value = (unsigned long)pid;
    if (value == 0) {
        reversed[digits++] = '0';
    } else {
        while (value && digits < (long)sizeof(reversed)) {
            reversed[digits++] = (char)('0' + (value % 10u));
            value /= 10u;
        }
    }
    while (digits) message[used++] = reversed[--digits];
    message[used++] = '\n';
    (void)init_write(1, message, used);
}
