.text
.globl chimera_cpu_pause
.type chimera_cpu_pause,@function
chimera_cpu_pause:
    pause
    ret

.globl chimera_arch_barrier
.type chimera_arch_barrier,@function
chimera_arch_barrier:
    fence rw,rw
    ret
