.section .text.boot
.globl _start
.extern koronos_boot
_start:
  mov x0,x1
  bl koronos_boot
1: wfi
   b 1b
