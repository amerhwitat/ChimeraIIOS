#include <cassert>
#include <cstdint>
#include <cstring>
#include "chimera/multiboot_modules.h"

namespace {
alignas(8) uint8_t info[512];
uint32_t align8(uint32_t n){return (n+7u)&~7u;}
uint32_t append_module(uint32_t off,uint32_t start,uint32_t end,const char*cmd){
 const uint32_t size=16u+static_cast<uint32_t>(std::strlen(cmd))+1u;
 const uint32_t type=3;
 std::memcpy(info+off,&type,4);
 std::memcpy(info+off+4,&size,4);
 std::memcpy(info+off+8,&start,4);std::memcpy(info+off+12,&end,4);
 std::memcpy(info+off+16,cmd,std::strlen(cmd)+1);
 return off+align8(size);
}
}
uint32_t append_framebuffer(uint32_t off) {
 const uint32_t type=8,size=38; const uint64_t addr=0xE0000000ull;
 const uint32_t pitch=4096,width=1024,height=768;
 const uint8_t bpp=32,format=1; const uint16_t reserved=0;
 std::memcpy(info+off,&type,4); std::memcpy(info+off+4,&size,4);
 std::memcpy(info+off+8,&addr,8); std::memcpy(info+off+16,&pitch,4);
 std::memcpy(info+off+20,&width,4); std::memcpy(info+off+24,&height,4);
 std::memcpy(info+off+28,&bpp,1); std::memcpy(info+off+29,&format,1);
 std::memcpy(info+off+30,&reserved,2);
 const uint8_t masks[6]={16,8,8,8,0,8}; std::memcpy(info+off+32,masks,6);
 return off+align8(size);
}
int main(){
 std::memset(info,0,sizeof(info));uint32_t total=0,reserved=0;
 std::memcpy(info,&total,4);std::memcpy(info+4,&reserved,4);
 uint32_t off=8;
 off=append_module(off,0x100000,0x101000,"chimera-recovery-initramfs");
 off=append_module(off,0x102000,0x102400,"chimera-recovery-manifest");
 off=append_module(off,0x103000,0x104000,"chimera-live-initramfs");
 off=append_framebuffer(off);
 const uint32_t end_type=0,end_size=8;
 std::memcpy(info+off,&end_type,4);std::memcpy(info+off+4,&end_size,4);off+=8;total=off;
 std::memcpy(info,&total,4);
 assert(chimera_multiboot_scan(reinterpret_cast<uint64_t>(info))==3);
 assert(chimera_multiboot_find(CHIMERA_MODULE_RECOVERY_INITRAMFS)!=nullptr);
 assert(chimera_multiboot_find(CHIMERA_MODULE_RECOVERY_MANIFEST)!=nullptr);
 assert(chimera_multiboot_find(CHIMERA_MODULE_LIVE_INITRAMFS)!=nullptr);
 assert(chimera_multiboot_find(CHIMERA_MODULE_INSTALL_IMAGE)==nullptr);
 const chimera_framebuffer_info *fb=chimera_multiboot_framebuffer();
 assert(fb!=nullptr && fb->valid==1);
 assert(fb->address==0xE0000000ull && fb->width==1024 && fb->height==768);
 assert(fb->pitch==4096 && fb->bpp==32 && fb->format==1);

 return 0;
}
