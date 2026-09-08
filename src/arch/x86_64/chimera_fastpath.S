.text
.globl chimera_cpu_pause
.type chimera_cpu_pause,@function
chimera_cpu_pause:
    pause
    ret

.globl chimera_rdtsc
.type chimera_rdtsc,@function
chimera_rdtsc:
    rdtsc
    shl $32, %rdx
    or %rdx, %rax
    ret

.section .note.GNU-stack,"",@progbits
