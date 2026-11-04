#pragma once
#include <stdint.h>
#define KORONOS_ELF_MAG0 0x7f
#define KORONOS_ELF_MAG1 'E'
#define KORONOS_ELF_MAG2 'L'
#define KORONOS_ELF_MAG3 'F'
#define KORONOS_ELFCLASS64 2
#define KORONOS_ELFDATA2LSB 1
#define KORONOS_ET_REL 1
#define KORONOS_ET_EXEC 2
#define KORONOS_ET_DYN 3
#define KORONOS_EM_X86_64 62
#define KORONOS_EM_AARCH64 183
#define KORONOS_EM_RISCV 243
struct koronos_elf64_ehdr {
 uint8_t e_ident[16]; uint16_t e_type; uint16_t e_machine; uint32_t e_version; uint64_t e_entry;
 uint64_t e_phoff; uint64_t e_shoff; uint32_t e_flags; uint16_t e_ehsize; uint16_t e_phentsize;
 uint16_t e_phnum; uint16_t e_shentsize; uint16_t e_shnum; uint16_t e_shstrndx;
};
struct koronos_elf64_phdr {
 uint32_t p_type; uint32_t p_flags; uint64_t p_offset; uint64_t p_vaddr; uint64_t p_paddr;
 uint64_t p_filesz; uint64_t p_memsz; uint64_t p_align;
};
struct koronos_elf64_shdr {
 uint32_t sh_name; uint32_t sh_type; uint64_t sh_flags; uint64_t sh_addr; uint64_t sh_offset;
 uint64_t sh_size; uint32_t sh_link; uint32_t sh_info; uint64_t sh_addralign; uint64_t sh_entsize;
};
struct koronos_elf64_rela { uint64_t r_offset; uint64_t r_info; int64_t r_addend; };
static inline int koronos_elf64_valid(const struct koronos_elf64_ehdr *h) {
 return h && h->e_ident[0]==KORONOS_ELF_MAG0 && h->e_ident[1]==KORONOS_ELF_MAG1 &&
 h->e_ident[2]==KORONOS_ELF_MAG2 && h->e_ident[3]==KORONOS_ELF_MAG3 &&
 h->e_ident[4]==KORONOS_ELFCLASS64 && h->e_ident[5]==KORONOS_ELFDATA2LSB;
}
