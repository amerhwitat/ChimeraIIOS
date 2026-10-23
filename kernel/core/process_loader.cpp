#include "chimera/process_loader.h"
namespace {
constexpr uint32_t PT_LOAD=1u, PF_X=1u, PF_W=2u, PF_R=4u;
static bool add_ok(uint64_t a,uint64_t b,uint64_t*out){if(a>UINT64_MAX-b)return false;*out=a+b;return true;}
static bool align_up(uint64_t x,uint64_t*out){if(x>UINT64_MAX-(CHIMERA_ELF_PAGE_SIZE-1u))return false;*out=(x+CHIMERA_ELF_PAGE_SIZE-1u)&~(CHIMERA_ELF_PAGE_SIZE-1u);return true;}
static uint64_t align_down(uint64_t x){return x&~(CHIMERA_ELF_PAGE_SIZE-1u);}
static bool inside(uint64_t o,uint64_t n,uint64_t z){uint64_t e=0;return add_ok(o,n,&e)&&e<=z;}
static bool user_addr(uint64_t a){return a<CHIMERA_ELF_USER_LIMIT;}
struct Plan{koronos_elf64_phdr ph;uint64_t base,size,delta,end;};
}
extern "C" int chimera_elf_load_user_image(const void*image,uint64_t image_size,uint16_t machine,
 uint64_t stack_top,uint64_t stack_size,const chimera_elf_load_ops*ops,void*context,chimera_loaded_elf*out){
 if(!image||!out||!ops||!ops->create_address_space||!ops->map_pages||!ops->destroy_address_space)return -1;
 if(image_size<sizeof(koronos_elf64_ehdr))return -2;
 koronos_elf64_ehdr h{};__builtin_memcpy(&h,image,sizeof(h));
 if(!koronos_elf64_valid(&h)||h.e_version!=1u||h.e_ehsize!=sizeof(h)||h.e_machine!=machine||h.e_type!=KORONOS_ET_EXEC||
    h.e_phentsize!=sizeof(koronos_elf64_phdr)||h.e_phnum==0||h.e_phnum>CHIMERA_ELF_LOADER_MAX_SEGMENTS)return -3;
 const uint64_t phbytes=(uint64_t)h.e_phnum*h.e_phentsize;
 if(!inside(h.e_phoff,phbytes,image_size))return -4;
 if(stack_size<CHIMERA_ELF_PAGE_SIZE||stack_size>CHIMERA_ELF_MAX_STACK_SIZE||!user_addr(stack_top)||
    (stack_top&(CHIMERA_ELF_PAGE_SIZE-1u))||stack_top<stack_size)return -5;
 const uint64_t stack_base=stack_top-stack_size;
 if(!user_addr(stack_base)||stack_base>=stack_top)return -5;
 Plan plans[CHIMERA_ELF_LOADER_MAX_SEGMENTS]{};uint32_t count=0;
 uint64_t low=UINT64_MAX,high=0,file_bytes=0;bool entry_x=false;
 const auto*bytes=static_cast<const uint8_t*>(image);
 for(uint16_t i=0;i<h.e_phnum;i++){
  koronos_elf64_phdr ph{};__builtin_memcpy(&ph,bytes+h.e_phoff+(uint64_t)i*h.e_phentsize,sizeof(ph));
  if(ph.p_type!=PT_LOAD)continue;
  if(count>=CHIMERA_ELF_LOADER_MAX_SEGMENTS||ph.p_memsz<ph.p_filesz||!inside(ph.p_offset,ph.p_filesz,image_size)||
     ph.p_memsz==0||(ph.p_flags&~(PF_R|PF_W|PF_X))!=0||(ph.p_flags&(PF_W|PF_X))==(PF_W|PF_X))return -6;
  uint64_t end=0,map_end=0;
  if(!add_ok(ph.p_vaddr,ph.p_memsz,&end)||ph.p_vaddr<CHIMERA_ELF_PAGE_SIZE||!user_addr(ph.p_vaddr)||!user_addr(end-1u)||!align_up(end,&map_end)||!user_addr(map_end-1u))return -7;
  if(ph.p_align>1u&&((ph.p_align&(ph.p_align-1u))!=0||(ph.p_vaddr%ph.p_align)!=(ph.p_offset%ph.p_align)))return -8;
  Plan&p=plans[count++];p.ph=ph;p.base=align_down(ph.p_vaddr);p.size=map_end-p.base;p.delta=ph.p_vaddr-p.base;p.end=end;
  if(p.base<low) low=p.base;
  if(map_end>high) high=map_end;
  if((ph.p_flags&PF_X)&&h.e_entry>=ph.p_vaddr&&h.e_entry<end)entry_x=true;
  if(!add_ok(file_bytes,ph.p_filesz,&file_bytes))return -9;
 }
 if(!count||!entry_x)return -10;
 if(high>stack_base&&low<stack_top)return -11;
 // Refuse page-rounded overlap: permission merging must be an explicit mapper policy.
 for(uint32_t i=0;i<count;i++){
  uint64_t ae=plans[i].base+plans[i].size;
  for(uint32_t j=i+1;j<count;j++){uint64_t be=plans[j].base+plans[j].size;if(plans[i].base<be&&plans[j].base<ae)return -12;}
  if(plans[i].base<stack_top&&stack_base<ae)return -12;
 }
 void*as=ops->create_address_space(context);if(!as)return -13;
 for(uint32_t i=0;i<count;i++){
  const Plan&p=plans[i];void*alias=nullptr;
  if(ops->map_pages(context,as,p.base,p.size,p.ph.p_flags,&alias)!=0||!alias){ops->destroy_address_space(context,as);return -14;}
  if (ops->set_backing) {
   if (p.ph.p_offset < p.delta ||
       ops->set_backing(context,as,p.base,p.size,CHIMERA_ELF_BACKING_IMAGE,
                        reinterpret_cast<uintptr_t>(image),p.ph.p_offset-p.delta)!=0) {
    ops->destroy_address_space(context,as);return -16;
   }
  }
  auto*dst=static_cast<uint8_t*>(alias);__builtin_memset(dst,0,(size_t)p.size);
  if(p.ph.p_filesz)__builtin_memcpy(dst+p.delta,bytes+p.ph.p_offset,(size_t)p.ph.p_filesz);
 }
 void*stack_alias=nullptr;
 if(ops->map_pages(context,as,stack_base,stack_size,PF_R|PF_W,&stack_alias)!=0||!stack_alias){ops->destroy_address_space(context,as);return -15;}
 __builtin_memset(stack_alias,0,(size_t)stack_size);
 chimera_loaded_elf result{};result.abi=CHIMERA_ELF_LOADER_ABI;result.segment_count=count;result.address_space=as;
 result.entry=h.e_entry;result.user_stack_top=stack_top;result.image_low=low;result.image_high=high;result.loaded_file_bytes=file_bytes;
 *out=result;return 0;
}
