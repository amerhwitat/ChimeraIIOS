#ifndef CHIMERA_INTERRUPT_H
#define CHIMERA_INTERRUPT_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_INTERRUPT_ABI 1u
#define CHIMERA_IDT_ENTRIES 256u
#define CHIMERA_IRQ_BASE 32u
#define CHIMERA_SYSCALL_VECTOR 0x80u
#define CHIMERA_WINDOWS_INT_VECTOR 0x2Eu
#define CHIMERA_DOS_INT_VECTOR 0x21u

/*
 * Stack layout produced by kernel/arch/x86_64/interrupts.asm.
 * cpu_frame[0] is RIP for vectors without a CPU error code and the error
 * code for vectors which push one. RSP/SS are present only after CPL changes.
 */
typedef struct chimera_interrupt_frame {
    uint64_t r15, r14, r13, r12, r11, r10, r9, r8;
    uint64_t rdi, rsi, rbp, rbx, rdx, rcx, rax;
    uint64_t vector;
    uint64_t cpu_frame[6];
} chimera_interrupt_frame;

static inline uint32_t chimera_interrupt_vector_has_error_code(uint64_t vector) {
    switch (vector) {
        case 8u: case 10u: case 11u: case 12u: case 13u:
        case 14u: case 17u: case 21u: case 29u: case 30u:
            return 1u;
        default:
            return 0u;
    }
}

static inline uint64_t chimera_interrupt_frame_rip(
    const chimera_interrupt_frame *frame, uint64_t vector) {
    if (!frame) return 0u;
    return frame->cpu_frame[chimera_interrupt_vector_has_error_code(vector)];
}

static inline uint64_t chimera_interrupt_frame_cs(
    const chimera_interrupt_frame *frame, uint64_t vector) {
    if (!frame) return 0u;
    return frame->cpu_frame[chimera_interrupt_vector_has_error_code(vector) + 1u];
}

typedef struct chimera_interrupt_snapshot {
    uint32_t abi;
    uint32_t initialized;
    uint32_t enabled;
    uint32_t idt_entries;
    uint32_t exception_count;
    uint32_t hardware_irq_count;
    uint32_t software_irq_count;
    uint32_t syscall_count;
    uint32_t last_vector;
} chimera_interrupt_snapshot;

int chimera_interrupt_init(void);
int chimera_interrupt_enable(void);
int chimera_interrupt_disable(void);
int chimera_interrupt_get_snapshot(chimera_interrupt_snapshot *out);
void chimera_interrupt_dispatch(uint64_t vector, const chimera_interrupt_frame *frame);

#ifdef __cplusplus
}
static_assert(offsetof(chimera_interrupt_frame, vector) == 120u,
              "interrupt assembly vector offset changed");
static_assert(offsetof(chimera_interrupt_frame, cpu_frame) == 128u,
              "interrupt assembly CPU-frame offset changed");
#endif

#endif
