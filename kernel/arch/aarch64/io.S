.section .text
.globl koronos_mmio_read32
.globl koronos_mmio_write32
koronos_mmio_read32:
  ldr w0,[x0]
  ret
koronos_mmio_write32:
  str w1,[x0]
  ret
