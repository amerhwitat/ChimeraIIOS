OPTION CASEMAP:NONE
.code

PUBLIC chimera_cpu_pause
chimera_cpu_pause PROC
    pause
    ret
chimera_cpu_pause ENDP

PUBLIC chimera_rdtsc
chimera_rdtsc PROC
    rdtsc
    shl rdx, 32
    or rax, rdx
    ret
chimera_rdtsc ENDP

END
