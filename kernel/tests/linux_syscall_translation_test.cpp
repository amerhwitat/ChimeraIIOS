#include <cstdio>
#include "chimera/compat.h"
#include "chimera/syscall.h"

namespace {
int failures = 0;
void expect(uint32_t entry, uint32_t bits, uint32_t linux_number,
            uint32_t expected, const char *label) {
    chimera_syscall_identity id{};
    const int rc = chimera_compat_recognize_syscall(entry, bits, linux_number, &id);
    if (rc != 0 || id.os != CHM_OS_LINUX || id.canonical != expected) {
        std::fprintf(stderr,
            "FAIL %s: rc=%d os=%u canonical=%u expected=%u\n",
            label, rc, id.os, id.canonical, expected);
        ++failures;
    }
}
}
int main() {
    if (chimera_compat_init(1u, 64u) != 0) return 2;

    // Linux x86-64 calls whose canonical semantics are explicitly represented.
    expect(CHM_ENTRY_X86_SYSCALL, 64, 0, CHM_SYS_READ, "x86_64 read");
    expect(CHM_ENTRY_X86_SYSCALL, 64, 1, CHM_SYS_WRITE, "x86_64 write");
    expect(CHM_ENTRY_X86_SYSCALL, 64, 9, CHM_SYS_MMAP, "x86_64 mmap translation");
    expect(CHM_ENTRY_X86_SYSCALL, 64, 11, CHM_SYS_MUNMAP, "x86_64 munmap");
    expect(CHM_ENTRY_X86_SYSCALL, 64, 16, CHM_SYS_IOCTL, "x86_64 ioctl translation");
    expect(CHM_ENTRY_X86_SYSCALL, 64, 35, CHM_SYS_NANOSLEEP, "x86_64 nanosleep");
    expect(CHM_ENTRY_X86_SYSCALL, 64, 39, CHM_SYS_GETPID, "x86_64 getpid");
    expect(CHM_ENTRY_X86_SYSCALL, 64, 60, CHM_SYS_EXIT, "x86_64 exit");
    expect(CHM_ENTRY_X86_SYSCALL, 64, 61, CHM_SYS_WAIT, "x86_64 wait4 translation");
    expect(CHM_ENTRY_X86_SYSCALL, 64, 158, CHM_SYS_ARCH_PRCTL, "x86_64 arch_prctl");
    expect(CHM_ENTRY_X86_SYSCALL, 64, 231, CHM_SYS_EXIT_GROUP, "x86_64 exit_group");

    // Do not alias open/close/fstat/brk/mprotect to unrelated native calls.
    expect(CHM_ENTRY_X86_SYSCALL, 64, 2, 0xFFFFFFFFu, "x86_64 open remains unsupported");
    expect(CHM_ENTRY_X86_SYSCALL, 64, 3, 0xFFFFFFFFu, "x86_64 close remains unsupported");
    expect(CHM_ENTRY_X86_SYSCALL, 64, 5, 0xFFFFFFFFu, "x86_64 fstat remains unsupported");
    expect(CHM_ENTRY_X86_SYSCALL, 64, 12, 0xFFFFFFFFu, "x86_64 mprotect remains unsupported");

    // The legacy i386 mmap syscall uses a pointer to an argument block, so it
    // must not be translated to the six-register native mmap contract.
    expect(CHM_ENTRY_X86_INT80, 32, 1, CHM_SYS_EXIT, "i386 exit");
    expect(CHM_ENTRY_X86_INT80, 32, 3, CHM_SYS_READ, "i386 read");
    expect(CHM_ENTRY_X86_INT80, 32, 4, CHM_SYS_WRITE, "i386 write");
    expect(CHM_ENTRY_X86_INT80, 32, 20, CHM_SYS_GETPID, "i386 getpid");
    expect(CHM_ENTRY_X86_INT80, 32, 91, CHM_SYS_MUNMAP, "i386 munmap");
    expect(CHM_ENTRY_X86_INT80, 32, 162, CHM_SYS_NANOSLEEP, "i386 nanosleep");
    expect(CHM_ENTRY_X86_INT80, 32, 5, 0xFFFFFFFFu, "i386 open remains unsupported");
    expect(CHM_ENTRY_X86_INT80, 32, 6, 0xFFFFFFFFu, "i386 close remains unsupported");
    expect(CHM_ENTRY_X86_INT80, 32, 45, 0xFFFFFFFFu, "i386 brk remains unsupported");
    expect(CHM_ENTRY_X86_INT80, 32, 90, 0xFFFFFFFFu, "i386 legacy mmap remains unsupported");

    if (failures) return 1;
    std::puts("Linux syscall translation regression tests: PASS");
    return 0;
}
