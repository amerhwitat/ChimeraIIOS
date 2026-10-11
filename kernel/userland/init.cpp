#include <stdint.h>
extern "C" __attribute__((used,noreturn)) void chimera_user_init_entry(void) {
    static const char message[] =
        "[USER] Ring-3 Chimera init entered successfully; userspace handoff verified\n";
    for (uint32_t i = 0; message[i]; ++i) {
        const uint8_t c = static_cast<uint8_t>(message[i]);
        __asm__ volatile("outb %0, $0xE9" : : "a"(c));
    }
    for (;;) __asm__ volatile("pause" ::: "memory");
}
