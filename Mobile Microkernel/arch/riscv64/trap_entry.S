/* Chimera II Mobile Microkernel RISC-V64 trap-entry ABI boundary.
 * Board-specific trap setup, register save/restore, delegation and timer
 * handling must be supplied by the RISC-V platform backend.
 */

#if defined(__riscv) && (__riscv_xlen == 64)
    .text
    .align 2
    .global chimera_mobile_riscv64_trap_entry
    .type chimera_mobile_riscv64_trap_entry, @function
chimera_mobile_riscv64_trap_entry:
    ret
#endif
