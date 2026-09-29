#include "chimera/multiboot_modules.h"
namespace { constexpr uint32_t MAX_MODULES=64; chimera_boot_module modules[MAX_MODULES]; uint32_t module_count=0;
static uint32_t strlen_bounded(const char* s,uint32_t cap){uint32_t n=0;while(n<cap&&s[n])++n;return n;}
static void copy_cmd(char* dst,const char* src){uint32_t i=0;if(!src){dst[0]=0;return;}for(;i<127&&src[i];++i)dst[i]=src[i];dst[i]=0;}
static bool has(const char* s,const char* needle){if(!s||!needle)return false;for(uint32_t i=0;s[i];++i){uint32_t j=0;while(needle[j]&&s[i+j]==needle[j])++j;if(!needle[j])return true;}return false;}
static uint32_t classify(const char* s){
 if(has(s,"chimera-live-initramfs"))return CHIMERA_MODULE_LIVE_INITRAMFS;
 if(has(s,"chimera-live-manifest"))return CHIMERA_MODULE_LIVE_MANIFEST;
 if(has(s,"chimera-installation-image"))return CHIMERA_MODULE_INSTALL_IMAGE;
 if(has(s,"chimera-installation-manifest"))return CHIMERA_MODULE_INSTALL_MANIFEST;
 if(has(s,"chimera-installer-contract"))return CHIMERA_MODULE_INSTALL_CONTRACT;
 if(has(s,"chimera-install-phases"))return CHIMERA_MODULE_INSTALL_PHASES;
 if(has(s,"chimera-installer-profiles"))return CHIMERA_MODULE_INSTALL_PROFILES;
 return CHIMERA_MODULE_OTHER;
}
}
extern "C" uint32_t chimera_multiboot_scan(uint64_t boot_info){
 module_count=0; if(!boot_info)return 0; const uint8_t* base=(const uint8_t*)(uintptr_t)boot_info;
 uint32_t total=*(const uint32_t*)base; if(total<16||total>16u*1024u*1024u)return 0;
 for(uint32_t off=8;off+8<=total;){const uint32_t type=*(const uint32_t*)(base+off);const uint32_t size=*(const uint32_t*)(base+off+4);if(size<8||off+size>total)break;
  if(type==3&&size>=16&&module_count<MAX_MODULES){const uint32_t start=*(const uint32_t*)(base+off+8);const uint32_t end=*(const uint32_t*)(base+off+12);chimera_boot_module&m=modules[module_count++];m.base=start;m.size=end>=start?(uint64_t)end-start:0;m.cmdline[0]=0;if(size>16)copy_cmd(m.cmdline,(const char*)(base+off+16));m.kind=classify(m.cmdline);}
  if(type==0)break;off=(off+size+7u)&~7u;
 }
 return module_count;
}
extern "C" uint32_t chimera_multiboot_module_count(void){return module_count;}
extern "C" const chimera_boot_module* chimera_multiboot_module(uint32_t index){return index<module_count?&modules[index]:0;}
extern "C" const chimera_boot_module* chimera_multiboot_find(uint32_t kind){for(uint32_t i=0;i<module_count;i++)if(modules[i].kind==kind)return &modules[i];return 0;}
