#include "chimera/x86_64_cpu.h"
#include "chimera/address_space.h"

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

    const uint64_t old_stack_top = chimera_x86_64_cpu_kernel_stack(0);
    const uint32_t old_pid = chimera_x86_64_cpu_current_pid(0);
    const uint64_t bootstrap_top = chimera_x86_64_cpu_bootstrap_kernel_stack(0);
    bool target_stack_valid = to->kernel_stack_top == bootstrap_top;
    if (!target_stack_valid) {
        constexpr uint64_t page_size = 4096u;
        constexpr uint64_t stack_bytes =
            static_cast<uint64_t>(KORONOS_KERNEL_STACK_USABLE_PAGES) * page_size;
        if (to->kernel_stack_top >= stack_bytes + page_size) {
            const uint64_t stack_base = to->kernel_stack_top - stack_bytes;
            target_stack_valid = to->rsp >= stack_base && to->rsp < to->kernel_stack_top;
            for (uint32_t i = 0; target_stack_valid &&
                 i < KORONOS_KERNEL_STACK_USABLE_PAGES; ++i) {
                target_stack_valid = koronos_address_space_kernel_page_mapped(
                    current_root, stack_base + static_cast<uint64_t>(i) * page_size) == 1;
            }
            if (target_stack_valid) {
                target_stack_valid = koronos_address_space_kernel_page_mapped(
                    current_root, stack_base - page_size) == 0;
            }
        }
    }
    if (!target_stack_valid || !old_stack_top) {
        __asm__ volatile("push %0; popfq" :: "r"(flags) : "memory", "cc");
        return -3;
    }

    from->cr3 = current_root;
    from->kernel_stack_top = old_stack_top;
    from->pid = old_pid;

    if (chimera_x86_64_cpu_set_kernel_stack(0, to->kernel_stack_top) != 0 ||
        chimera_x86_64_cpu_set_current_pid(0, to->pid) != 0) {
        (void)chimera_x86_64_cpu_set_kernel_stack(0, old_stack_top);
        (void)chimera_x86_64_cpu_set_current_pid(0, old_pid);
        __asm__ volatile("push %0; popfq" :: "r"(flags) : "memory", "cc");
        return -4;
    }

    const int result = koronos_x86_64_context_switch_raw(from, to);
    if (result != 0) {
        /* Validation failures return on the old stack; restore its CPU state. */
        (void)chimera_x86_64_cpu_set_kernel_stack(0, old_stack_top);
        (void)chimera_x86_64_cpu_set_current_pid(0, old_pid);
    }
    /* On a successful resume, the context switching back has already restored
     * this context's TSS/PID. Restore only the caller's saved interrupt state. */
    __asm__ volatile("push %0; popfq" :: "r"(flags) : "memory", "cc");
    return result;
}
