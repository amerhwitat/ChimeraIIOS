#include <stdint.h>
#include "../include/chimera/scheduler.h"
#include "../include/chimera/multiboot_modules.h"

namespace {
static volatile uint32_t watchdog_runs;
static volatile uint32_t watchdog_idle_reported;

static void vga_text(uint32_t row, uint32_t col, const char *text) {
    volatile uint16_t *v = (volatile uint16_t *)0xB8000;
    for (uint32_t i = 0; text[i] && col + i < 80; ++i)
        v[row * 80 + col + i] = (uint16_t)(0x0F00u | (uint8_t)text[i]);
}

static void vga_hex(uint32_t row, uint32_t col, uint32_t value) {
    static const char h[] = "0123456789ABCDEF";
    volatile uint16_t *v = (volatile uint16_t *)0xB8000;
    for (uint32_t i = 0; i < 8 && col + i < 80; ++i)
        v[row * 80 + col + i] =
            (uint16_t)(0x0F00u | (uint8_t)h[(value >> (28 - 4 * i)) & 15u]);
}

static void debugcon_write(const char *text) {
    if (!text) return;
    while (*text) {
        const uint8_t byte = (uint8_t)*text++;
        __asm__ volatile("outb %0, $0xE9" : : "a"(byte));
    }
    __asm__ volatile("outb %0, $0xE9" : : "a"((uint8_t)'\n'));
}

static void watchdog_task(void *) {
    ++watchdog_runs;
    const uint32_t ready = chimera_sched_runnable_count();
    if (ready == 0 && !watchdog_idle_reported) {
        watchdog_idle_reported = 1;
        vga_text(23, 0, "KORONOS WATCHDOG: no READY service tasks; checking runtime");
        debugcon_write("[WDOG] Scheduler is alive but no other service task is READY");
        debugcon_write("[WDOG] Userspace handoff has not produced a runnable task");
    } else if (ready != 0 && watchdog_idle_reported) {
        watchdog_idle_reported = 0;
        vga_text(23, 0, "KORONOS WATCHDOG: runnable services detected");
        debugcon_write("[WDOG] Runnable service activity resumed");
    }

    // Keep a visible heartbeat even after all one-shot bootstrap tasks block.
    // This is a diagnostic safety net, not a substitute for a userspace loader.
    if ((watchdog_runs & 0x0000FFFFu) == 0) {
        vga_text(24, 0, "KORONOS WDOG ALIVE RUN=");
        vga_hex(24, 23, watchdog_runs);
        vga_text(24, 34, "READY=");
        vga_hex(24, 40, ready);
        vga_text(24, 50, "MB2=");
        vga_hex(24, 54, chimera_multiboot_module_count());
    }
}
}

extern "C" void koronos_idle_loop(void) {
    // The low-priority watchdog remains schedulable when all bootstrap workers
    // have blocked, so an empty READY queue is diagnosed instead of looking like
    // a frozen Koronos boot. It never claims that Aurora/userspace was launched.
    if (chimera_sched_submit(watchdog_task, nullptr, 1) < 0) {
        vga_text(23, 0, "KORONOS WATCHDOG REGISTRATION FAILED");
        debugcon_write("[WDOG] ERROR: could not register runtime watchdog task");
    }

    uint32_t spin = 0;
    for (;;) {
        const uint32_t dispatched = chimera_sched_run_once(0);
        ++spin;
        if ((spin & 0x0000FFFFu) == 0) {
            vga_text(24, 0, "KORONOS SCHEDULER ALIVE");
            vga_hex(24, 25, spin);
            vga_text(24, 34, "RUN");
            vga_hex(24, 38, dispatched);
            vga_text(24, 47, "READY");
            vga_hex(24, 53, chimera_sched_runnable_count());
            vga_text(24, 62, "MB2");
            vga_hex(24, 66, chimera_multiboot_module_count());
        }
#if defined(__x86_64__) || defined(__i386__)
        __asm__ volatile("pause" ::: "memory");
#elif defined(__aarch64__)
        __asm__ volatile("yield" ::: "memory");
#elif defined(__riscv)
        __asm__ volatile("nop" ::: "memory");
#else
        __asm__ volatile("" ::: "memory");
#endif
    }
}
