#include "chimera/gdt_tss.h"
namespace {
struct __attribute__((packed)) DescriptorPointer { uint16_t limit; uint64_t base; };
uint64_t gdt[7];chimera_x86_tss64 tss{};DescriptorPointer gdtr{};bool prepared=false,installed=false;
static bool valid_stack(uint64_t p){return p!=0&&(p&0xFul)==0;}
static uint64_t segment(uint8_t access,uint8_t flags){return 0xFFFFull|((uint64_t)access<<40)|((uint64_t)(flags&0xF)<<52);}
static void set_tss_descriptor(uint64_t base,uint32_t limit){gdt[5]=(limit&0xFFFFu)|((base&0xFFFFFFull)<<16)|(0x89ull<<40)|(((uint64_t)limit&0xF0000ull)<<32)|(((base>>24)&0xFFull)<<56);gdt[6]=base>>32;}
}
extern "C" int chimera_x86_gdt_tss_prepare(uint64_t stack){if(!valid_stack(stack))return -1;for(uint32_t i=0;i<7;++i)gdt[i]=0;gdt[1]=segment(0x9A,0xA);gdt[2]=segment(0x92,0xC);gdt[3]=segment(0xF2,0xC);gdt[4]=segment(0xFA,0xA);tss={};tss.rsp0=stack;tss.iopb_offset=sizeof(tss);set_tss_descriptor(reinterpret_cast<uint64_t>(&tss),sizeof(tss)-1u);gdtr.limit=sizeof(gdt)-1u;gdtr.base=reinterpret_cast<uint64_t>(gdt);prepared=true;installed=false;return 0;}
extern "C" int chimera_x86_gdt_tss_install(uint64_t stack){int rc=chimera_x86_gdt_tss_prepare(stack);if(rc)return rc;
#if defined(CHIMERA_GDT_TSS_HOST_TEST)
 return -2;
#else
 extern void koronos_x86_load_gdt_tss(const void*,uint16_t);
 koronos_x86_load_gdt_tss(&gdtr,CHIMERA_X86_TSS_SELECTOR);installed=true;return 0;
#endif
}
extern "C" int chimera_x86_tss_set_kernel_stack(uint64_t stack){if(!prepared||!valid_stack(stack))return -1;tss.rsp0=stack;return 0;}
extern "C" const chimera_x86_tss64*chimera_x86_tss_snapshot(void){return prepared?&tss:nullptr;}
extern "C" int chimera_x86_user_entry_available(void){return prepared&&installed?1:0;}
