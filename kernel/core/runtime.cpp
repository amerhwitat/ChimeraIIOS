#include <stddef.h>
#include <stdint.h>

// Freestanding C/C++ kernels cannot rely on the hosted libc implementations
// of these routines. GCC/Clang are nevertheless allowed to lower simple
// aggregate initialization and copy operations to libc ABI symbols such as
// memset. Provide the small, dependency-free implementations here so the
// Koronos link remains completely freestanding (-nostdlib).
extern "C" void *memset(void *dst, int value, size_t count) {
    uint8_t *p = static_cast<uint8_t *>(dst);
    const uint8_t v = static_cast<uint8_t>(value);
    for (size_t i = 0; i < count; ++i) p[i] = v;
    return dst;
}

extern "C" void *memcpy(void *dst, const void *src, size_t count) {
    uint8_t *d = static_cast<uint8_t *>(dst);
    const uint8_t *s = static_cast<const uint8_t *>(src);
    for (size_t i = 0; i < count; ++i) d[i] = s[i];
    return dst;
}

extern "C" void *memmove(void *dst, const void *src, size_t count) {
    uint8_t *d = static_cast<uint8_t *>(dst);
    const uint8_t *s = static_cast<const uint8_t *>(src);
    if (d == s || count == 0) return dst;
    if (d < s || d >= s + count) {
        for (size_t i = 0; i < count; ++i) d[i] = s[i];
    } else {
        for (size_t i = count; i != 0; --i) d[i - 1] = s[i - 1];
    }
    return dst;
}

extern "C" int memcmp(const void *lhs, const void *rhs, size_t count) {
    const uint8_t *a = static_cast<const uint8_t *>(lhs);
    const uint8_t *b = static_cast<const uint8_t *>(rhs);
    for (size_t i = 0; i < count; ++i) {
        if (a[i] < b[i]) return -1;
        if (a[i] > b[i]) return 1;
    }
    return 0;
}

extern "C" size_t strlen(const char *s) {
    if (!s) return 0;
    size_t n = 0;
    while (s[n]) ++n;
    return n;
}

extern "C" void __cxa_pure_virtual() {
    for (;;) {
        __asm__ volatile("cli; hlt");
    }
}

#include "chimera/scheduler.h"
#include "chimera/timer.h"
#include "chimera/watchdog.h"

extern "C" [[noreturn]] void koronos_idle_loop() {
    /*
     * Koronos has no hosted runtime to return to after koronos_boot().
     * The bootstrap vCPU therefore owns an explicit cooperative dispatch loop.
     * Advance the kernel timer from the same path so watchdogs and timers keep
     * progressing even before hardware timer IRQs are enabled.
     */
    for (;;) {
        const uint32_t ran = chimera_sched_run_parallel(0, 1);
        chimera_timer_tick(1);
        if (!ran) {
            __asm__ volatile("pause" ::: "memory");
        }
    }
}
