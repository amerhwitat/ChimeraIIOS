#include "chimera/x86_64_cpu.h"

namespace {
struct __attribute__((aligned(16))) CpuState {
    uint64_t gdt[7];
    chimera_x86_64_gdtr gdtr;
    chimera_x86_64_tss tss;
    uint8_t entry_stack[CHIMERA_X86_64_ENTRY_STACK_SIZE];
    volatile uint32_t ready;
};

static CpuState cpus[CHIMERA_X86_64_MAX_CPUS];

extern "C" void koronos_x86_64_load_gdt_tss(
    const chimera_x86_64_gdtr *gdtr, uint16_t selector);

static bool canonical(uint64_t address) {
    return (address >> 47) == 0 || (address >> 47) == 0x1FFFFu;
}
}

extern "C" int chimera_x86_64_cpu_init(uint32_t cpu_id) {
    if (cpu_id >= CHIMERA_X86_64_MAX_CPUS) return -1;
    CpuState &cpu = cpus[cpu_id];
    if (cpu.ready) return -2;

    cpu.gdt[0] = 0;
    cpu.gdt[1] = 0x00AF9A000000FFFFull; /* ring-0 64-bit code */
    cpu.gdt[2] = 0x00CF92000000FFFFull; /* ring-0 data */
    cpu.gdt[3] = 0x00AFFA000000FFFFull; /* ring-3 64-bit code */
    cpu.gdt[4] = 0x00CFF2000000FFFFull; /* ring-3 data */

    const uint64_t stack_top =
        (uint64_t)(uintptr_t)(cpu.entry_stack + sizeof(cpu.entry_stack));
    if ((stack_top & 0xFu) != 0 || !canonical(stack_top)) return -3;

    cpu.tss = {};
    cpu.tss.rsp0 = stack_top;
    cpu.tss.io_map_base = sizeof(chimera_x86_64_tss);
    uint64_t tss_low = 0, tss_high = 0;
    chimera_x86_64_encode_tss_descriptor(
        (uint64_t)(uintptr_t)&cpu.tss,
        (uint32_t)(sizeof(chimera_x86_64_tss) - 1u),
        &tss_low, &tss_high);
    cpu.gdt[5] = tss_low;
    cpu.gdt[6] = tss_high;
    cpu.gdtr.limit = (uint16_t)(sizeof(cpu.gdt) - 1u);
    cpu.gdtr.base = (uint64_t)(uintptr_t)cpu.gdt;

    /* Load the per-CPU GDT and available 64-bit TSS before any CPL3 gate can
     * be enabled. Interrupt gates remain DPL0 until process contexts exist. */
    koronos_x86_64_load_gdt_tss(&cpu.gdtr, CHIMERA_X86_64_TSS_SELECTOR);
    cpu.ready = 1;
    return 0;
}

extern "C" int chimera_x86_64_cpu_set_kernel_stack(
    uint32_t cpu_id, uint64_t stack_top) {
    if (cpu_id >= CHIMERA_X86_64_MAX_CPUS || !cpus[cpu_id].ready)
        return -1;
    if (!stack_top || (stack_top & 0xFu) != 0 || !canonical(stack_top))
        return -2;
    /* Caller must invoke this on the owning CPU with interrupts disabled.
     * Scheduler/process integration will provide owned stacks before CPL3. */
    cpus[cpu_id].tss.rsp0 = stack_top;
    __asm__ volatile("" ::: "memory");
    return 0;
}

extern "C" int chimera_x86_64_cpu_is_ready(uint32_t cpu_id) {
    return cpu_id < CHIMERA_X86_64_MAX_CPUS && cpus[cpu_id].ready ? 1 : 0;
}

extern "C" uint64_t chimera_x86_64_cpu_kernel_stack(uint32_t cpu_id) {
    if (cpu_id >= CHIMERA_X86_64_MAX_CPUS || !cpus[cpu_id].ready) return 0;
    return cpus[cpu_id].tss.rsp0;
}
