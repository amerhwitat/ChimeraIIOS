.section .text
.globl koronos_aarch64_priv_init
koronos_aarch64_priv_init:
  msr daifset,#0xf
  isb
  ret
