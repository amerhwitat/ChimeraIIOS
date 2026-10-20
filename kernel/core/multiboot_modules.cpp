#include "chimera/multiboot_modules.h"
namespace {
constexpr uint32_t MAX_MODULES=64;
chimera_boot_module modules[MAX_MODULES];
uint32_t module_count=0;
chimera_framebuffer_info framebuffer{};
static void copy_cmd(char* dst,const char* src){
 uint32_t i=0;
 if(!src){dst[0]=0;return;}
 for(;i<127&&src[i];++i) dst[i]=src[i];
 dst[i]=0;
}
static bool has(const char* s,const char* needle){
 if(!s||!needle)return false;
 for(uint32_t i=0;s[i];++i){
  uint32_t j=0;
  while(needle[j]&&s[i+j]==needle[j])++j;
  if(!needle[j])return true;
 }
 return false;
}
static uint32_t classify(const char* s){
 if(has(s,"chimera-user-init-elf")||has(s,"user-init.elf")||has(s,"chimera-init.elf"))return CHIMERA_MODULE_USER_INIT_ELF;
 if(has(s,"chimera-live-initramfs")||has(s,"live-initramfs")||has(s,"live-initramfs.img"))return CHIMERA_MODULE_LIVE_INITRAMFS;
 if(has(s,"chimera-live-manifest")||has(s,"live-manifest.json"))return CHIMERA_MODULE_LIVE_MANIFEST;
 if(has(s,"chimera-recovery-initramfs")||has(s,"recovery-initramfs.img"))return CHIMERA_MODULE_RECOVERY_INITRAMFS;
 if(has(s,"chimera-recovery-manifest")||has(s,"recovery-manifest.json"))return CHIMERA_MODULE_RECOVERY_MANIFEST;
 if(has(s,"chimera-installation-image")||has(s,"installation.img")||has(s,"install-image"))return CHIMERA_MODULE_INSTALL_IMAGE;
 if(has(s,"chimera-installation-manifest")||has(s,"installation-manifest.json")||has(s,"install-manifest"))return CHIMERA_MODULE_INSTALL_MANIFEST;
 if(has(s,"chimera-installer-contract")||has(s,"installer-contract.json")||has(s,"install-contract"))return CHIMERA_MODULE_INSTALL_CONTRACT;
 if(has(s,"chimera-install-phases")||has(s,"install-phases.json"))return CHIMERA_MODULE_INSTALL_PHASES;
 if(has(s,"chimera-installer-profiles")||has(s,"installer-profiles.json"))return CHIMERA_MODULE_INSTALL_PROFILES;
 return CHIMERA_MODULE_OTHER;
}
}
extern "C" __attribute__((used,noinline)) uint32_t chimera_multiboot_scan(uint64_t boot_info){
 module_count=0;
 framebuffer = {};
 if(!boot_info)return 0;
 const uint8_t* base=(const uint8_t*)(uintptr_t)boot_info;
 uint32_t total=*(const uint32_t*)base;
 if(total<16||total>16u*1024u*1024u)return 0;
 for(uint32_t off=8;off+8<=total;){
  const uint32_t type=*(const uint32_t*)(base+off);
  const uint32_t size=*(const uint32_t*)(base+off+4);
  if(size<8||off+size>total)break;
  if(type==8 && size>=32) {
   /* Multiboot2 framebuffer information tag. Never trust firmware-supplied
    * dimensions/pitch blindly: validate the complete scanline and byte span. */
   const uint64_t addr=*(const uint64_t*)(base+off+8);
   const uint32_t pitch=*(const uint32_t*)(base+off+16);
   const uint32_t width=*(const uint32_t*)(base+off+20);
   const uint32_t height=*(const uint32_t*)(base+off+24);
   const uint8_t bpp=*(const uint8_t*)(base+off+28);
   const uint8_t format=*(const uint8_t*)(base+off+29);
   uint64_t row_bytes=((uint64_t)width*(uint64_t)bpp+7u)/8u;
   uint64_t span=(uint64_t)pitch*(uint64_t)height;
   if(addr && width && height && width<=16384u && height<=16384u &&
      (bpp==8u || bpp==15u || bpp==16u || bpp==24u || bpp==32u) &&
      (format==0u || format==1u || format==2u) &&
      pitch>=row_bytes && span>=pitch && span<=0xFFFFFFFFFFFFFFFFull-addr) {
     framebuffer.address=addr; framebuffer.pitch=pitch; framebuffer.width=width;
     framebuffer.height=height; framebuffer.bpp=bpp; framebuffer.format=format;
     framebuffer.reserved=*(const uint16_t*)(base+off+30);
     if(format==1u && size>=38u) {
       framebuffer.red_pos=*(const uint8_t*)(base+off+32);
       framebuffer.red_mask_size=*(const uint8_t*)(base+off+33);
       framebuffer.green_pos=*(const uint8_t*)(base+off+34);
       framebuffer.green_mask_size=*(const uint8_t*)(base+off+35);
       framebuffer.blue_pos=*(const uint8_t*)(base+off+36);
       framebuffer.blue_mask_size=*(const uint8_t*)(base+off+37);
     }
     framebuffer.valid=1u;
   }
  }
  if(type==3&&size>=16&&module_count<MAX_MODULES){
   const uint32_t start=*(const uint32_t*)(base+off+8);
   const uint32_t end=*(const uint32_t*)(base+off+12);
   chimera_boot_module&m=modules[module_count++];
   m.base=start;
   m.size=end>=start?(uint64_t)end-start:0;
   m.cmdline[0]=0;
   if(size>16)copy_cmd(m.cmdline,(const char*)(base+off+16));
   m.kind=classify(m.cmdline);
  }
  if(type==0) break;
  off=(off+size+7u)&~7u;
 }
 return module_count;
}
extern "C" uint32_t chimera_multiboot_module_count(void){return module_count;}
extern "C" const chimera_boot_module* chimera_multiboot_module(uint32_t index){return index<module_count?&modules[index]:0;}
extern "C" const chimera_boot_module* chimera_multiboot_find(uint32_t kind){
 for(uint32_t i=0;i<module_count;i++)
  if(modules[i].kind==kind)return &modules[i];
 return 0;
}

extern "C" const chimera_framebuffer_info* chimera_multiboot_framebuffer(void){
 return framebuffer.valid ? &framebuffer : 0;
}
