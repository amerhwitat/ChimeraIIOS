#include "chimera/gdt_tss.h"
#include <cassert>
int main(){assert(chimera_x86_gdt_tss_prepare(0x8000)==0);auto*t=chimera_x86_tss_snapshot();assert(t&&t->rsp0==0x8000&&t->iopb_offset==sizeof(*t));assert(chimera_x86_tss_set_kernel_stack(0x9000)==0);assert(chimera_x86_tss_snapshot()->rsp0==0x9000);assert(chimera_x86_tss_set_kernel_stack(0x9001)<0);assert(chimera_x86_gdt_tss_prepare(0)<0);assert(chimera_x86_user_entry_available()==0);return 0;}
