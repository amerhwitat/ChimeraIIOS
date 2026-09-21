.section .text
.globl koronos_riscv_priv_init
koronos_riscv_priv_init:
  csrw mie,zero
  csrw sie,zero
  ret
