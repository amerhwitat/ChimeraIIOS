#ifndef CHIMERA_X86_64_TRAP_FRAME_H
#define CHIMERA_X86_64_TRAP_FRAME_H

#include <stdint.h>
#include "x86_64_cpu.h"

#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_X86_64_TRAP_FRAME_ABI 1u
#define CHIMERA_X86_64_RFLAGS_FIXED (1ull << 1)
#define CHIMERA_X86_64_RFLAGS_IF (1ull << 9)
#define CHIMERA_X86_64_RFLAGS_IOPL (3ull << 12)
#define CHIMERA_X86_64_RFLAGS_NT (1ull << 14)
#define CHIMERA_X86_64_RFLAGS_VM (1ull << 17)

/* Exact normalized stack layout produced by interrupts.asm. The final RSP/SS
 * words are supplied by the CPU only for a privilege-level transition. */
typedef struct chimera_x86_64_trap_frame {
    uint64_t r15, r14, r13, r12, r11, r10, r9, r8;
    uint64_t rdi, rsi, rbp, rbx, rdx, rcx, rax;
    uint64_t vector, error_code;
    uint64_t rip, cs, rflags;
    uint64_t user_rsp, user_ss;
} chimera_x86_64_trap_frame;

static inline int chimera_x86_64_is_canonical_user_address(uint64_t address) {
    /* Conservative 48-bit user canonical range; LA57 user mappings are not
     * admitted by this ABI until their range policy is explicitly defined. */
    return address != 0 && (address >> 47) == 0;
}

static inline int chimera_x86_64_trap_frame_is_user(
    const chimera_x86_64_trap_frame *frame) {
    if (!frame || (frame->cs & 3u) != 3u) return 0;
    if ((frame->cs & 0xFFFFu) != CHIMERA_X86_64_USER_CODE_SELECTOR) return 0;
    if ((frame->user_ss & 0xFFFFu) != CHIMERA_X86_64_USER_DATA_SELECTOR) return 0;
    if (!chimera_x86_64_is_canonical_user_address(frame->rip) ||
        !chimera_x86_64_is_canonical_user_address(frame->user_rsp)) return 0;
    if ((frame->rflags & CHIMERA_X86_64_RFLAGS_FIXED) == 0 ||
        (frame->rflags & CHIMERA_X86_64_RFLAGS_IF) == 0) return 0;
    if (frame->rflags & (CHIMERA_X86_64_RFLAGS_IOPL |
                         CHIMERA_X86_64_RFLAGS_NT |
                         CHIMERA_X86_64_RFLAGS_VM)) return 0;
    return 1;
}

#ifdef __cplusplus
}
static_assert(offsetof(chimera_x86_64_trap_frame, vector) == 120,
              "ISR vector offset must match assembly");
static_assert(offsetof(chimera_x86_64_trap_frame, error_code) == 128,
              "ISR error-code offset must match assembly");
static_assert(offsetof(chimera_x86_64_trap_frame, rip) == 136,
              "CPU return-frame offset must match assembly");
static_assert(offsetof(chimera_x86_64_trap_frame, user_rsp) == 160,
              "CPL3 RSP offset must match CPU frame");
static_assert(sizeof(chimera_x86_64_trap_frame) == 176,
              "normalized trap-frame ABI size changed");
#endif

#endif
