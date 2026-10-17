#if defined(CHIMERA_TARGET_LIVE)
#define CHIMERA_TARGET_NAME "live"
#elif defined(CHIMERA_TARGET_INSTALLER)
#define CHIMERA_TARGET_NAME "installer"
#elif defined(CHIMERA_TARGET_RECOVERY)
#define CHIMERA_TARGET_NAME "recovery"
#else
#error "Select CHIMERA_TARGET_LIVE, CHIMERA_TARGET_INSTALLER, or CHIMERA_TARGET_RECOVERY"
#endif

static const char ready_message[] =
    "USERSPACE READY: " CHIMERA_TARGET_NAME " init pid=1\n";

__attribute__((noreturn, used)) void _start(void) {
    register long number __asm__("rax") = 9; /* CHM_SYS_WRITE */
    register long fd __asm__("rdi") = 1;
    register const char *buffer __asm__("rsi") = ready_message;
    register long length __asm__("rdx") = (long)(sizeof(ready_message) - 1u);
    __asm__ volatile("syscall"
                     : "+a"(number)
                     : "D"(fd), "S"(buffer), "d"(length)
                     : "rcx", "r11", "memory");

    /* This second write proves SYSRET returned to ring 3 after the first
       syscall; it is diagnostic output from the acceptance probe only. */
    static const char returned_message[] = "USERSPACE SYSCALL RETURNED TO RING3\\n";
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
    for (;;) __asm__ volatile("pause");
}
