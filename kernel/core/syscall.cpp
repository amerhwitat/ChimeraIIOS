#include "chimera/syscall.h"
#include "chimera/compat.h"
#include "chimera/scheduler.h"
#include "chimera/timer.h"

namespace {
static volatile uint32_t g_initialized = 0;
static volatile uint32_t g_dispatched = 0;
static volatile uint32_t g_translated = 0;
static volatile uint32_t g_rejected = 0;
static volatile uint32_t g_last_os = 0;
static volatile uint32_t g_last_entry = 0;
static volatile uint32_t g_last_number = 0;
static volatile uint32_t g_last_canonical = 0xFFFFFFFFu;

static uint64_t error_value() {
    return (uint64_t)(-(int64_t)CHIMERA_ENOSYS);
}
}

extern "C" int chimera_syscall_init(void) {
    g_initialized = 1;
    return 0;
}

extern "C" int chimera_syscall_dispatch(uint32_t entry, uint32_t bitness, uint32_t number,
                                         const uint64_t *args, uint64_t *return_value) {
    if (!return_value) return -1;
    ++g_dispatched;

    chimera_syscall_identity id{};
    if (chimera_compat_recognize_syscall(entry, bitness, number, &id) != 0) {
        ++g_rejected;
        *return_value = error_value();
        return -1;
    }

    g_last_os = id.os;
    g_last_entry = id.entry;
    g_last_number = id.number;
    g_last_canonical = id.canonical;

    if (id.canonical != 0xFFFFFFFFu) ++g_translated;

    switch (id.canonical) {
        case CHM_SYS_GETPID:
            /*
             * A constant PID is not process identity. Until the trap path is
             * bound to a live, scheduled process context, fail closed rather
             * than allowing a probe to mistake the bootstrap task for init.
             */
            ++g_rejected;
            *return_value = error_value();
            return -1;
        case CHM_SYS_YIELD:
            /*
             * Callback dispatch is not a saved-register process context switch.
             * Do not report a successful user yield before that backend exists.
             */
            ++g_rejected;
            *return_value = error_value();
            return -1;
        case CHM_SYS_TIME_TICKS:
            *return_value = chimera_timer_now();
            return 0;
        case CHM_SYS_EXIT:
        case CHM_SYS_EXIT_GROUP:
            /*
             * Returning success without marking the current process exited,
             * waking waiters, and reclaiming its resources fabricates lifecycle
             * progress. Keep these calls unsupported until process ownership
             * and teardown are connected to the active syscall context.
             */
            (void)args;
            ++g_rejected;
            *return_value = error_value();
            return -1;
        default:
            ++g_rejected;
            *return_value = error_value();
            return -1;
    }
}

extern "C" int chimera_syscall_get_snapshot(chimera_syscall_snapshot *out) {
    if (!out) return -1;
    out->abi = CHIMERA_SYSCALL_ABI;
    out->initialized = g_initialized;
    out->dispatched = g_dispatched;
    out->translated = g_translated;
    out->rejected = g_rejected;
    out->last_os = g_last_os;
    out->last_entry = g_last_entry;
    out->last_number = g_last_number;
    out->last_canonical = g_last_canonical;
    return 0;
}
