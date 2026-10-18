#include <cassert>
#include <cstdint>
#include <cstring>
#include "chimera/multiboot_modules.h"

namespace {
alignas(8) uint8_t info[512];
uint32_t align8(uint32_t n){return (n+7u)&~7u;}
uint32_t append_module(uint32_t off,uint32_t start,uint32_t end,const char*cmd){
 const uint32_t size=16u+static_cast<uint32_t>(std::strlen(cmd))+1u;
 std::memcpy(info+off,&(const uint32_t&)(uint32_t{3}),4);
 std::memcpy(info+off+4,&size,4);
 std::memcpy(info+off+8,&start,4);std::memcpy(info+off+12,&end,4);
 std::memcpy(info+off+16,cmd,std::strlen(cmd)+1);
 return off+align8(size);
}
}
int main(){
 std::memset(info,0,sizeof(info));uint32_t total=0,reserved=0;
 std::memcpy(info,&total,4);std::memcpy(info+4,&reserved,4);
 uint32_t off=8;
 off=append_module(off,0x100000,0x101000,"chimera-recovery-initramfs");
 off=append_module(off,0x102000,0x102400,"chimera-recovery-manifest");
 off=append_module(off,0x103000,0x104000,"chimera-live-initramfs");
 const uint32_t end_type=0,end_size=8;
 std::memcpy(info+off,&end_type,4);std::memcpy(info+off+4,&end_size,4);off+=8;total=off;
 std::memcpy(info,&total,4);
 assert(chimera_multiboot_scan(reinterpret_cast<uint64_t>(info))==3);
 assert(chimera_multiboot_find(CHIMERA_MODULE_RECOVERY_INITRAMFS)!=nullptr);
 assert(chimera_multiboot_find(CHIMERA_MODULE_RECOVERY_MANIFEST)!=nullptr);
 assert(chimera_multiboot_find(CHIMERA_MODULE_LIVE_INITRAMFS)!=nullptr);
 assert(chimera_multiboot_find(CHIMERA_MODULE_INSTALL_IMAGE)==nullptr);
 return 0;
}
