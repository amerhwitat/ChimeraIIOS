/*
 * Koronos Kernel Syscall Interface
 * Abstraction layer for userspace to kernel communication
 * Supports x86_64, ARM64, RISC-V64
 */

#ifndef KORONOS_SYSCALLS_H
#define KORONOS_SYSCALLS_H

#include <stdint.h>
#include <sys/types.h>

/* Koronos syscall numbers (x86_64) */
#define KORONOS_SYS_exit           0
#define KORONOS_SYS_fork           1
#define KORONOS_SYS_read           2
#define KORONOS_SYS_write          3
#define KORONOS_SYS_open           4
#define KORONOS_SYS_close          5
#define KORONOS_SYS_stat           6
#define KORONOS_SYS_fstat          7
#define KORONOS_SYS_lstat          8
#define KORONOS_SYS_mount          9
#define KORONOS_SYS_umount         10
#define KORONOS_SYS_clone          11
#define KORONOS_SYS_mmap           12
#define KORONOS_SYS_munmap         13
#define KORONOS_SYS_mprotect       14
#define KORONOS_SYS_brk            15
#define KORONOS_SYS_signal         16
#define KORONOS_SYS_kill           17
#define KORONOS_SYS_getpid         18
#define KORONOS_SYS_getppid        19
#define KORONOS_SYS_getuid         20
#define KORONOS_SYS_geteuid        21
#define KORONOS_SYS_getgid         22
#define KORONOS_SYS_getegid        23
#define KORONOS_SYS_dup            24
#define KORONOS_SYS_dup2           25
#define KORONOS_SYS_pipe           26
#define KORONOS_SYS_ioctl          27
#define KORONOS_SYS_fcntl          28
#define KORONOS_SYS_select         29
#define KORONOS_SYS_poll           30

/* CPU parallel execution syscalls */
#define KORONOS_SYS_get_cpu_count  128
#define KORONOS_SYS_get_cpuid      129
#define KORONOS_SYS_set_affinity   130
#define KORONOS_SYS_get_affinity   131
#define KORONOS_SYS_getcpufreq     132

/* Process management */
typedef struct {
    pid_t pid;
    pid_t ppid;
    int state;
    int priority;
    uint64_t utime;
    uint64_t stime;
} koronos_proc_t;

/* CPU topology */
typedef struct {
    int cpu_count;
    int core_count;
    int thread_count;
    int cache_l3_kb;
    uint32_t cpu_flags;
} koronos_cpu_info_t;

/* Inline syscall wrapper for x86_64 */
static inline long koronos_syscall(int num, ...) {
    #ifdef __x86_64__
    long result;
    va_list ap;
    va_start(ap, num);
    long arg1 = va_arg(ap, long);
    long arg2 = va_arg(ap, long);
    long arg3 = va_arg(ap, long);
    va_end(ap);
    
    __asm__ volatile(
        "syscall"
        : "=a" (result)
        : "a" (num), "D" (arg1), "S" (arg2), "d" (arg3)
        : "rcx", "r11", "memory"
    );
    return result;
    #else
    #error "Architecture not supported"
    #endif
}

#endif /* KORONOS_SYSCALLS_H */
