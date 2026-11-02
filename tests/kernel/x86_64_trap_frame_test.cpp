#include "chimera/x86_64_trap_frame.h"
#include <assert.h>
#include <stdio.h>

int main() {
    chimera_x86_64_trap_frame f{};
    f.vector = CHIMERA_SYSCALL_VECTOR;
    f.rip = 0x0000000010000100ull;
    f.cs = CHIMERA_X86_64_USER_CODE_SELECTOR;
    f.rflags = CHIMERA_X86_64_RFLAGS_FIXED | CHIMERA_X86_64_RFLAGS_IF;
    f.user_rsp = 0x0000000010080000ull;
    f.user_ss = CHIMERA_X86_64_USER_DATA_SELECTOR;
    assert(chimera_x86_64_trap_frame_is_user(&f) == 1);

    f.cs = CHIMERA_X86_64_KERNEL_CODE_SELECTOR;
    assert(chimera_x86_64_trap_frame_is_user(&f) == 0);
    f.cs = CHIMERA_X86_64_USER_CODE_SELECTOR;
    f.user_ss = CHIMERA_X86_64_KERNEL_DATA_SELECTOR;
    assert(chimera_x86_64_trap_frame_is_user(&f) == 0);
    f.user_ss = CHIMERA_X86_64_USER_DATA_SELECTOR;
    f.rip = 0x0000800000000000ull;
    assert(chimera_x86_64_trap_frame_is_user(&f) == 0);
    f.rip = 0x1000;
    f.user_rsp = 0x0000800000000000ull;
    assert(chimera_x86_64_trap_frame_is_user(&f) == 0);
    f.user_rsp = 0x8000;
    f.rflags |= CHIMERA_X86_64_RFLAGS_IOPL;
    assert(chimera_x86_64_trap_frame_is_user(&f) == 0);
    f.rflags &= ~CHIMERA_X86_64_RFLAGS_IOPL;
    f.rflags |= CHIMERA_X86_64_RFLAGS_NT;
    assert(chimera_x86_64_trap_frame_is_user(&f) == 0);
    f.rflags &= ~CHIMERA_X86_64_RFLAGS_NT;
    f.rflags &= ~CHIMERA_X86_64_RFLAGS_IF;
    assert(chimera_x86_64_trap_frame_is_user(&f) == 0);
    assert(chimera_x86_64_trap_frame_is_user(nullptr) == 0);
    puts("x86_64 trap-frame ABI: normalized offsets and CPL3 return-frame validation passed");
    return 0;
}
