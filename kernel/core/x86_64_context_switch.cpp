#include "chimera/x86_64_cpu.h"
#include "chimera/address_space.h"

namespace {
static bool canonical(uint64_t address) {
    return (address >> 47) == 0 || (address >> 47) == 0x1FFFFu;
}
}
extern "C" int koronos_x86_64_context_switch_raw(
    chimera_x86_64_context *from, const chimera_x86_64_context *to);

/* BSP-only same-CR3 switch. The target stack must be either the immutable
 * bootstrap stack or a fully mapped guarded stack from the shared arena. */
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
        (void)chimera_x86_64_cpu_set_kernel_stack(0, old_stack_top);
        (void)chimera_x86_64_cpu_set_current_pid(0, old_pid);
    }
    __asm__ volatile("push %0; popfq" :: "r"(flags) : "memory", "cc");
    return result;
}
