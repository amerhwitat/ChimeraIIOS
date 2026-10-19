#include <stddef.h>

#if defined(CHIMERA_TARGET_LIVE)
#define CHIMERA_TARGET_NAME "live"
#elif defined(CHIMERA_TARGET_INSTALLER)
#define CHIMERA_TARGET_NAME "installer"
#elif defined(CHIMERA_TARGET_RECOVERY)
#define CHIMERA_TARGET_NAME "recovery"
#else
#error "Select CHIMERA_TARGET_LIVE, CHIMERA_TARGET_INSTALLER, or CHIMERA_TARGET_RECOVERY"
#endif

__attribute__((noreturn, used)) void _start(void) {
#if defined(CHIMERA_TEST_HANG)
    /* Deliberately hostile acceptance payload: no syscalls, no readiness,
       and no voluntary yield. Only a hardware IRQ-backed kernel deadline can
       regain control from this loop. */
    for (;;) __asm__ volatile("pause" ::: "memory");
#endif
    /* INT 0x80 enters a DPL3 IDT gate. The kernel acknowledgement is emitted
       only after checking the CPU-saved CS.RPL==3 and the active process CR3.
       This is distinct from SYSCALL, which does not save caller CS. */
    __asm__ volatile("int $0x80" ::: "memory");
    /* Ask the active kernel process record for our PID. Never bake PID 1 into
       the user image: this must keep working when process allocation changes. */
    register long number __asm__("rax") = 2; /* CHM_SYS_GETPID */
    __asm__ volatile("syscall"
                     : "+a"(number)
                     :
                     : "rcx", "r11", "memory");
    if (number <= 0) {
        number = 1; /* CHM_SYS_EXIT */
        register long failure_code __asm__("rdi") = 1;
        __asm__ volatile("syscall"
                         : "+a"(number)
                         : "D"(failure_code)
                         : "rcx", "r11", "memory");
        for (;;) __asm__ volatile("pause" ::: "memory");
    }

    char ready_message[96];
    const char prefix[] = "USERSPACE PROBE READY: " CHIMERA_TARGET_NAME " init pid=";
    size_t used = 0;
    for (size_t i = 0; i < sizeof(prefix) - 1u; ++i)
        ready_message[used++] = prefix[i];

    char reversed[20];
    size_t digits = 0;
    unsigned long pid = (unsigned long)number;
    while (pid && digits < sizeof(reversed)) {
        reversed[digits++] = (char)('0' + (pid % 10u));
        pid /= 10u;
    }
    if (digits == 0 || used + digits + 2u > sizeof(ready_message)) {
        number = 1;
        register long failure_code __asm__("rdi") = 1;
        __asm__ volatile("syscall"
                         : "+a"(number)
                         : "D"(failure_code)
                         : "rcx", "r11", "memory");
        for (;;) __asm__ volatile("pause" ::: "memory");
    }
    while (digits) ready_message[used++] = reversed[--digits];
    ready_message[used++] = '\n';

    number = 9; /* CHM_SYS_WRITE */
    register long fd __asm__("rdi") = 1;
    register const char *buffer __asm__("rsi") = ready_message;
    register long length __asm__("rdx") = (long)used;
    __asm__ volatile("syscall"
                     : "+a"(number)
                     : "D"(fd), "S"(buffer), "d"(length)
                     : "rcx", "r11", "memory");

    /* This second write proves the native syscall returned to ring 3. */
    static const char returned_message[] = "USERSPACE PROBE SYSCALL RETURNED TO RING3\n";
    number = 9;
    fd = 1;
    buffer = returned_message;
    length = (long)(sizeof(returned_message) - 1u);
    __asm__ volatile("syscall"
                     : "+a"(number)
                     : "D"(fd), "S"(buffer), "d"(length)
                     : "rcx", "r11", "memory");

    number = 1; /* CHM_SYS_EXIT */
    fd = 0;
    __asm__ volatile("syscall"
                     : "+a"(number)
                     : "D"(fd)
                     : "rcx", "r11", "memory");
    for (;;) __asm__ volatile("pause" ::: "memory");
}
