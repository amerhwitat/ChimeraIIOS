#include "chimera/x86_64_cpu.h"
#include "chimera/address_space.h"

namespace {
constexpr uint64_t PAGE_MASK = 0xFFFull;
constexpr uint64_t PHYSICAL_LIMIT = 0x100000000ull;

static bool canonical(uint64_t address) {
    return (address >> 47) == 0 || (address >> 47) == 0x1FFFFu;
}

extern "C" int koronos_x86_64_context_switch_raw(
    chimera_x86_64_context *from, const chimera_x86_64_context *to);
}

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

/* The only supported live switch is BSP-to-BSP within the currently active
 * address space. The stack arena is shared supervisor-only; the caller must
 * supply a live mapped stack top and must not release either context's stack.
 * Cross-CR3 transitions remain refused until AP/TLB shootdown support exists. */
extern "C" int koronos_x86_64_context_switch(
    chimera_x86_64_context *from, const chimera_x86_64_context *to) {
    if (!from || !to || from == to || !to->rsp ||
        !chimera_x86_64_cpu_is_ready(0) ||
        !to->kernel_stack_top || (to->kernel_stack_top & 0xFu) != 0 ||
        !canonical(to->kernel_stack_top)) return -1;

    uint64_t flags = 0;
    __asm__ volatile("pushfq; pop %0; cli" : "=r"(flags) :: "memory");
    const uint64_t current_root = koronos_address_space_current_root();
    if (!current_root || to->cr3 != current_root) {
        __asm__ volatile("push %0; popfq" :: "r"(flags) : "memory", "cc");
        return -2;
    }

    from->cr3 = current_root;
    from->kernel_stack_top = chimera_x86_64_cpu_kernel_stack(0);
    from->pid = chimera_x86_64_cpu_current_pid(0);

    if (chimera_x86_64_cpu_set_kernel_stack(0, to->kernel_stack_top) != 0) {
        __asm__ volatile("push %0; popfq" :: "r"(flags) : "memory", "cc");
        return -3;
    }
    if (chimera_x86_64_cpu_set_current_pid(0, to->pid) != 0) {
        (void)chimera_x86_64_cpu_set_kernel_stack(0, from->kernel_stack_top);
        __asm__ volatile("push %0; popfq" :: "r"(flags) : "memory", "cc");
        return -4;
    }

    const int result = koronos_x86_64_context_switch_raw(from, to);
    /* This executes when this context is resumed, not when it is suspended.
     * The next context's switch has already installed this context's TSS/PID. */
    __asm__ volatile("push %0; popfq" :: "r"(flags) : "memory", "cc");
    return result;
}
