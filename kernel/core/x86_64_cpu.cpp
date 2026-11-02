#include "chimera/x86_64_cpu.h"

namespace {
static_assert(sizeof(chimera_x86_64_tss) == 104,
              "x86-64 architectural TSS layout must remain 104 bytes");

struct __attribute__((aligned(16))) CpuState {
    uint32_t logical_id;
    uint32_t apic_id;
    uint64_t gdt[7];
    chimera_x86_64_gdtr gdtr;
    chimera_x86_64_tss tss;
    uint8_t entry_stack[CHIMERA_X86_64_ENTRY_STACK_SIZE] __attribute__((aligned(16)));
    volatile uint32_t ready;
};

static_assert(__builtin_offsetof(CpuState, logical_id) == 0,
              "GS current-CPU identity must be the first per-CPU field");
static_assert((__builtin_offsetof(CpuState, entry_stack) & 0xFu) == 0,
              "per-CPU privilege-entry stack must be 16-byte aligned");

static CpuState cpus[CHIMERA_X86_64_MAX_CPUS];

extern "C" void koronos_x86_64_load_gdt_tss(
    const chimera_x86_64_gdtr *gdtr, uint16_t selector);

static bool canonical_kernel(uint64_t address) {
    return address != 0 && (address >> 47) == 0x1FFFFu;
}

static uint64_t read_msr(uint32_t msr) {
    uint32_t lo = 0, hi = 0;
    __asm__ volatile("rdmsr" : "=a"(lo), "=d"(hi) : "c"(msr));
    return (static_cast<uint64_t>(hi) << 32) | lo;
}

static void write_msr(uint32_t msr, uint64_t value) {
    const uint32_t lo = static_cast<uint32_t>(value);
    const uint32_t hi = static_cast<uint32_t>(value >> 32);
    __asm__ volatile("wrmsr" : : "c"(msr), "a"(lo), "d"(hi) : "memory");
}

static bool current_apic_id(uint32_t *out) {
    if (!out) return false;
    uint32_t a = 1, b = 0, c = 0, d = 0;
    __asm__ volatile("cpuid" : "+a"(a), "=b"(b), "=c"(c), "=d"(d) : "c"(0));
    if ((d & (1u << 9)) == 0) return false;
    const uint64_t apic_base = read_msr(0x1Bu);
    if (apic_base & (1ull << 10)) {
        *out = static_cast<uint32_t>(read_msr(0x802u));
    } else {
        *out = (b >> 24) & 0xFFu;
    }
    return true;
}

static uint32_t current_logical_id() {
    uint32_t id = UINT32_MAX;
    __asm__ volatile("movl %%gs:0, %0" : "=r"(id) :: "memory");
    return id;
}
}

extern "C" int chimera_x86_64_cpu_init(uint32_t cpu_id) {
    if (cpu_id >= CHIMERA_X86_64_MAX_CPUS) return -1;
    CpuState &cpu = cpus[cpu_id];
    if (cpu.ready) return -2;

    uint32_t apic_id = 0;
    if (!current_apic_id(&apic_id)) return -4;
    for (uint32_t i = 0; i < CHIMERA_X86_64_MAX_CPUS; ++i) {
        if (i != cpu_id && cpus[i].ready && cpus[i].apic_id == apic_id)
            return -5;
    }

    cpu.logical_id = cpu_id;
    cpu.apic_id = apic_id;
    cpu.gdt[0] = 0;
    cpu.gdt[1] = 0x00AF9A000000FFFFull;
    cpu.gdt[2] = 0x00CF92000000FFFFull;
    cpu.gdt[3] = 0x00AFFA000000FFFFull;
    cpu.gdt[4] = 0x00CFF2000000FFFFull;

    const uint64_t stack_top =
        (uint64_t)(uintptr_t)(cpu.entry_stack + sizeof(cpu.entry_stack));
    if ((stack_top & 0xFu) != 0 || !canonical_kernel(stack_top)) return -3;

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

    koronos_x86_64_load_gdt_tss(&cpu.gdtr, CHIMERA_X86_64_TSS_SELECTOR);
    /* IA32_GS_BASE is the trusted current-CPU anchor. This is installed on
       the CPU that is executing this initializer, never on a remote CPU. */
    write_msr(0xC0000101u, reinterpret_cast<uint64_t>(&cpu));
    if (current_logical_id() != cpu_id) return -6;
    cpu.ready = 1;
    return 0;
}

extern "C" int chimera_x86_64_cpu_current_id(void) {
    const uint32_t id = current_logical_id();
    if (id >= CHIMERA_X86_64_MAX_CPUS || !cpus[id].ready) return -1;
    return static_cast<int>(id);
}

extern "C" int chimera_x86_64_cpu_current_apic_id(uint32_t *out) {
    if (!out || chimera_x86_64_cpu_current_id() < 0) return -1;
    uint32_t id = 0;
    if (!current_apic_id(&id)) return -2;
    if (id != cpus[current_logical_id()].apic_id) return -3;
    *out = id;
    return 0;
}

extern "C" int chimera_x86_64_cpu_set_kernel_stack(
    uint32_t cpu_id, uint64_t stack_top) {
    if (cpu_id >= CHIMERA_X86_64_MAX_CPUS || !cpus[cpu_id].ready)
        return -1;
    if (current_logical_id() != cpu_id) return -4;
    if (!stack_top || (stack_top & 0xFu) != 0 || !canonical_kernel(stack_top))
        return -2;
    uint64_t rflags = 0;
    __asm__ volatile("pushfq; popq %0" : "=r"(rflags) :: "memory");
    if (!chimera_x86_64_tss_update_allowed(rflags)) return -3;
    cpus[cpu_id].tss.rsp0 = stack_top;
    __asm__ volatile("" ::: "memory");
    return 0;
}

extern "C" int chimera_x86_64_cpu_is_ready(uint32_t cpu_id) {
    return cpu_id < CHIMERA_X86_64_MAX_CPUS && cpus[cpu_id].ready ? 1 : 0;
}

extern "C" uint64_t chimera_x86_64_cpu_kernel_stack(uint32_t cpu_id) {
    if (cpu_id >= CHIMERA_X86_64_MAX_CPUS || !cpus[cpu_id].ready) return 0;
    if (current_logical_id() != cpu_id) return 0;
    return cpus[cpu_id].tss.rsp0;
}
