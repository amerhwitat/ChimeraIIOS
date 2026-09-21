BITS 16
section .text
global koronos_real_mode_probe
global koronos_protected_mode_probe
koronos_real_mode_probe:
 cli
 xor ax,ax
 mov ds,ax
 mov es,ax
 mov ss,ax
 ret
BITS 32
koronos_protected_mode_probe:
 cli
 mov ax,0x10
 mov ds,ax
 mov es,ax
 mov ss,ax
 ret
