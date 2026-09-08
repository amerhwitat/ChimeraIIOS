#include <cassert>
#include <cstdint>
#include <string>
#include "chimera/RegisterN.hpp"
#include "chimera/state128.hpp"
#include "chimera/unified_isa.hpp"
#include "chimera/kernel_arch.hpp"

int main() {
    chimera::RegisterN<8192> a{};
    chimera::RegisterN<8192> b{};
    a.set_u64(0, 0xffffffffffffffffULL);
    b.set_u64(0, 1ULL);
    auto c = a + b;
    assert(c.lane(0) == 0);
    assert(c.lane(1) == 1);

    chimera::State128 s{};
    s[0] = 1.0;
    s[127] = 2.0;
    auto y = chimera::state_transition(s, s);
    assert(y[0] == 2.0);
    assert(y[127] == 4.0);

    auto rv = chimera::isa::decode_riscv64(0x003100b3u);
    assert(rv.valid);
    assert(rv.instruction.rd == 1 && rv.instruction.rs1 == 2 && rv.instruction.rs2 == 3);
    assert(rv.instruction.mnemonic == "add");

    const uint8_t syscall[] = {0x0f, 0x05};
    auto x86 = chimera::isa::decode_x86_64(syscall, sizeof(syscall));
    assert(x86.valid && x86.instruction.mnemonic == "syscall");

    chimera::kernel::Scheduler sched;
    chimera::kernel::Task task{42, 0, 0, 1, 0};
    sched.enqueue(&task);
    assert(sched.pick_next() == &task);
    return 0;
}
