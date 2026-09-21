#include "../include/chimera/elf64.h"
#define R_X86_64_RELATIVE 8u
#define R_AARCH64_RELATIVE 1027u
#define R_RISCV_RELATIVE 3u
static uint32_t machine_relative(uint16_t machine){
 if(machine==KORONOS_EM_X86_64)return R_X86_64_RELATIVE;
 if(machine==KORONOS_EM_AARCH64)return R_AARCH64_RELATIVE;
 if(machine==KORONOS_EM_RISCV)return R_RISCV_RELATIVE;
 return 0;
}
extern "C" int koronos_apply_relative(const koronos_elf64_rela* rela,uint64_t load_base,uint16_t machine){
 if(!rela)return 0;
 uint32_t type=(uint32_t)(rela->r_info & 0xffffffffu);
 if(type!=machine_relative(machine))return 0;
 *reinterpret_cast<volatile uint64_t*>(load_base+rela->r_offset)=load_base+(uint64_t)rela->r_addend;
 return 1;
}
