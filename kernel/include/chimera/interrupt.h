#ifndef CHIMERA_INTERRUPT_H
#define CHIMERA_INTERRUPT_H

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
void chimera_interrupt_dispatch(uint64_t vector, uint64_t frame);

#ifdef __cplusplus
}
#endif

#endif
