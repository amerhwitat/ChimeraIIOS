/* Chimera II Mobile Microkernel AArch64 exception-vector integration point.
 *
 * This file deliberately contains only the ABI boundary. Platform-specific
 * vector tables, GIC configuration, EL transitions, and context switching
 * belong in a board/SoC backend and must be validated on target hardware.
 */

#if defined(__aarch64__)
    .text
    .align 11
    .global chimera_mobile_aarch64_vectors
    .type chimera_mobile_aarch64_vectors, %function
chimera_mobile_aarch64_vectors:
    ret
#endif
