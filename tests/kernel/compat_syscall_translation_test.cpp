#include <cassert>
#include <cstdint>
#include "chimera/compat.h"
#include "chimera/syscall.h"

int main() {
    chimera_syscall_identity id{};

    // Linux x86-64 syscall ABI used by the Octavian musl init payload.
    assert(chimera_compat_recognize_syscall(
        CHM_ENTRY_X86_SYSCALL, 64u, 39u, &id) == 0);
    assert(id.os == CHM_OS_LINUX);
    assert(id.canonical == CHM_SYS_GETPID);

    assert(chimera_compat_recognize_syscall(
        CHM_ENTRY_X86_SYSCALL, 64u, 1u, &id) == 0);
    assert(id.canonical == CHM_SYS_WRITE);
    assert(chimera_compat_recognize_syscall(
        CHM_ENTRY_X86_SYSCALL, 64u, 0u, &id) == 0);
    assert(id.canonical == CHM_SYS_READ);

    assert(chimera_compat_recognize_syscall(
        CHM_ENTRY_X86_SYSCALL, 64u, 24u, &id) == 0);
    assert(id.canonical == CHM_SYS_YIELD);

    assert(chimera_compat_recognize_syscall(
        CHM_ENTRY_X86_SYSCALL, 64u, 0x43484D04u, &id) == 0);
    assert(id.canonical == CHM_SYS_TIME_TICKS);

    assert(chimera_compat_recognize_syscall(
        CHM_ENTRY_X86_SYSCALL, 64u, 60u, &id) == 0);
    assert(id.canonical == CHM_SYS_EXIT);

    assert(chimera_compat_recognize_syscall(
        CHM_ENTRY_X86_SYSCALL, 64u, 231u, &id) == 0);
    assert(id.canonical == CHM_SYS_EXIT_GROUP);

    // Process creation, exec and mount are intentionally not mapped until
    // their native process/VFS implementations exist.
    assert(chimera_compat_recognize_syscall(
        CHM_ENTRY_X86_SYSCALL, 64u, 57u, &id) == 0);
    assert(id.canonical == 0xFFFFFFFFu);
    assert(chimera_compat_recognize_syscall(
        CHM_ENTRY_X86_SYSCALL, 64u, 59u, &id) == 0);
    assert(id.canonical == 0xFFFFFFFFu);
    assert(chimera_compat_recognize_syscall(
        CHM_ENTRY_X86_SYSCALL, 64u, 165u, &id) == 0);
    assert(id.canonical == 0xFFFFFFFFu);

    return 0;
}
