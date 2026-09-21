#include "../include/chimera/elf64.h"
static volatile uint32_t module_state;
extern "C" void koronos_module_init(void){ module_state=0x4D4F4441u; }
extern "C" int koronos_module_compatible(const koronos_elf64_ehdr* h,uint16_t machine){
 if(!koronos_elf64_valid(h))return 0;
 if(h->e_type!=KORONOS_ET_REL && h->e_type!=KORONOS_ET_DYN)return 0;
 return h->e_machine==machine;
}
