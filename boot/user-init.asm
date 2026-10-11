BITS 64
default rel
section .text
global _start
_start:
    ; Minimal freestanding first userspace task.  This intentionally avoids
    ; libc/syscalls until the kernel exposes a stable userspace ABI.
    mov rdi, 0xB8000
    lea rsi, [rel message]
    mov ah, 0x0F
.loop:
    lodsb
    test al, al
    jz .idle
    stosw
    jmp .loop
.idle:
    pause
    jmp .idle

section .rodata
message: db "Chimera II OS: native userspace init reached", 0
