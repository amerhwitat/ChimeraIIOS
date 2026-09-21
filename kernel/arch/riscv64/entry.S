.section .text.boot
.globl _start
.extern koronos_boot
_start:
  mv sp,t0
  mv a0,a1
  call koronos_boot
1: wfi
   j 1b
