.section .text
.global chimera_live_entry
.type chimera_live_entry,@function
chimera_live_entry:
  cli
  call koronos_live_main
1: hlt
  jmp 1b
.size chimera_live_entry,.-chimera_live_entry
