.section .text.boot
.globl _start
.extern koronos_boot
_start:
  ldr x2, =__stack_top
  mov sp, x2
  mov x0, x1
  bl koronos_boot
1: wfi
   b 1b
