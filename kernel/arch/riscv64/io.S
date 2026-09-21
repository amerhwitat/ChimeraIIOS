.section .text
.globl koronos_mmio_read32
.globl koronos_mmio_write32
koronos_mmio_read32:
  lw a0,0(a0)
  ret
koronos_mmio_write32:
  sw a1,0(a0)
  ret
