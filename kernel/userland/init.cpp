#include <stdint.h>
static volatile uint8_t user_state = 1;
extern "C" __attribute__((used,noreturn)) void chimera_user_init_entry(void) {
    static const char message[] =
        "[USER] Ring-3 Chimera init entered successfully; userspace handoff verified\n";
    uint64_t syscall_number = 1;
    __asm__ volatile("int $0x80"
                     : "+a"(syscall_number)
                     : "D"(message), "S"(sizeof(message)-1u)
                     : "rcx", "r11", "memory");
    for (;;) {
        user_state ^= 1u; // Exercise the writable user-data mapping as well.
        __asm__ volatile("pause" ::: "memory");
    }
}
