#include "chimera/native_stack.h"
#include "chimera/install.h"

/* Phase dispatcher for the real installer/recovery implementation in
 * koronos_install.cpp. Multiboot module cmdlines select the phase; all durable
 * state lives in GPT partitions and KoronosFS v2 files. */

namespace {
static inline void out8_(uint16_t port, uint8_t value) {
    __asm__ volatile("outb %0, %1" : : "a"(value), "Nd"(port));
}
static void debug_(const char *text) {
    while (*text) out8_(0xE9, static_cast<uint8_t>(*text++));
    out8_(0xE9, '\n');
}
static void debug_u32_(const char *label, uint32_t value) {
    char line[80];
    uint32_t pos = 0;
    while (label[pos] && pos + 1u < sizeof(line)) { line[pos] = label[pos]; ++pos; }
    char reversed[12];
    uint32_t n = 0;
    if (!value) reversed[n++] = '0';
    while (value && n < sizeof(reversed)) { reversed[n++] = static_cast<char>('0' + value % 10u); value /= 10u; }
    while (n && pos + 1u < sizeof(line)) line[pos++] = reversed[--n];
    line[pos] = 0;
    debug_(line);
}
} // namespace

extern "C" int koronos_install_recovery_selftest(void) {
    const koronos_install_phase_t phase = koronos_install_selected_phase();
    if (phase == KORONOS_PHASE_NONE) {
        debug_("[INS ] SKIPPED: no install target module");
        return 0;
    }
    if (koronos_block_init() != 0) {
        debug_("[INS ] SELFTEST FAIL: block backend unavailable");
        return -1;
    }
    debug_u32_("[INS ] mode_selected=", static_cast<uint32_t>(phase));
    if (koronos_install_run_phase(phase) != 0) {
        debug_("[INS ] SELFTEST FAIL");
        return -1;
    }
    debug_("[INS ] SELFTEST PASS");
    if (phase == KORONOS_PHASE_INSTALLER || phase == KORONOS_PHASE_INSTALLED ||
        phase == KORONOS_PHASE_RECOVERY) {
        debug_("[INS ] REBOOTING FOR NEXT PHASE");
        koronos_native_machine_reset();
    }
    return 0;
}
