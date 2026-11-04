#include "chimera/x86_64_cpu.h"

namespace {
constexpr uint64_t PAGE_MASK = 0xFFFull;
constexpr uint64_t PHYSICAL_LIMIT = 0x100000000ull;

static bool canonical(uint64_t address) {
    return (address >> 47) == 0 || (address >> 47) == 0x1FFFFu;
}

}

extern "C" int koronos_x86_64_context_switch_raw(
    chimera_x86_64_context *from, const chimera_x86_64_context *to);
extern "C" void koronos_x86_64_context_trampoline();

extern "C" int koronos_x86_64_context_prepare(
    chimera_x86_64_context *context, uint64_t stack_base, uint64_t stack_size,
    uint64_t cr3, void (*entry)(void *), void *argument) {
    if (!context || !entry || !stack_base ||
        stack_size < CHIMERA_X86_64_CONTEXT_FRAME_SIZE ||
        stack_base > UINT64_MAX - stack_size || !cr3 ||
        cr3 >= PHYSICAL_LIMIT || (cr3 & PAGE_MASK) != 0) return -1;

    const uint64_t stack_end = stack_base + stack_size;
    const uint64_t aligned_top = stack_end & ~0xFull;
    if (aligned_top < stack_base ||
        aligned_top - stack_base < CHIMERA_X86_64_CONTEXT_FRAME_SIZE ||
        !canonical(stack_base) || !canonical(aligned_top - 1u)) return -2;

    const uint64_t entry_address = reinterpret_cast<uint64_t>(entry);
    const uint64_t trampoline_address =
        reinterpret_cast<uint64_t>(&koronos_x86_64_context_trampoline);
    if (!canonical(entry_address) || !canonical(trampoline_address)) return -3;

    /* Layout consumed by cpu_state.asm:
     * r15, r14, r13(entry), r12(argument), rbx, rbp, RFLAGS, return RIP,
     * padding. Initial IF is clear; the first RET leaves RSP at 8 mod 16. */
    auto *frame = reinterpret_cast<uint64_t *>(
        aligned_top - CHIMERA_X86_64_CONTEXT_FRAME_SIZE);
    frame[0] = 0;
    frame[1] = 0;
    frame[2] = entry_address;
    frame[3] = reinterpret_cast<uint64_t>(argument);
    frame[4] = 0;
    frame[5] = 0;
    frame[6] = 0x2u;
    frame[7] = trampoline_address;
    frame[8] = 0;

    context->rsp = reinterpret_cast<uint64_t>(frame);
    context->cr3 = cr3;
    return 0;
}

