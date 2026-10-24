#include <cassert>
#include <cstdint>
#include <cstring>
#include "chimera/process.h"

static void make_elf(uint8_t* b,bool wx){
  std::memset(b,0,4096);
  auto* h=(koronos_elf64_ehdr*)b;
  h->e_ident[0]=0x7f; h->e_ident[1]='E'; h->e_ident[2]='L'; h->e_ident[3]='F';
  h->e_ident[4]=2; h->e_ident[5]=1; h->e_ident[6]=1; h->e_type=KORONOS_ET_EXEC; h->e_machine=KORONOS_EM_X86_64;
  h->e_version=1; h->e_entry=0x100400100; h->e_ehsize=sizeof(*h); h->e_phoff=sizeof(*h);
  h->e_phentsize=sizeof(koronos_elf64_phdr); h->e_phnum=1;
  auto* p=(koronos_elf64_phdr*)(b+h->e_phoff);
  p->p_type=1; p->p_flags=wx?3:5; p->p_offset=0x1000; p->p_vaddr=0x100400000;
  p->p_filesz=16; p->p_memsz=0x2000; p->p_align=4096;
  std::memset(b+0x1000,0x90,16);
}
int main(){
  uint8_t image[8192]{};
  chimera_process_init();
  make_elf(image,false);
  chimera_process_image p{};
  assert(chimera_process_admit_elf(image,sizeof(image),KORONOS_EM_X86_64,0x7fffffffe000ull,&p)>0);
  assert(p.segment_count==1 && p.entry==0x100400100 && p.image_low==0x100400000);
  uint32_t pid=p.pid;
  assert(chimera_process_set_state(pid,CHIMERA_PROCESS_READY)==0);
  chimera_process_image q{};
  assert(chimera_process_get(pid,&q)==0 && q.state==CHIMERA_PROCESS_READY);
  make_elf(image,false);
  auto* h = reinterpret_cast<koronos_elf64_ehdr*>(image);
  h->e_phoff = UINT64_MAX - 7u;
  assert(koronos_elf64_validate(image,sizeof(image),KORONOS_EM_X86_64)==0);
  assert(chimera_process_admit_elf(image,sizeof(image),KORONOS_EM_X86_64,0x7fffffffe000ull,&q)<0);
  make_elf(image,false);
  h = reinterpret_cast<koronos_elf64_ehdr*>(image);
  h->e_phnum = UINT16_MAX;
  assert(koronos_elf64_validate(image,sizeof(image),KORONOS_EM_X86_64)==0);
  assert(chimera_process_admit_elf(image,sizeof(image),KORONOS_EM_X86_64,0x7fffffffe000ull,&q)<0);
  make_elf(image,false);
  h = reinterpret_cast<koronos_elf64_ehdr*>(image);
  h->e_phentsize = 1;
  assert(koronos_elf64_validate(image,sizeof(image),KORONOS_EM_X86_64)==0);
  assert(chimera_process_admit_elf(image,sizeof(image),KORONOS_EM_X86_64,0x7fffffffe000ull,&q)<0);
  make_elf(image,true);
  assert(chimera_process_admit_elf(image,sizeof(image),KORONOS_EM_X86_64,0x7fffffffe000ull,&q)<0);
  return 0;
}
