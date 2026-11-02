#include "chimera/x86_64_cpu.h"
#include "chimera/address_space.h"

namespace {
static bool canonical(uint64_t address) {
    return (address >> 47) == 0 || (address >> 47) == 0x1FFFFu;
}

static bool bsp_only() {
    for (uint32_t cpu = 1; cpu < CHIMERA_X86_64_MAX_CPUS; ++cpu)
        if (chimera_x86_64_cpu_is_ready(cpu)) return false;
    return true;
}
}

extern "C" int koronos_x86_64_context_switch_raw(
    chimera_x86_64_context *from, const chimera_x86_64_context *to);

/*
 * BSP-only saved-context handoff. The shared supervisor subtree makes the
 * current and target kernel stacks visible under both roots. A local CR3
 * write flushes this CPU's non-PCID translations. Cross-CPU reuse/reaping is
 * still forbidden until AP startup and acknowledged TLB shootdowns exist.
 */
extern "C" int koronos_x86_64_context_switch(
    chimera_x86_64_context *from, const chimera_x86_64_context *to) {
    if (!from || !to || from == to || !to->rsp ||
        !chimera_x86_64_cpu_is_ready(0) ||
        !to->kernel_stack_top || (to->kernel_stack_top & 0xFu) != 0 ||
        !canonical(to->kernel_stack_top)) return -1;

    uint64_t flags = 0;
    __asm__ volatile("pushfq; pop %0; cli" : "=r"(flags) :: "memory");

    const uint64_t current_root = koronos_address_space_current_root();
    if (!current_root || !koronos_address_space_root_valid(current_root) ||
        !koronos_address_space_root_valid(to->cr3)) {
        __asm__ volatile("push %0; popfq" :: "r"(flags) : "memory", "cc");
        return -2;
    }
    const bool cross_cr3 = to->cr3 != current_root;
    if (cross_cr3 && !bsp_only()) {
        __asm__ volatile("push %0; popfq" :: "r"(flags) : "memory", "cc");
        return -3;
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
                    to->cr3, stack_base + static_cast<uint64_t>(i) * page_size) == 1;
            }
            if (target_stack_valid) {
                target_stack_valid = koronos_address_space_kernel_page_mapped(
                    to->cr3, stack_base - page_size) == 0;
            }
        }
    }
    if (!target_stack_valid || !old_stack_top) {
        __asm__ volatile("push %0; popfq" :: "r"(flags) : "memory", "cc");
        return -4;
    }

    /* Save the outgoing ownership tuple before changing any privileged state. */
    from->cr3 = current_root;
    from->kernel_stack_top = old_stack_top;
    from->pid = old_pid;

    /* Interrupts remain disabled across CR3, TSS.RSP0, PID and RSP handoff. */
    if (cross_cr3)
        __asm__ volatile("mov %0, %%cr3" :: "r"(to->cr3) : "memory");
    if (chimera_x86_64_cpu_set_kernel_stack(0, to->kernel_stack_top) != 0 ||
        chimera_x86_64_cpu_set_current_pid(0, to->pid) != 0) {
        (void)chimera_x86_64_cpu_set_kernel_stack(0, old_stack_top);
        (void)chimera_x86_64_cpu_set_current_pid(0, old_pid);
        if (cross_cr3)
            __asm__ volatile("mov %0, %%cr3" :: "r"(current_root) : "memory");
        __asm__ volatile("push %0; popfq" :: "r"(flags) : "memory", "cc");
        return -5;
    }

    const int result = koronos_x86_64_context_switch_raw(from, to);
    if (result != 0) {
        (void)chimera_x86_64_cpu_set_kernel_stack(0, old_stack_top);
        (void)chimera_x86_64_cpu_set_current_pid(0, old_pid);
        if (cross_cr3)
            __asm__ volatile("mov %0, %%cr3" :: "r"(current_root) : "memory");
    }
    /* On a successful resume, the incoming context already restored its own
       CR3/TSS/PID tuple before returning to this suspended wrapper frame. */
    __asm__ volatile("push %0; popfq" :: "r"(flags) : "memory", "cc");
    return result;
}
