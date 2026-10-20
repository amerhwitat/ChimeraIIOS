#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include "chimera/compat.h"
#include "chimera/syscall.h"

static uint32_t yielded = 0;
extern "C" void chimera_sched_yield(void) { ++yielded; }
extern "C" uint64_t chimera_timer_now(void) { return 123456u; }

int main() {
    assert(chimera_compat_init(1u, 64u) == 0);
    assert(chimera_syscall_init() == 0);
    uint64_t rv = 0;
    uint64_t args[CHIMERA_SYSCALL_MAX_ARGS] = {};
    /* Never claim PID 1 until a scheduler/process identity binding exists. */
    assert(chimera_syscall_dispatch(CHM_ENTRY_NATIVE, 64, CHM_SYS_GETPID, args, &rv) == -1);
    assert(rv == (uint64_t)(-(int64_t)CHIMERA_ENOSYS));
    /* Exit cannot be a successful no-op; teardown must be wired first. */
    assert(chimera_syscall_dispatch(CHM_ENTRY_NATIVE, 64, CHM_SYS_EXIT, args, &rv) == -1);
    assert(rv == (uint64_t)(-(int64_t)CHIMERA_ENOSYS));
    assert(chimera_syscall_dispatch(CHM_ENTRY_NATIVE, 64, CHM_SYS_YIELD, args, &rv) == 0);
    assert(rv == 0 && yielded == 1);
    assert(chimera_syscall_dispatch(CHM_ENTRY_NATIVE, 64, CHM_SYS_TIME_TICKS, args, &rv) == 0);
    assert(rv == 123456u);
    assert(chimera_syscall_dispatch(CHM_ENTRY_NATIVE, 64, CHM_SYS_MMAP, args, &rv) == -1);
    assert(rv == (uint64_t)(-(int64_t)CHIMERA_ENOSYS));
    puts("syscall backend honesty regression tests: PASS");
    return 0;
}
