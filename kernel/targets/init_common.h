#pragma once
/* Freestanding ring-3 init payload helpers for native Koronos targets.
 *
 * These payloads enter through the DPL3 INT 0x80 gate once so Koronos can
 * prove CPL3 origin from the saved CS.RPL. Their subsequent SYSCALL calls use
 * the Linux x86-64 register ABI because koronos_syscall_user_dispatch()
 * translates Linux syscall numbers through linux_canonical().
 *
 * Linux x86-64 numbers used here: write=1, getpid=39, exit=60.
 * Do not pass CHM_SYS_* semantic IDs to this Linux compatibility entry.
 * No libc, no builtins, no stack protector, no CRT shim.
 */
#ifndef CHIMERA_TARGET_NAME
#error "CHIMERA_TARGET_NAME must be defined (live|installer|recovery)"
#endif

#define LINUX_X86_64_SYS_WRITE 1
#define LINUX_X86_64_SYS_GETPID 39
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

static long init_write(long fd, const char *buffer, long length) {
    return init_syscall3(LINUX_X86_64_SYS_WRITE, fd, (long)buffer, length);
}

__attribute__((noreturn)) static void init_exit(long code) {
    register long rax __asm__("rax") = LINUX_X86_64_SYS_EXIT;
    register long rdi __asm__("rdi") = code;
    __asm__ volatile("syscall"
                     : "+a"(rax)
                     : "D"(rdi)
                     : "rcx", "r11", "memory");
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
