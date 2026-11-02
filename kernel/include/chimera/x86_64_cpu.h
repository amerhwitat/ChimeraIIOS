#ifndef CHIMERA_X86_64_CPU_H
#define CHIMERA_X86_64_CPU_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_X86_64_CPU_ABI 1u
#define CHIMERA_X86_64_MAX_CPUS 16u
#define CHIMERA_X86_64_ENTRY_STACK_SIZE 16384u
#define CHIMERA_X86_64_KERNEL_CODE_SELECTOR 0x08u
#define CHIMERA_X86_64_KERNEL_DATA_SELECTOR 0x10u
#define CHIMERA_X86_64_USER_CODE_SELECTOR 0x1Bu
#define CHIMERA_X86_64_USER_DATA_SELECTOR 0x23u
#define CHIMERA_X86_64_TSS_SELECTOR 0x28u

#if defined(_MSC_VER)
#pragma pack(push, 1)
#define CHIMERA_X86_64_PACKED
#else
#define CHIMERA_X86_64_PACKED __attribute__((packed))
#endif

typedef struct CHIMERA_X86_64_PACKED chimera_x86_64_tss {
    uint32_t reserved0;
    uint64_t rsp0, rsp1, rsp2;
    uint64_t reserved1;
    uint64_t ist1, ist2, ist3, ist4, ist5, ist6, ist7;
    uint64_t reserved2;
    uint16_t reserved3;
    uint16_t io_map_base;
} chimera_x86_64_tss;

typedef struct CHIMERA_X86_64_PACKED chimera_x86_64_gdtr {
    uint16_t limit;
    uint64_t base;
} chimera_x86_64_gdtr;

#if defined(_MSC_VER)
#pragma pack(pop)
#endif
#undef CHIMERA_X86_64_PACKED

/* Pure policy helper shared with host-side TSS guard tests. */
#define CHIMERA_X86_64_RFLAGS_IF (1ull << 9)
static inline int chimera_x86_64_tss_update_allowed(uint64_t rflags) {
    return (rflags & CHIMERA_X86_64_RFLAGS_IF) == 0;
}

/* Pure helper shared with host-side descriptor-layout tests. */
static inline void chimera_x86_64_encode_tss_descriptor(
    uint64_t base, uint32_t limit, uint64_t *low, uint64_t *high) {
    if (!low || !high) return;
    *low = ((uint64_t)(limit & 0xFFFFu)) |
           ((base & 0xFFFFFFu) << 16) |
           (0x89ull << 40) |
           ((uint64_t)((limit >> 16) & 0x0Fu) << 48) |
           (((base >> 24) & 0xFFu) << 56);
    *high = base >> 32;
}

int chimera_x86_64_cpu_init(uint32_t cpu_id);
/* Current CPU identity is read from the CPU-local GS anchor installed during init. */
int chimera_x86_64_cpu_current_id(void);
int chimera_x86_64_cpu_current_apic_id(uint32_t *out);
int chimera_x86_64_cpu_set_kernel_stack(uint32_t cpu_id, uint64_t stack_top);
int chimera_x86_64_cpu_is_ready(uint32_t cpu_id);
uint64_t chimera_x86_64_cpu_kernel_stack(uint32_t cpu_id);

#ifdef __cplusplus
}
#endif

#endif
