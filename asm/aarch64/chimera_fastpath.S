.text
.global chimera_cpu_pause
.type chimera_cpu_pause, %function
chimera_cpu_pause:
    yield
    ret

.global chimera_arch_barrier
.type chimera_arch_barrier, %function
chimera_arch_barrier:
    dmb ish
    ret
