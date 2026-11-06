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
        CHM_ENTRY_X86_SYSCALL, 64u, 60u, &id) == 0);
    assert(id.canonical == CHM_SYS_EXIT);

    assert(chimera_compat_recognize_syscall(
        CHM_ENTRY_X86_SYSCALL, 64u, 231u, &id) == 0);
    assert(id.canonical == CHM_SYS_EXIT_GROUP);

    // Native Koronos targets use stable Chimera IDs directly. They must not
    // be confused with Linux numbers that happen to have the same integer.
    uint32_t canonical = 0xFFFFFFFFu;
    assert(chimera_compat_resolve_user_syscall(
        CHM_USER_ABI_NATIVE, CHM_ENTRY_X86_SYSCALL, 64u,
        CHM_SYS_EXIT, &canonical) == 0);
    assert(canonical == CHM_SYS_EXIT);
    assert(chimera_compat_resolve_user_syscall(
        CHM_USER_ABI_NATIVE, CHM_ENTRY_X86_SYSCALL, 64u,
        CHM_SYS_WRITE, &canonical) == 0);
    assert(canonical == CHM_SYS_WRITE);
    assert(chimera_compat_resolve_user_syscall(
        CHM_USER_ABI_LINUX, CHM_ENTRY_X86_SYSCALL, 64u,
        1u, &canonical) == 0);
    assert(canonical == CHM_SYS_WRITE);
    assert(chimera_compat_resolve_user_syscall(
        CHM_USER_ABI_LINUX, CHM_ENTRY_X86_SYSCALL, 64u,
        2u, &canonical) == 0);
    assert(canonical != CHM_SYS_GETPID); // Linux syscall 2 is open, not getpid.
    assert(chimera_compat_resolve_user_syscall(
        CHM_USER_ABI_LINUX, CHM_ENTRY_X86_SYSCALL, 64u,
        39u, &canonical) == 0);
    assert(canonical == CHM_SYS_GETPID);
    assert(chimera_compat_resolve_user_syscall(
        CHM_USER_ABI_LINUX, CHM_ENTRY_X86_SYSCALL, 64u,
        0u, &canonical) == 0);
    assert(canonical == CHM_SYS_READ);

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
