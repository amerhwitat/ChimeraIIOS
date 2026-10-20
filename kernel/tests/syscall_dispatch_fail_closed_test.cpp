#include "chimera/syscall.h"
#include "chimera/compat.h"
#include <stdint.h>
#include <stdio.h>

extern "C" int chimera_compat_recognize_syscall(uint32_t entry, uint32_t bitness, uint32_t number, chimera_syscall_identity *out) {
    if (!out) return -1;
    *out = {};
    out->os = CHM_OS_LINUX; out->entry = entry; out->bitness = bitness; out->number = number;
    switch (number) {
        case 39: out->canonical = CHM_SYS_GETPID; return 0;
        case 60: out->canonical = CHM_SYS_EXIT; return 0;
        case 231: out->canonical = CHM_SYS_EXIT_GROUP; return 0;
        case 24: out->canonical = CHM_SYS_YIELD; return 0;
        case 228: out->canonical = CHM_SYS_TIME_TICKS; return 0;
        default: out->canonical = 0xFFFFFFFFu; return 0;
    }
}
extern "C" void chimera_sched_yield(void) {}
extern "C" uint64_t chimera_timer_now(void) { return 1234; }

static int check(bool ok, const char *message) {
    if (!ok) std::fprintf(stderr, "FAIL: %s\n", message);
    return ok ? 0 : 1;
}
int main() {
    int failures = 0; uint64_t value = 0; const uint64_t args[6] = {};
    failures += check(chimera_syscall_init() == 0, "init succeeds");
    const uint64_t enosys = static_cast<uint64_t>(-static_cast<int64_t>(CHIMERA_ENOSYS));
    failures += check(chimera_syscall_dispatch(CHM_ENTRY_X86_SYSCALL, 64, 39, args, &value) == -1 && value == enosys, "GETPID rejected without process context");
    failures += check(chimera_syscall_dispatch(CHM_ENTRY_X86_SYSCALL, 64, 60, args, &value) == -1 && value == enosys, "EXIT rejected without teardown");
    failures += check(chimera_syscall_dispatch(CHM_ENTRY_X86_SYSCALL, 64, 231, args, &value) == -1 && value == enosys, "EXIT_GROUP rejected without teardown");
    failures += check(chimera_syscall_dispatch(CHM_ENTRY_X86_SYSCALL, 64, 228, args, &value) == 0 && value == 1234, "timer syscall returns timer value");
    failures += check(chimera_syscall_dispatch(CHM_ENTRY_X86_SYSCALL, 64, 9999, args, &value) == -1 && value == enosys, "unsupported syscall fails closed");
    failures += check(chimera_syscall_dispatch(CHM_ENTRY_X86_SYSCALL, 64, 39, args, nullptr) == -1, "null return pointer rejected");
    chimera_syscall_snapshot snapshot{};
    failures += check(chimera_syscall_get_snapshot(&snapshot) == 0 && snapshot.initialized == 1 && snapshot.rejected >= 4, "snapshot tracks rejected calls");
    if (failures) return 1;
    std::puts("PASS: syscall dispatch fail-closed regression tests");
    return 0;
}
