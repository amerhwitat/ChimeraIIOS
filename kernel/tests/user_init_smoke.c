#ifndef CHIMERA_TARGET_NAME
#error "CHIMERA_TARGET_NAME must be supplied by the acceptance build"
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

    number = 1; /* CHM_SYS_EXIT */
    fd = 0;
    __asm__ volatile("syscall"
                     : "+a"(number)
                     : "D"(fd)
                     : "rcx", "r11", "memory");
    for (;;) __asm__ volatile("pause");
}
