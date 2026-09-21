#pragma once
#include <stdint.h>
struct koronos_elf32_ehdr {
 uint8_t e_ident[16]; uint16_t e_type,e_machine; uint32_t e_version,e_entry,e_phoff,e_shoff,e_flags;
 uint16_t e_ehsize,e_phentsize,e_phnum,e_shentsize,e_shnum,e_shstrndx;
};
static inline int koronos_elf32_valid(const struct koronos_elf32_ehdr* h){
 return h && h->e_ident[0]==0x7f && h->e_ident[1]=='E' && h->e_ident[2]=='L' && h->e_ident[3]=='F' && h->e_ident[4]==1;
}
