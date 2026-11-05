#include "../include/chimera/elf64.h"
static volatile uint32_t elf64_state;
extern "C" void koronos_elf64_init(void) { elf64_state=0x454C4634u; }
extern "C" int koronos_elf64_validate(const void* image,uint64_t size,uint16_t machine) {
 if(!image || size<sizeof(koronos_elf64_ehdr))return 0;
 const auto* h=static_cast<const koronos_elf64_ehdr*>(image);
 if(!koronos_elf64_valid(h) || h->e_version!=1 ||
    h->e_ehsize<sizeof(koronos_elf64_ehdr))return 0;
 if(h->e_machine!=machine || h->e_phentsize!=sizeof(koronos_elf64_phdr) ||
    h->e_phnum==0)return 0;
 /* Subtraction-based bounds checking avoids overflow in e_phoff + table_size. */
 if(h->e_phoff>size)return 0;
 const uint64_t phbytes=(uint64_t)h->e_phnum*(uint64_t)h->e_phentsize;
 if(phbytes>size-h->e_phoff)return 0;
 return 1;
}
